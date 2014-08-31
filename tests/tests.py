"""
Things to test in Pycco:

*   Skipping Markdown substitutions in the `<pre>` sections
*   (Single-line) comments at the end of the file
*   Subsequent (multi-line) comments

        #!/usr/bin/env python
        ""
        "**Pycco**" is a Python port of [Docco](http://jashkenas.github.com/docco/):\
        the original quick-and-dirty, hundred-line-long, literate-programming-style\
        documentation generator. It produces HTML that displays your comments\
        alongside your code. Comments are passed through \
        [Markdown](http://daringfireball.net/projects/markdown/syntax) and\
        [SmartyPants](http://daringfireball.net/projects/smartypants), while code is\
        passed through [Pygments](http://pygments.org/) for syntax highlighting.
        This page is the result of running Pycco against its own source file.
        ""

        ""
        Pycco generates the documentation folder structured correspondingly to the code. To create \
        documentation `docs` for the project in `src` folder, run the following:

            $ python src/utils/pycco.py -s src -d docs

        The [original source for Pycco](https://github.com/fitzgen/pycco) is available on GitHub,\
        and released under the MIT license.
        ""

*   Same indentation level multi-line comments:

        ""
        ## KPEX keyphrase extractor

        This module wraps around the KPEX extractor and declares its API.
        ""

        import os
        import re
        import subprocess
        import tempfile

        from django.conf import settings as platform_settings

        ""
        Default configs for different platform domains.
        TODO: leave one default configuration, move others to platform settings.
        ""

*   This thing (wrong indentation matching):

        # Set default settings and override them with platform settings
        default_settings = {
            # Path to the folder that contains `kpex` executable
            "KPEX_PATH": "/opt/bin/kpex",
            # Command-line invocation template with several parameters:
            # :param path: KPEX_PATH
            # :param weights: Text sections weights
            # :param domain: Platform instance (e.g., `physics`, `bio`)
            # :param input: Input file
            "template":  "{{path}}/kpex --struct-weights {{weights}} "
                         "--max-length 3 -n 10 --freq -d {{domain}} {{input}}"
        }.update(configs['climate'])

        settings = default_settings
        settings.update(platform_settings)

*   This thing (wrong comment splitting):

        # Set default settings and override them with platform settings
        default_settings = {
            # Path to the folder that contains `kpex` executable
            "KPEX_PATH": "/opt/bin/kpex",
            "" Command-line invocation template with several parameters:
            :param path: KPEX_PATH
            :param weights: Text sections weights
            :param domain: Platform instance (e.g., `physics`, `bio`)
            :param input: Input file ""
            "template":  "{{path}}/kpex --struct-weights {{weights}} "
                         "--max-length 3 -n 10 --freq -d {{domain}} {{input}}"
        }.update(configs['climate'])

        settings = default_settings
        settings.update(platform_settings)
"""

import os
import unittest
from pyccoon import pyccoon


class DummyFileTest(unittest.TestCase):

    """
    `TestCase` specially designed for Pycco testing. Subclasses of it override `input` param\
    and `check` method, while everything else takes care of creating and removing temp input and\
    output files for Pycco.
    """

    input = ""
    input_name = "__test_input__.py"
    output_name = "__test_input__.html"

    def setUp(self):
        """ Initialize Pycco in the same folder as `__file__`, create a temporary input file\
            and force Pycco to run only over it."""
        folder = os.path.split(__file__)[0]
        self.pycco = Pycco({
            'sourcedir':    folder,
            'outdir':       folder
        })
        with open(self.input_name, "w") as temp:
            temp.write(self.input)

        self.pycco.sources = [self.input_name]

    def tearDown(self):
        """ Remove created temporary files and check if they do not exist """
        os.unlink(self.input_name)
        os.unlink(self.output_name)
        assert not os.path.exists(self.input_name), "Dummy input file exists after test"
        assert not os.path.exists(self.output_name), "Dummy output file exists after test"

    def check(self, output):
        """ Check that dummy file exist at this point. This method should be overrided in \
            inherited classes """
        assert os.path.exists(self.input_name), "Dummy input file does not exist before test"
        assert os.path.exists(self.output_name), "Dummy output file does not exist before test"

    def test(self):
        """ The test itself. Starts pycco processing and invokes the `check` method """
        self.pycco.process()
        with open(self.output_name, "r") as temp:
            output = temp.read()
        self.check(output)


class PyDocSubstitutions(DummyFileTest):
    input = """# :return:
               # :param something:
               # `:pre:`"""

    def check(self, output):
        assert "pydoc-return" in repr(output), "Single word PyDoc expression not converted"
        assert "pydoc-param" in repr(output), "Multiple words PyDoc expression not converted"
        assert "<code>:pre:</code>" in repr(output), "PyDoc expression in `pre` converted"


class TodoSubstitutions(DummyFileTest):
    input = """# TODO: something
               # `FIXME: something`
               \"""`
               FIXME: not converted
               `\"""
            """

    def check(self, output):
        assert "class=todo" in repr(output), "TODO not converted"
        assert "<code>FIXME: something</code>" in repr(output), "FIXME in `pre` converted"
        assert "<code>FIXME: not converted</code>" in repr(output),\
            "FIXME in multiline `pre` converted"
