import re
import os

from markdown.util import etree, AtomicString
from markdown.inlinepatterns import Pattern
from markdown.preprocessors import Preprocessor
from markdown.extensions import Extension


class Todo(Extension):

    """ ## TODO, FIXME, WARNING, CAUTION marks """

    class Prep(Preprocessor):

        """
        Markdown preprocessor that matches all TODO and FIXME strings occurring at the beginning\
        of the line or after the inline comment delimiter and highlights them in the documentation.
        """

        matched_strings = ["TODO", "FIXME", "WARNING", "CAUTION"]
        regex = re.compile("^\s*(" + "|".join(matched_strings) + ":?)(.*)", flags=re.I)

        def template(self, match):
            """ Intended markup for TODO strings. The type of the string is used as a class. """
            return "<span class={0:s}><strong>{1:s}</strong>{2:s}</span>"\
                .format(match.group(1).lower(), match.group(1), match.group(2))

        def run(self, lines):
            """ String matching is case insensitive """
            return [self.regex.sub(self.template, line) for line in lines]

    def extendMarkdown(self, md, md_globals):
        md.preprocessors.add('todo', Todo.Prep(md), '_end')


class LinesConnector(Extension):

    """ ## Lines connector extension """

    def __init__(self, regex=r"(\S)\s*\\\s*\n\s*(\S)", sub=r"\1 \2", *args, **kwargs):

        regex = re.compile(regex, flags=re.M)

        class Prep(Preprocessor):

            def run(self, lines):
                """ Method ensures that there is exactly one space between 2 joined strings. """
                return regex.sub(sub, "\n".join(lines)).split("\n")

        self.Prep = Prep()

        super(LinesConnector, self).__init__(*args, **kwargs)

    def extendMarkdown(self, md, md_globals):
        md.preprocessors.add('lines-connector', self.Prep, '_end')


class SaneDefList(Extension):

    """ ## Better definition lists """

    class Prep(Preprocessor):

        """
        Markdown preprocessor that prepares natural-style definition lists for native Markdown \
        extension `def_list`. It allows to write more compact and readable class field definitions.
        """

        def run(self, lines):
            """
            Searches for a line starting with a literal followed by a colon and multiple spaces:

                some arbitrary parameter name:  and its definition separated by `:\s\s+`
                `parameter name` might contain\
                everything except a \
                [colon](//en.wikipedia.org/wiki/Colon_(punctuation))\
                and be multiline:               it still works

            And turns it into:

            some arbitrary parameter name:  and its definition separated by `:\s\s+`
            `parameter name` might contain\
            everything except a \
            [colon](//en.wikipedia.org/wiki/Colon_(punctuation))\
            and be multiline:               it still works
            """
            new_lines = []
            for line in lines:
                match = re.match(r'^(\s*)([^:]+):\s{2,}(.+)', line)
                if match:
                    new_lines.append(match.group(1) + match.group(2))
                    new_lines.append(match.group(1) + ':   ' + match.group(3))
                    new_lines.append('')
                else:
                    new_lines.append(line)

            return new_lines

    def extendMarkdown(self, md, md_globals):
        md.preprocessors.add('sane-def-list', SaneDefList.Prep(md), '_end')


class Pydoc(Extension):

    """ ## Docblocks meta marks processor """

    class Prep(Preprocessor):

        """ Preprocessor used to parse PyDoc-style comments like `:param name:` and format them. """

        regexps = dict(
            (re.compile(key, re.M), value)
            for key, value in
            {
                # `@param name`
                r'^(\s?)@(\w+)\s+(["\'\`].+["\'\`]|\S+)\s*(.*)$':
                r'\1<span class="pydoc pydoc-\2"><span>\2</span> <code>\3</code></span> \4<br/>',

                # `@var`
                r'^(\s?)@(\w+)(.*)$':
                r'\1<span class="pydoc pydoc-\2"><span>\2</span></span> \3<br/>',

                # `:param name:`
                r'^(\s?):([^: ]+)\s+([^:]+):(.*)$':
                r'\1<span class="pydoc pydoc-\2"><span>\2</span> <code>\3</code></span> \4<br/>',

                # `:return:`
                r'^(\s?):([^: ]+):(.*)$':
                r'\1<span class="pydoc pydoc-\2"><span>\2</span></span> \3<br/>'
            }.items()
        )

        def run(self, lines):
            """
            :param lines: Documentation lines
            :return: Lines of text with parsed PyDoc comments
            """
            new_lines = []
            for text in lines:
                for regex, template in self.regexps.items():
                    text = regex.sub(template, text)

                new_lines.append(text)
            return new_lines

    def extendMarkdown(self, md, md_globals):
        md.preprocessors.add('pydoc', Pydoc.Prep(md), '_end')


