import re

from markdown.util import etree
from markdown.inlinepatterns import Pattern
from markdown.preprocessors import Preprocessor
from markdown.extensions import Extension


class Todo(Extension):

    """ == TODO, FIXME, WARNING, CAUTION marks == """

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

    """ == Lines connector extension == """

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

    """ == Better definition lists == """

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

    """ == Docblocks meta marks processor == """

    class Prep(Preprocessor):

        """ Preprocessor used to parse PyDoc-style comments like `:param name:` and format them. """

        def run(self, lines):
            """
            :param lines: Documentation lines
            :return: Lines of text with parsed PyDoc comments
            """
            new_lines = []
            for text in lines:
                # Regex that matches `@param name`
                text = re.compile(
                    r'^(\s?)@(\w+)\s+(["\'\`].+["\'\`]|\S+)\s*', re.M
                ).sub(
                    r'\1<span class="pydoc pydoc-\2"><span>\2</span> <code>\3</code></span> ',
                    text)
                # Regex that matches `@var`
                text = re.compile(
                    r'^(\s?)@(\w+)', re.M
                ).sub(
                    r'\1<span class="pydoc pydoc-\2"><span>\2</span></span>',
                    text)
                # Regex that matches `:param name:`
                text = re.compile(
                    r'^(\s?):([^: ]+) +([^:]+):', re.M
                ).sub(
                    r'\1<span class="pydoc pydoc-\2"><span>\2</span> <code>\3</code></span>',
                    text)
                # Regex that matches single-word comments: `:return:`
                text = re.compile(
                    r'^(\s?):([^: ]+):', re.M
                ).sub(
                    r'\1<span class="pydoc pydoc-\2"><span>\2</span></span>',
                    text)

                new_lines.append(text)
            return new_lines

    def extendMarkdown(self, md, md_globals):
        md.preprocessors.add('pydoc', Pydoc.Prep(md), '_end')


class AutoLinkExtension(Extension):

    """ == Autolink extension ==
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
