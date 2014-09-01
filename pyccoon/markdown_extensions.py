import re

from markdown.util import etree
from markdown.inlinepatterns import Pattern
from markdown.preprocessors import Preprocessor
from markdown.extensions import Extension

import pygments
from pygments import lexers, formatters


class Todo(Extension):
    class Prep(Preprocessor):

        """
        Markdown preprocessor that matches all TODO and FIXME strings occurring at the beginning\
        of the line or after the `#` symbol and highlights them in the documentation.
        """

        matched_strings = ["TODO", "FIXME", "WARNING", "CAUTION"]
        regex = re.compile("(#|^)\s*(" + "|".join(matched_strings) + ":?)(.*)", flags=re.I)

        def template(self, match):
            """
            Intended markup for TODO strings. The type of the string is used as a class.
            """
            return "{:s}<span class={:s}><strong>{:s}</strong>{:s}</span>"\
                .format(match.group(1), match.group(2).lower(), match.group(2), match.group(3))

        def run(self, lines):
            """
            String matching is case insensitive
            """
            return [self.regex.sub(self.template, line, re.I) for line in lines]

    def extendMarkdown(self, md, md_globals):
        md.preprocessors.add('todo', Todo.Prep(md), '_end')


class LineConnector(Extension):

    def __init__(self, regex=r"(\S)\s*\\\s*\n\s*(\S)", sub=r"\1 \2", *args, **kwargs):

        regex = re.compile(regex, flags=re.M)

        class Prep(Preprocessor):

            def run(self, lines):
                """ Method ensures that there is exactly one space between 2 joined strings. """
                return regex.sub(sub, "\n".join(lines)).split("\n")

        self.Prep = Prep()

        super(LineConnector, self).__init__(*args, **kwargs)

    def extendMarkdown(self, md, md_globals):
        md.preprocessors.add('line-connector', self.Prep, '_end')


class SaneDefList(Extension):
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
    class Prep(Preprocessor):

        """
        Preprocessor used to parse PyDoc-style comments like `:param name:` and format them.
        """

        def run(self, lines):
            """
            :param lines: Documentation lines
            :return: Lines of text with parsed PyDoc comments
            """
            new_lines = []
            for text in lines:
                # Regex that matches `@param name`
                text = re.sub(
                    r'^(\s?)@(\w+)\s+(["\'\`].+["\'\`]|\S+)\s*',
                    r'\1<span class="pydoc pydoc-\2"><span>\2</span> <code>\3</code></span> ',
                    text, re.M)
                # Regex that matches `@var`
                text = re.sub(
                    r'^(\s?)@(\w+)',
                    r'\1<span class="pydoc pydoc-\2"><span>\2</span></span>',
                    text, re.M)
                # Regex that matches `:param name:`
                text = re.sub(
                    r'^(\s?):([^: ]+) +([^:]+):',
                    r'\1<span class="pydoc pydoc-\2"><span>\2</span> <code>\3</code></span>',
                    text, re.M)
                # Regex that matches single-word comments: `:return:`
                text = re.sub(
                    r'^(\s?):([^: ]+):',
                    r'\1<span class="pydoc pydoc-\2"><span>\2</span></span>',
                    text, re.M)

                new_lines.append(text)
            return new_lines

    def extendMarkdown(self, md, md_globals):
        md.preprocessors.add('pydoc', Pydoc.Prep(md), '_end')


class AutoLinkExtension(Extension):
    """
    There's already an inline pattern called autolink which handles
    <http://www.google.com> type links. So lets call this extra_autolink
    """

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


class FencedCodeExtension(Extension):

    class Prep(Preprocessor):

        """
        Preprocessor used to parse fenced code blocks (Github syntax) highlight and format them.
        """

        regex = re.compile(r'```(\w*)$\n^([\s\S]*)$\n^\s*```', flags=re.M)

        def run(self, lines):
            text = "\n".join(lines)
            for match in self.regex.finditer(text):
                code = match.group(2)
                language = match.group(1)

                try:
                    lexer = lexers.get_lexer_by_name(language)
                except:
                    print("Pygments lexer `{}` not found, guessing".format(language))
                    lexer = lexers.guess_lexer(code)

                text = text[:match.start()]\
                    + pygments.highlight(
                        code, lexer,
                        formatters.get_formatter_by_name('html'))\
                    + text[match.end():]
            return text.split('\n')

    def extendMarkdown(self, md, md_globals):
        md.preprocessors.add('fenced_code_highlight', FencedCodeExtension.Prep(md), '<html_block')