class AutoLinkExtension(Extension):

    """ ## Autolink extension
        There's already an inline pattern called autolink which handles\
        <http://www.google.com> type links. """

    EXTRA_AUTOLINK_RE = r'(?<!"|>)((https?://|www)[-\w./#?%=&]+)'

    class pattern(Pattern):

        def handleMatch(self, m):
            el = etree.Element('a')
            if m.group(2).startswith('http'):
                href = m.group(2)
            else:
                href = 'http://%s' % m.group(2)
            el.set('href', href)
            el.text = m.group(2)
            return el

    def extendMarkdown(self, md, md_globals):
        md.inlinePatterns.add(
            'extra_autolink',
            AutoLinkExtension.pattern(self.EXTRA_AUTOLINK_RE, self),
            '>autolink'
        )


class MathExtension(Extension):
    """
    ## Math extension for Python-Markdown

    Adds support for displaying math formulas using [MathJax](http://www.mathjax.org/).

    Author: 2015, Dmitry Shachnev <mitya57@gmail.com>.
    Slightly customized by cryptonomicon314
    """

    def __init__(self, *args, **kwargs):
        super(MathExtension, self).__init__(*args, **kwargs)

    def extendMarkdown(self, md, md_globals):
        def handle_match_inline(m):
            node = etree.Element('script')
            node.set('type', 'math/tex')
            node.text = AtomicString(m.group(3))
            return node

        def handle_match(m):
            node = etree.Element('script')
            node.set('type', 'math/tex; mode=display')
            if '\\begin' in m.group(2):
                node.text = AtomicString(m.group(2) + m.group(4) + m.group(5))
            else:
                node.text = AtomicString(m.group(3))
            return node

        inlinemathpatterns = (
            # Inline math with `$...$`
            Pattern(r'(?<!\\|\$)(\$)([^\$]+)(\$)'),
            # Inline math with `\(...\)`
            Pattern(r'(?<!\\)(\\\()(.+?)(\\\))')
        )
        mathpatterns = (
            # Display style math with `$$...$$`
            Pattern(r'(?<!\\)(\$\$)([^\$]+)(\$\$)'),
            # Display style math with `\[...\]`
            Pattern(r'(?<!\\)(\\\[)(.+?)(\\\])'),
            Pattern(r'(?<!\\)(\\begin{([a-z]+?\*?)})(.+?)(\\end{\3})')
        )
        for i, pattern in enumerate(inlinemathpatterns):
            pattern.handleMatch = handle_match_inline
            md.inlinePatterns.add('math-inline-%d' % i, pattern, '<escape')
        for i, pattern in enumerate(mathpatterns):
            pattern.handleMatch = handle_match
            md.inlinePatterns.add('math-%d' % i, pattern, '<escape')


class Haddock(Extension):
    """
    ## Haddock

    This is meant to be used with the Haskell language.

    Haddock is haskell's way of documenting a module's API.
    The idea is to insert annotated comments in the source,
    which will document the API for external consumption.
    These comments are different from the ones used for documenting the code.

    Haddock is also the name of the program that extracts the API
    documentaion from the annotated source files.

    Haddock has its own markup language, described
    [here](https://www.haskell.org/haddock/doc/html/markup.html).
    There are very few programs that can parse the haddock markup language correctly.
    One of them is [pandoc](http://pandoc.org/README.html),
    written in haskell, but with python bindings
    ([pypandoc](https://pypi.python.org/pypi/pypandoc/)).
    Haddock's full markup language is very dependent on the location of the
    text in the file, and nothing can really parse Haddock except Haddock itself.
    Our goal here is to merely support the text formatting directives, which
    map reasonably well into HTML.

    We will use pypandoc to parse the Haddock markup language into HTML.
    This requires having pandoc installed and is much slower than
    python's Markdown package, but it's the only way to parse Haddock
    reliably from python.
    """
    class Prep(Preprocessor):

        regex = re.compile(r"(((^|\n)\s*\|(?P<down>.*))|((^|\n)\s*\^(?P<up>.*)))", re.DOTALL)

        def template(self, match):
            text = match.group('down') or match.group('up')

            try:
                import pypandoc
            except ImportError:
                print("Install pandoc for Haddock extension")
                return text

            lines = text.split('\n')

            """
            The Module Characteristics

            According to Haddock's docs, these fields aren't
            really used by Haddock or any other program, for that matter,
            but the are usually included in the file, and we want to
            be able to typeset them correctly.

            The supported fields are only: `Module`, `Description`,
            `Copyright`, `License`, `Maintainer`, `Stability` and
            `Portability`. The syntax is YAML-like.

            Here is an example of the fields in use:

              ```yaml
              Module      : W
              Description : Short description
              Copyright   : (c) Some Guy, 2013; Someone Else, 2014
              License     : GPL-3
              Maintainer  : sample@email.com
              Stability   : experimental
              Portability : POSIX
              ```

            This is supposed to appear at the top of the module, but
            I can't find a formal specification, so we will highlight any
            valid characteristic (defined by the pair `name: value`,
            where `name` is a characteristic name) anywhere in the file.
            """

            module_characteristics = []
            for i, line in enumerate(lines):
                match = re.match(characteristic_re, line)
                if match:
                    module_characteristics.append(match_to_html(match))
                elif line.isspace() or not line:
                    pass
                else:
                    break
            characteristics_block = ''.join(module_characteristics)

            # The rest of the text (after the last characteristic) is normal Haddock text.
            rest = lines[i:]
            # Use *pypandoc* to convert Haddocks markup into HTML
            converted_rest = pypandoc.convert('\n'.join(rest), 'html', format='haddock')

            if characteristics_block:
                return haddock_template.format('\n'.join([characteristics_block, converted_rest]))
            else:
                return haddock_template.format(converted_rest)

        def run(self, lines):
            # We have no use for a list of lines, so we join them together.
            # It is easier to find the Haddock comments inside a text block
            # than inside a list of lines.
            text = '\n'.join(lines)
            # The result of `run()` is supposed to be a list of lines,
            # so we must split the text into lines again.
            return self.regex.sub(self.template, text).split('\n')

    def extendMarkdown(self, md, md_globals):
        md.preprocessors.add('haddock', Haddock.Prep(md), '_begin')


