#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
![Pyccoon](pyccoon.svg)

"**Pyccoon**" is a side-to-side documentation generator.
"""


import optparse
import os
import shutil
import pystache
import re
import sys
import json
from io import open
from datetime import datetime
from collections import defaultdict

# This module contains all of our static resources.
from . import resources, __version__, __author__
from .languages import get_language, Language

from .utils import shift, ensure_directory, SourceFile


# ## Main documentation generation class

class Pyccoon(object):

    add_lineno = True

    # The start of each Pygments highlight block.
    highlight_start = "<div class=\"highlight\"><pre>"

    # The end of each Pygments highlight block.
    highlight_end = "</pre></div>"

    config = defaultdict(lambda: [], {
        "skip_files": [".+\\.pyc", "__pycache__", "\\.travis.yml", "\\.git", "\\.DS_Store"]
    })

    config_file = '.pyccoon'
    watch = False
    verbosity = -1

    outdir = sourcedir = None

    def __init__(self, opts, process=True):
        """
        ## Pyccoon initialization
        :param opts: `dict` of parameters.
        :param process: Whether to generate documentation immediately

        Available parameters:

          * `sourcedir` - project source directory
          * `outdir` - output directory
          * `config_file` - pyccoon project settings
          * `watch` - whether to regenerate the docs automatically
        """

        for key, value in opts.items():
            setattr(self, key, value)

        self.log("Pyccoon {0}".format(__version__))
        self.log("-------------")

        self.init_config()

        self.verbosity = self.config['verbosity'] or 1 if self.verbosity == -1 else self.verbosity

        if not self.outdir:
            raise TypeError("Missing the required 'outdir' argument.")
        if not self.sourcedir:
            raise TypeError("Missing the required 'sourcedir' argument.")

        self.sourcedir = os.path.abspath(self.sourcedir)
        self.log("Source folder: " + self.sourcedir)
        self.outdir = os.path.abspath(self.outdir)
        self.log("Output folder: " + self.outdir)

        # Create the template that we will use to generate the Pyccoon HTML page.
        # If the user has supplied a path, we read it from there.
        if self.custom_html_template_path:
            with open(self.custom_html_template_path) as f:
                html_template = f.read()
            self.page_template = self.template(html_template)
        # If not, we use the default.
        else:
            self.page_template = self.template(resources.html)

        self.collect_sources()

        if process:
            self.process()

        # If the -w / --watch option was present, monitor the source directories
        # for changes and re-generate documentation for source files whenever they
        # are modified.
        if self.watch:
            try:
                import watchdog.events
                import watchdog.observers
            except ImportError:
                sys.exit('The `watch` option requires the watchdog package.')

            from .utils import monitor
            monitor(path=self.sourcedir,
                    file_modified=self.process,
                    file_changed=self.collect_n_process)

    def log(self, message):
        if self.verbosity:
            print(message)

    def init_config(self):
        """ Try to get `.pyccoon` config file or use the default values """
        config_file = os.path.abspath(self.config_file)
        if os.path.exists(config_file):
            self.log('Using config {0:s}'.format(config_file))
            with open(config_file, 'rb') as f:
                self.config.update(json.loads(f.read().decode('utf8')))

        self.config['skip_files'] = [re.compile(p) for p in self.config['skip_files']]
        self.config['copy_files'] = [re.compile(p) for p in self.config['copy_files']]

        self.project_name = self.config['project_name'] \
            or (os.path.split(self.sourcedir)[1] + " documentation")

        # If a line breaking behavior is not supplied, assume it is `'pre-wrap'`
        # for backward compatibility.
        # The user might want to supply a different value, such as `'normal'`.
        self.linebreaking_behavior = self.config['linebreaking-behavior'] \
            or 'pre-wrap'

        # `self.custom_css_path` is either `None` or a path relative to the
        # path of the config file.
        custom_css_path = self.config['css-path'] or None
        if custom_css_path:
            self.custom_css_path = os.path.join(os.path.dirname(self.config_file),
                                                custom_css_path)
        else:
            self.custom_css_path = None

        # `self.custom_html_template_path` is either `None` or a path relative to the
        # path of the config file.
        custom_html_template_path = self.config['custom-html-template'] or None
        if custom_html_template_path:
            self.custom_html_template_path = os.path.join(os.path.dirname(self.config_file),
                                                          custom_html_template_path)
        else:
            self.custom_html_template_path = None

    _textchars = bytearray([7, 8, 9, 10, 12, 13, 27]) + bytearray(range(0x20, 0x100))

    @classmethod
    def is_binary_string(cls, bytes):
        return bool(bytes.translate(None, cls._textchars))

    def collect_sources(self):
        """ Collect names of all files to be copied or processed """
        self.sources = {}
        for dirpath, dirnames, files in os.walk(self.sourcedir):
            if any([reg.search(dirpath) for reg in self.config['skip_files']]):
                continue
            for name in files:
                if name in dirnames or any([reg.search(name) for reg in self.config['skip_files']]):
                    continue

                # Don't copy the custom CSS file, if there is one.
                # That file will be copied with the name specified by `resources.css_filename`.
                if self.custom_css_path and \
                   os.path.join(dirpath, name) == os.path.abspath(self.custom_css_path):
                    continue

                fullpath = os.path.join(dirpath, name)
                source = os.path.relpath(fullpath, self.sourcedir)
                process = True
                if any([regex.search(name) for regex in self.config['copy_files']]):
                    process = False

                prefix = None
                if process:
                    with open(fullpath, 'rb') as f:
                        prefix = f.read(1024)
                        if self.is_binary_string(prefix):
                            process = False

                self.sources[source] = SourceFile(
                    source=source,
                    destination=self.destination(source, process=process),
                    process=process,
                    prefix=prefix
                )

    def collect_n_process(self):
        self.collect_sources()
        self.process()

    def process(self, sources=None, language=None):
        """
        ## Source files processing

        :param sources: `list` of source files to process
        :param language: Force programming language
        """

        self.log('\n' + '-'*80)
        self.log("[{0}] Generating documentation for {1}".format(datetime.now(), self.project_name))
        self.log('-'*80 + '\n')

        if sources:
            sources = dict([(k, v) for (k, v) in self.sources.items() if k in sources])
        else:
            sources = self.sources

        ensure_directory(self.outdir)

        # Handle CSS file which is either:
        #
        # - built from a default template
        # - user specified (in which case it is not a template, but a normal file
        #     to be used verbatim.

        # If the user has supplied a path, we use that file.
        if self.custom_css_path:
            with open(self.custom_css_path) as f:
                css_contents = f.read()
        # Else, we use the default template.
        else:
            # Currently, the only configurable item in the template is the linebreaking behavior
            # of the text in documentation sections.
            css_contents = pystache.render(resources.css,
                                           {'linebreaking-behavior':
                                            self.linebreaking_behavior})

        # Now that we have specified the *contents* of the file, the code is equal in both
        # situations (*template* or *custom file*).
        filepath = os.path.join(os.path.split(resources.__file__)[0], resources.css_filename)
        destpath = os.path.join(self.outdir, resources.css_filename)

        with open(destpath, 'w') as f:
            f.write(css_contents)

        # Handle static files
        for filename, dest in resources.static_files:
            filepath = os.path.join(os.path.split(resources.__file__)[0], filename)
            destpath = os.path.join(self.outdir, dest)
            self.sources[filepath] = SourceFile(source=filepath,
                                                destination=destpath,
                                                process=False,
                                                prefix=None)

            shutil.copyfile(
                filepath,
                destpath
            )

        # Proceed to generating the documentation.
        for sf in sorted(sources.values(), key=lambda x: x.destination):

            filepath = os.path.join(self.sourcedir, sf.source)
            try:
                if sf.process:
                    with open(filepath, "rb") as f:
                        code = f.read().decode('utf8')

                    self.language = get_language(sf.source, code, language=language)
                    if not self.language:
                        self.sources[sf.source] = sf._replace(process=False)
                        sf = self.sources[sf.source]

                    try:
                        ensure_directory(os.path.split(sf.destination)[0])
                    except OSError:
                        pass

                if sf.process:
                    if os.path.exists(os.path.join(self.sourcedir, sf.source)):
                        with open(sf.destination, "wb") as f:
                            f.write(self.generate_documentation(sf.source, code,
                                                                language=self.language)
                                    .encode('utf8'))

                        self.log("\tProcessed:\t{0:s} -> {1:s}"
                                 .format(sf.source, os.path.relpath(sf.destination, self.outdir)))
                    else:
                        self.log("File does not exist: {0:s}".format(sf.source))

                else:
                    ensure_directory(os.path.split(sf.destination)[0])
                    shutil.copyfile(os.path.join(self.sourcedir, sf.source), sf.destination)
                    self.log("\tCopied:   \t{0:s}".format(sf.source))
            except Exception as e:
                self.log("Error while processing file {0:s}: {1}".format(sf.source, e))

        # Ensure there is always an index file in the output folder
        to_append = []
        for sf in self.sources.values():
            folder = os.path.relpath(os.path.split(sf.destination)[0], self.outdir).lstrip('./')
            index = os.path.join(folder, "index.html")

            if not any([os.path.join(self.outdir, index) == sf.destination
                        for sf in self.sources.values()]):
                source = os.path.join(folder, 'index.html')
                to_append.append((
                    source,
                    SourceFile(source=source,
                               destination=os.path.join(self.outdir, index),
                               process=False,
                               prefix=None)
                ))

                with open(os.path.join(self.outdir, index), 'w', encoding='utf8') as f:
                    self.language = Language()
                    f.write(self.generate_html(source, []))
                    self.log("\tGenerated:\t{0:s}".format(source))

        for source, sf in to_append:
            self.sources[source] = sf

        self.log("...Done.")

    def template(self, source):
        return lambda context: pystache.render(source, context)

    def generate_documentation(self, source, code, language=None):
        """
        ## Generating documentation
        Generate the documentation for a source file by reading it in, splitting it
        up into comment/code sections, highlighting them for the appropriate
        language, and merging them into an HTML template.
        """

        self.sections = language.parse(code, add_lineno=self.add_lineno)
        self.highlight(source, self.sections, language)
        return self.generate_html(source, self.sections)

    def highlight(self, source, sections, language):
        """
        ### Highlighting the source code

        Highlights a single chunk of code using the **Pygments** module, and runs
        the text of its corresponding comment through **Markdown**.

        We process the entire file in a single call to Pygments by inserting little
        marker comments between each section and then splitting the result string
        wherever our markers occur.
        """
        output = language.highlight(
            language.divider_text.join(section["code_text"].rstrip() for section in sections)
        )

        output = output.replace(self.highlight_start, "").replace(self.highlight_end, "")
        fragments = re.split(language.divider_html, output)
        for i, section in enumerate(sections):
            section["code_html"] = shift(fragments, "")
            if section["code_html"]:
                section["code_html"] = \
                    self.highlight_start + section["code_html"] + self.highlight_end
            docs_text = section["docs_text"]
            section["docs_html"] = language.markdown(
                self.preprocess(docs_text, source=os.path.join(self.sourcedir, source))
            )
            section["num"] = i

    def preprocess(self, comment, source):
        """
        ### Preprocessing the comments

        Add cross-references before having the text processed by markdown.  It's
        possible to reference another file, like this : `[[utils.py]]` which renders
        [[utils.py]]. You can also reference a specific section of another file, like
        this: `[[utils.py#ensure-directory]]` which renders as
        [[utils.py#ensure-directory]]. Sections have to be manually
        declared; they are written on a single line, prefixed by `#`s:
        `### like this`
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
            anchor = None
            if '#' in path:
                path, anchor = path.split('#')

            if not name:
                name = os.path.basename(path)
                if anchor:
                    name = name + '#' + anchor

            anchor = '#' + anchor if anchor else ''

            if not path.startswith('.'):
                # Absolute reference
                path = os.path.relpath(
                    self.destination(path),
                    os.path.split(self.sources[os.path.relpath(source,
                                                               self.sourcedir)].destination)[0]
                )
            else:
                # Relative reference
                path = os.path.relpath(
                    self.destination(os.path.join(
                        os.path.split(os.path.relpath(source, self.sourcedir))[0], path)
                    ),
                    os.path.split(self.sources[os.path.relpath(source,
                                                               self.sourcedir)].destination)[0]
                )

            return "[{0:s}]({1:s}{2:s})".format(name, path, anchor)

        def replace_section_name(match):
            return (
                    '\n{lvl} <a id="{id}" class="header-anchor" href="#{id}">{name}</a>'
            ).format(**{
                "lvl":  match.group(2),
                "id":   slugify(match.group(3)),
                "name": match.group(3)
            })

        # def replace_texblocks(match):
        #     print match.groups()
        #     return (
        #         '```\n{begin}\n{code}\n{end}\n```'
        #     ).format(**{
        #         "begin": r"\begin{{{}}}".format(match.group(2)),
        #         "end": r"\end{{{}}}".format(match.group(2)),
        #         "code": match.group(3)
        #     })

        comment = re.compile(r'^\s*(#\s)?\s*(#+)([^#\n]+)\s*$', re.M)\
            .sub(replace_section_name, comment)
        comment = re.sub(r'\[\[([^\|\n]+\|)?(.+?)\]\]', replace_crossref, comment)
        # comment = re.compile(r'\s*```tex(`([\w]+))?([\s\S]+)```\s*$', re.M)\
        #     .sub(replace_texblocks, comment)

        return comment

    # ## HTML Code generation

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
        title = os.path.relpath(source, self.sourcedir)
        page_title = self.project_name + ": " + os.path.relpath(source, self.sourcedir).lstrip('./')
        csspath = os.path.relpath(os.path.join(self.outdir, resources.css_filename),
                                  os.path.split(dest)[0])

        breadcrumbs, filename = self.generate_breadcrumbs(dest, title)
        children = self.generate_navigation(source)
        contents = self.generate_contents(sections)

        for section in sections:
            section['line_count'] = (section['code_text'].rstrip('\n') + '\n').count('\n')
            section['linenos'] = '\n'.join(str(section['line'] + i)
                                           for i in range(section['line_count']))

        rendered = self.page_template({
            "title":            page_title,
            "breadcrumbs":      breadcrumbs,
            "filename":         filename,
            "children":         children,
            "stylesheet":       csspath,
            "sections":         sections,
            "source":           source,
            "contents":         contents,
            "contents?":        bool(contents),
            "destination":      dest,
            "generation_time":  datetime.now().strftime('%Y-%m-%d %H:%M'),
            "root_path":        os.path.relpath(".", os.path.split(source)[0]),
            "project_name":     self.project_name,
            "mathjax?":          self.config['mathjax'],
            "docs_only?": not any(section['code_text'] for section in sections)
        })

        return rendered.replace("__DOUBLE_OPEN_STACHE__", "{{")

    def generate_breadcrumbs(self, dest, title):
        """
        ### Generating breadcrumbs
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

        return breadcrumbs[:-1], source_chunks[0]

    def generate_navigation(self, source):
        """
        ### Generating navigation
        For `index.html` files, generate a menu of folder contents.

        TODO: remove language dependency
        """
        index_names = [r'__init__\..+', r'index\..+']
        basename = os.path.basename(source)
        if not any([re.match(regex, basename) for regex in index_names]):
            return []

        children = []
        folder = os.path.split(os.path.join(self.sourcedir, source))[0]
        relfolder = os.path.relpath(folder, self.sourcedir)
        outfolder = os.path.join(self.outdir, relfolder) if relfolder != "." else self.outdir
        for filename in os.listdir(folder):
            if not any([regex.search(filename) for regex in self.config['skip_files']]):
                isdir = False
                filepath = None

                if os.path.isdir(os.path.join(folder, filename)):
                    isdir = True
                    filepath = os.path.join(filename, "index.html")
                else:

                    if filename in index_names:
                        filepath = "index.html"
                    else:
                        in_sources = self.sources.get(
                            os.path.join(relfolder, filename)
                            if relfolder != "." else filename
                        )

                        if in_sources:
                            filepath = in_sources.destination[len(outfolder)+1:]

                if filepath:
                    children.append({
                        "title": filename,
                        "path": filepath,
                        "isdir": isdir
                    })

        return sorted(children, key=lambda x: not x['isdir'])

    def generate_contents(self, sections):
        """
        ### Generating page contents
        Gather the names of the documentation sections for "jump-to"-like navigation on the page.
        """
        contents = []

        for section in sections:
            section["code_html"] = section["code_html"].replace("{{", "__DOUBLE_OPEN_STACHE__")

            for match in re.finditer(r'<h(\d)>(.+href=\"#(.+)\".+)</h(\d)>',
                                     section["docs_html"], re.M):

                contents.append({
                    "url": "#{0}".format(match.group(3)),
                    "basename": re.sub(r'<[^<]+?>', '', match.group(2)),
                    "level": match.group(1)
                })
        return contents

    # ## Utilities

    def destination(self, source, language=None, process=True):
        """
        Compute the destination HTML path for an input source file path. If the
        source is `lib/example.py`, the HTML will be at `docs/lib/example.html`
        """

        dirname, filename = os.path.split(source)
        if process:
            language = language or self.get_language(source)

        name = language.transform_filename(filename) if language else filename
        return os.path.normpath(os.path.join(self.outdir, os.path.join(dirname, name)))

    def get_language(self, source):
        """ Determine language of the file """
        language = None

        try:
            with open(os.path.join(self.sourcedir, source), "rb") as sourcefile:
                code = sourcefile.read().decode('utf8')

            language = get_language(source, code)
        except Exception:
            pass

        return language


def main():
    """Hook spot for the console script."""

    parser = optparse.OptionParser(version='Pyccoon {0}'.format(__version__))
    parser.add_option('-s', '--source', action='store', type='string',
                      dest='sourcedir', default='.',
                      help='Source files directory (default: `%default`)')

    parser.add_option('-d', '--destination', action='store', type='string',
                      dest='outdir', default='docs',
                      help='Output directory (default: `%default`)')

    parser.add_option('-w', '--watch', action='store_true',
                      help='Watch original files and regenerate documentation on changes')

    parser.add_option('-c', '--config', action='store', dest='config_file',
                      default=os.path.join(os.getcwd(), '.pyccoon'), type='string',
                      help='Config file to use (default: `%default`)')

    parser.add_option('-v', '--verbosity', action='store', dest='verbosity',
                      default=-1, type='int',
                      help='Terminal output verbosity (0 to 1; default: %default)')

    opts, _ = parser.parse_args()
    opts = defaultdict(lambda: None, vars(opts))

    Pyccoon(opts)

# Run the script.
if __name__ == "__main__":
    main()
