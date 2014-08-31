#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
"**Pyccoon**" is a Python port of [Docco](http://jashkenas.github.com/docco/):\
the original quick-and-dirty, hundred-line-long, literate-programming-style\
documentation generator. It produces HTML that displays your comments\
alongside your code. Comments are passed through \
[Markdown](http://daringfireball.net/projects/markdown/syntax) and\
[SmartyPants](http://daringfireball.net/projects/smartypants), while code is\
passed through [Pygments](http://pygments.org/) for syntax highlighting.
This page is the result of running Pyccoon against its own source file.

Pyccoon generates the documentation folder structured correspondingly to the code. To create \
documentation `docs` for the project in `src` folder, run the following:

    $ python src/utils/pyccoon.py -s src -d docs

The [original source for Pyccoon](https://github.com/fitzgen/pyccoon) is available on GitHub,\
and released under the MIT license.
"""

import optparse
import os
import pystache
import re
import sys
from collections import defaultdict

# This module contains all of our static resources.
from . import resources
from .languages import get_language

from .utils import shift, ensure_directory


# === Main Documentation Generation Functions ===

class Pyccoon:

    add_lineno = True

    # The CSS styles we'd like to apply to the documentation.
    css = resources.css

    # The start of each Pygments highlight block.
    highlight_start = "<div class=\"highlight\"><pre>"

    # The end of each Pygments highlight block.
    highlight_end = "</pre></div>"

    def __init__(self, opts):
        for key, value in opts.items():
            setattr(self, key, value)

        if not self.outdir:
            raise TypeError("Missing the required 'outdir' keyword argument.")

        if not self.sourcedir:
            raise TypeError("Missing the required 'sourcedir' keyword argument.")

        self.outdir = os.path.abspath(self.outdir)
        self.sourcedir = os.path.abspath(self.sourcedir)

        self.sources = []
        for dirpath, dirnames, files in os.walk(self.sourcedir):
            for name in files:
                if name not in dirnames:
                    self.sources.append(os.path.relpath(os.path.join(dirpath, name),
                                                        self.sourcedir))

        # Create the template that we will use to generate the Pyccoon HTML page.
        self.page_template = self.template(resources.html)

    def process(self, sources=None, language=None):
        """For each source file passed as argument, generate the documentation."""

        if not sources:
            sources = sorted(self.sources)

        if not sources:
            return

        ensure_directory(self.outdir)
        with open(os.path.join(self.outdir, "pyccoon.css"), 'w') as css_file:
            css_file.write(resources.css)

        # Proceed to generating the documentation.
        while sources:
            source = sources.pop(0)

            with open(os.path.join(self.sourcedir, source), "r") as sourcefile:
                code = sourcefile.read()

            self.language = get_language(source, code, language=language)
            if not self.language:
                print("{:s} -> Skipped".format(source))
                continue

            dest = self.destination(source)

            try:
                os.makedirs(os.path.split(dest)[0])
            except OSError:
                pass

            if os.path.exists(os.path.join(self.sourcedir, source)):
                with open(dest, "w") as f:
                    f.write(self.generate_documentation(source, code, language=self.language))

                print("{:s} -> {:s}".format(source, os.path.relpath(dest, self.outdir)))
            else:
                print("File does not exist: {:s}".format(source))

    def template(self, source):
        return lambda context: pystache.render(source, context)

    def generate_documentation(self, source, code, language=None):
        """
        Generate the documentation for a source file by reading it in, splitting it\
        up into comment/code sections, highlighting them for the appropriate\
        language, and merging them into an HTML template.
        """

        sections = language.parse(code, add_lineno=self.add_lineno)
        self.highlight(source, sections, language)
        return self.generate_html(source, sections)

    # === Preprocessing the comments ===

    def preprocess(self, comment, section_nr, source):
        """
        Add cross-references before having the text processed by markdown.  It's\
        possible to reference another file, like this : `[[main.py]]` which renders\
        [[main.py]]. You can also reference a specific section of another file, like\
        this: `[[main.py#highlighting-the-source-code]]` which renders as\
        [[main.py#highlighting-the-source-code]]. Sections have to be manually\
        declared; they are written on a single line, and surrounded by equals signs:\
        `=== like this ===`

        TODO: currently broken
        """

        def slugify(name):
            """ Return URL-friendly section name representation """
            return "-".join(name.lower().strip().split(" "))

        def replace_crossref(match):
            name = match.group(1)
            if name:
                name = name.rstrip("|")
            path = match.group(2)

            if not name and not path:
                return

            # Check if the match contains an anchor
            if '#' in path:
                link, anchor = path.split('#')
                if not name:
                    name = link
                    if anchor:
                        name = name + '#' + anchor
                return "[{:s}]({:s}#{:s})"\
                    .format(name,
                            os.path.relpath(self.destination(link),
                                            self.destination(source)),
                            anchor)

            else:
                if not name:
                    name = os.path.basename(path)

                dest = self.destination(path)
                if not dest:
                    return
                return "[{:s}]({:s})"\
                    .format(name, os.path.relpath(dest, os.path.dirname(source)))

        def replace_section_name(match):
            return '\n{lvl} <span id="{id}" href="{id}">{name}</span>'.format(**{
                "lvl":  re.sub('=', '#', match.group(1)),
                "id":   slugify(match.group(2)),
                "name": match.group(2)
            })

        comment = comment.replace('<', '&lt;')
        comment = comment.replace('>', '&gt;')

        comment = re.sub('^\s*#?\s*([=]+)([^=\n]+)([=]+)', replace_section_name, comment,
                         flags=re.M)
        comment = re.sub('\[\[([^\|]+\|)?(.+?)\]\]', replace_crossref, comment)

        return comment

    # === Highlighting the source code ===

    def highlight(self, source, sections, language):
        """
        Highlights a single chunk of code using the **Pygments** module, and runs\
        the text of its corresponding comment through **Markdown**.

        We process the entire file in a single call to Pygments by inserting little\
        marker comments between each section and then splitting the result string\
        wherever our markers occur.
        """
        output = language.highlight(
            language.divider_text.join(section["code_text"].rstrip() for section in sections)
        )

        output = output.replace(self.highlight_start, "").replace(self.highlight_end, "")
        fragments = re.split(language.divider_html, output)
        for i, section in enumerate(sections):
            section["code_html"] = self.highlight_start + shift(fragments, "") + self.highlight_end
            docs_text = section["docs_text"]
            section["docs_html"] = language.markdown(
                self.preprocess(docs_text, i, source=os.path.join(self.sourcedir, source))
            )
            section["num"] = i

    # === HTML Code generation ===

    def generate_breadcrumbs(self, dest, title):
        """
        Based on the source file path, generate linked breadcrumbs of the documentation.
        """
        breadcrumbs = []
        crumbpath = None

        dest_chunks = os.path.relpath(dest, self.outdir).split("/")
        source_chunks = title.split("/")
        dest_chunks.reverse()
        source_chunks.reverse()

        for i, crumb in enumerate(dest_chunks):

            crumbpath = os.path.join(crumbpath, "..") if crumbpath else crumb

            breadcrumbs.insert(0, {
                "title": source_chunks[i],
                "path": crumbpath if crumbpath.endswith('.html')
                else os.path.join(crumbpath, 'index.html')
            })
        breadcrumbs.insert(0, {
            "title": ".",
            "path": os.path.join(crumbpath, "../index.html")
        })

        return breadcrumbs

    def generate_navigation(self, source):
        """
        For `index.html` files, generate a menu of folder contents.

        TODO: remove language dependency
        """
        if os.path.basename(source) != '__init__.py':
            return []

        children = []
        folder = os.path.split(os.path.join(self.sourcedir, source))[0]
        for filename in os.listdir(folder):
            isdir = False
            filepath = None

            if os.path.isdir(os.path.join(folder, filename)):
                isdir = True
                filepath = os.path.join(filename, "index.html")
            elif filename.endswith(".py"):
                if filename == '__init__.py':
                    filepath = "index.html"
                else:
                    filepath = filename[:-3] + ".html"

            if filepath:
                children.append({
                    "title": filename,
                    "path": filepath,
                    "isdir": isdir
                })

        return sorted(children, key=lambda x: not x['isdir'])

    def generate_contents(self, sections):
        """
        Gather the names of the documentation sections for "jump-to"-like navigation on the page.
        """
        contents = []

        for section in sections:
            section["code_html"] = re.sub(r"\{\{", r"__DOUBLE_OPEN_STACHE__", section["code_html"])

            match = re.search(r'<h(\d)>(.+)</h(\d)>', section["docs_html"], flags=re.M)

            if match:
                contents.append({
                    "url": "#section-{}".format(section["num"]),
                    "basename": re.sub('<[^<]+?>', '', match.group(2)),
                    "level": match.group(1)
                })
        return contents

    def generate_html(self, source, sections):
        """
        Once all of the code is finished highlighting, we can generate the HTML file\
        and write out the documentation. Pass the completed sections into the\
        template found in `resources/pyccoon.html`.

        Pystache will attempt to recursively render context variables, so we must\
        replace any occurences of `{{`, which is valid in some languages, with a\
        "unique enough" identifier before rendering, and then post-process the\
        rendered template and change the identifier back to `{{`.
        """

        dest = self.destination(source)
        title = os.path.relpath(os.path.abspath(source), self.sourcedir)
        csspath = os.path.relpath(os.path.join(self.outdir, "pyccoon.css"), os.path.split(dest)[0])

        breadcrumbs = self.generate_breadcrumbs(dest, title)
        children = self.generate_navigation(source)
        contents = self.generate_contents(sections)

        rendered = self.page_template({
            "title":        title,
            "breadcrumbs":  breadcrumbs,
            "children":     children,
            "stylesheet":   csspath,
            "sections":     sections,
            "source":       source,
            "contents":     contents,
            "contents?":    bool(contents),
            "destination":  dest
        })

        return re.sub(r"__DOUBLE_OPEN_STACHE__", "{{", rendered)

    def destination(self, filepath):
        """
        Compute the destination HTML path for an input source file path. If the \
        source is `lib/example.py`, the HTML will be at `docs/lib/example.html`
        """

        dirname, filename = os.path.split(filepath)
        name = self.language.transform_filename(filename)
        return os.path.normpath(os.path.join(self.outdir, os.path.join(dirname, name)))


def main():
    """Hook spot for the console script."""

    parser = optparse.OptionParser()
    parser.add_option('-s', '--source', action='store', type='string',
                      dest='sourcedir', default='.',
                      help='The source files directory.')

    parser.add_option('-d', '--directory', action='store', type='string',
                      dest='outdir', default='docs',
                      help='The output directory that the rendered files should go to.')

    parser.add_option('-w', '--watch', action='store_true',
                      help='Watch original files and re-generate documentation on changes')

    opts, _ = parser.parse_args()
    opts = defaultdict(lambda: None, vars(opts))

    pyccoon = Pyccoon(opts)
    pyccoon.process()

    # If the -w / --watch option was present, monitor the source directories \
    # for changes and re-generate documentation for source files whenever they \
    # are modified.
    if pyccoon.watch:
        try:
            import watchdog.events
            import watchdog.observers
        except ImportError:
            sys.exit('The -w/--watch option requires the watchdog package.')

        from .utils import monitor
        monitor(pyccoon)

# Run the script.
if __name__ == "__main__":
    main()