# ### Haddock Utilities

# #### Module Characteristic Utilities
def match_to_html(match):
    """
    Render a Module Characteristic
    """
    return ('<p class="module-characteristic"><strong>{0}</strong>: {1}</p>'
            .format(match.group('key'), match.group('value')))

# This regexp matches the names of all module characteristics
characteristic_key_re = \
    "(Module)|(Description)|(Copyright)|" + \
    "(License)|(Maintainer)|(Stability)|(Portability)"

# The regexp to parse a pair `(name, value)` for a module characteristic.
characteristic_re = (r"^\s*(?P<key>{key_re})\s*:\s*(?P<value>.*)"
                     .format(key_re=characteristic_key_re))


# #### Template for a Haddock comment

haddock_template = """
<div class="haddock">
  <div class="haddock-header">
    Haddock:
  </div>
  <div class="haddock-text">
    {0}
  </div>
</div>"""

# Example:
# ```haskell
# -- | Function @foo@ frobnicates the /bar/
# ```
#
# renders as:
# <div class="haddock">
#   <div class="haddock-header">
#     Haddock:
#   </div>
#   <div class="haddock-text">
#     Function <code>foo</code> frobnicates the <em>bar</em>.
#   </div>
# </div>
#


class NsLinks(Extension):
    """
    ### Namespace Links

    It makes it easier to refer to a namespaced function or
    macro definition in the code as a namespaced value.

    Using the Clojure language, for example:

    It turns patterns like this:
    ```
    [|foo.bar/frobnicator @ bar.clj|]
    ```
    into HTML links such as this:
    ```html
    <a href="bar.cljs.html#_frobnicator">
      foo.bar/frobnicator
    </a>
    ```
    which renders as:

    <a href="javascript:void(0);">
      foo.bar/frobnicator
    </a>

    This is meant to be customized for the supported languages.
    Customized versions are defined at
    [languages/\_\_init\_\_.py](languages/__init__.py.html).
    """

    # Initialize with default values.
    # There isn't really a good default value for `namespace_re`,
    # so it is empty by dafault.
    namespace_re = ""
    # Probably `_` will be defined as a prefix for all languages.
    # This prefix is used by crossclj.
    anchor_prefix = "_"

    class Prep(Preprocessor):

        def __init__(self, md, namespace_re, anchor_prefix):
            super(Prep, self).__init__(md)
            # Initialize the specific constants for this language.
            self.namespace_re = namespace_re
            self.anchor_prefix = anchor_prefix
            # TODO: Explain this regular expression.
            self.regex = re.compile(
                (r"(\[\|\s*(?P<namespace>{namespace_re})?(?P<name>\S+)" +
                 r"((\s+@\s+)(?P<path>\S.+))?\s*\|\])")
                .format(namespace_re=self.namespace_re), re.M
            )

        def template(self, match):
            namespace = match.group('namespace')
            name = match.group('name')
            path = match.group('path')
            if not namespace:
                namespace = ""

            if path:
                _, ext = os.path.splitext(path)
                if ext.lower() != '.html':
                    path += '.html'
            else:
                path = ""

            link_target = path + '#' + self.anchor_prefix + name
            link_text = namespace + name

            link_html = ("<a href={target}>{text}</a>\n"
                         .format(target=link_target, text=link_text))

            return link_html

        def run(self, lines):
            return [self.regex.sub(self.template, line) for line in lines]

    def extendMarkdown(self, md, md_globals):
        md.preprocessors.add('nslinks',
                             NsLinks.Prep(md, self.namespace_re, self.anchor_prefix),
                             '_begin')
