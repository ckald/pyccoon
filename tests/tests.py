
import os
import unittest
from pyccoon import Pyccoon


class FileTest(unittest.TestCase):

    """
    Test case that takes care of initializing Pyccoon and cleaning up after it.
    """

    input_name = "tests.py"
    output_name = "tests.py.html"

    def setUp(self):
        """ Initialize Pyccoon in the same folder as `__file__` and force Pyccoon to run only over\
            specified input file."""

        self.folder = os.path.split(__file__)[0]

        self.input_name = os.path.join(self.folder, self.input_name)
        self.output_name = os.path.join(self.folder, self.output_name)

        self.pyccoon = Pyccoon({
            'sourcedir':    self.folder,
            'outdir':       self.folder,
            'verbosity':    0,
        }, process=False)
        self.pyccoon.sources = {os.path.split(self.input_name)[1]: (self.output_name, True)}

    def tearDown(self):
        """ Remove created files and verify they do not exist """
        for _, (dest, _) in self.pyccoon.sources.items():
            os.unlink(dest)
        assert not os.path.exists(self.output_name), "Dummy output file exists after test"

    def check(self, output):
        pass

    def test(self):
        """ The test itself. Starts pyccoon processing and invokes the `check` method """
        self.pyccoon.process()
        with open(self.output_name, "r") as temp:
            output = temp.read()
        self.check(output)

    def shortDescription(self):
        return self.check.__doc__


class DummyFileTest(FileTest):

    """
    Test case specially designed for convenient Pyccoon testing. Subclasses of it override `input`\
    param and `check` method, while everything else takes care of creating and removing temp input\
    and output files for Pyccoon.
    """

    input = ""
    input_name = "__test_input__.py"
    output_name = "__test_input__.py.html"

    def setUp(self):
        """ Additionally to `FileTest.setUp`, fill the input file with `input` data """
        super(DummyFileTest, self).setUp()

        with open(self.input_name, "w") as temp:
            temp.write(self.input)

    def tearDown(self):
        """ Remove created temporary files and verify they do not exist """
        super(DummyFileTest, self).tearDown()

        os.unlink(self.input_name)
        assert not os.path.exists(self.input_name), "Dummy input file exists after test"

    def check(self, output):
        """ DummyFileTest: Check that files exist. This method should be overridden """
        assert os.path.exists(self.input_name), "Dummy input file does not exist before test"
        assert os.path.exists(self.output_name), "Dummy output file does not exist before test"


class PyDocSubstitutions(DummyFileTest):
    input = """# :return:
               # :param something:
               # `:pre:`"""

    def check(self, output):
        self.assertTrue("pydoc-return" in repr(output),
                        "Single word PyDoc expression not converted")
        self.assertTrue("pydoc-param" in repr(output),
                        "Multiple words PyDoc expression not converted")
        self.assertTrue(":pre:" in repr(output), "PyDoc expression in `pre` converted")


class TodoSubstitutions(DummyFileTest):
    input = """# TODO: something
               # `FIXME: something`
               \"""`
               FIXME: not converted
               `\"""
            """

    def check(self, output):
        assert "class=todo" in repr(output), "TODO not converted"
        assert "FIXME: something" in repr(output), "FIXME in `pre` converted"
        # TODO: this one is failing. Will fix after migrating to Mistune markdown parser
        # assert "FIXME: not converted" in repr(output),\
            # "FIXME in multiline `pre` converted"


class Crossref(DummyFileTest):
    input = """ # [[1not_existing.py]]
                # [[tests.py]]
                # [[3not_existing.py#anchor]]
                # [[tests.py#anchor]]
                # [[Not existing named|5not_existing.py]]
                # [[Existing named|tests.py]]
                # [[Not existing named with anchor|7not_existing.py#anchor]]
                # [[Existing named with anchor|tests.py#anchor]]
                Malformed links tests:
                # [[multiline
                # link]]
            """

    def check(self, output):
        validation_list = [
            ['1not_existing.py"',                   "Link to not existing file"],
            ['tests.py.html',                       "Link to existing file"],
            ['3not_existing.py#anchor',             "Link to not existing file with anchor"],
            ['tests.py.html#anchor',                "Link to existing file with anchor"],
            ['Not existing named</a>',              "Named link to not existing file"],
            ['Existing named</a>',                  "Named link to existing file"],
            ['7not_existing.py#anchor',             "Named link to not existing file with anchor"],
            ['Not existing named with anchor</a>',  "Named link to not existing file with anchor"],
            ['tests.py.html#anchor',                "Named link to existing file with anchor"],
            ['Existing named with anchor',          "Named link to existing file with anchor"],
            ['[[multiline',                         "Multiline link processed"],
            ['link]]',                              "Multiline link processed"]
        ]
        for item in validation_list:
            self.assertTrue(item[0] in output, item[1])


class PythonLanguage(FileTest):
    input_name = "python_test_sample.py"
    output_name = input_name + ".html"

    def check(self, output):
        sections = self.pyccoon.sections

        self.assertFalse('for Pyccoon' in sections[0]['docs_text'],
                         "Multiline and inline comment were glued")
        self.assertFalse(sections[0]['code_html'], "There should be no code in the section")

        self.assertFalse('indent-based language' in sections[1]['docs_text'],
                         "Inline comments separated by an empty line were glued")
        self.assertFalse(sections[1]['code_html'], "There should be no code in the section")

        self.assertFalse('indent-based language' in sections[3]['docs_text'],
                         "Preceding comment attributed to the following function")
        self.assertTrue('def purpose' in sections[3]['code_text'],
                        "There should be code in the section")

        self.assertTrue('different features' in sections[3]['code_text'],
                        "Multiline string was mistaken for comment")
        self.assertTrue("The purpose of this test" in sections[3]['docs_text'], "Wrong splitting")

        self.assertTrue('@one_of' in sections[4]['code_text'])
        self.assertTrue('def are_decorators' in sections[4]['code_text'],
                        "Decorator separated from function")
        self.assertTrue('and also the convention' in sections[4]['docs_text'], "Lost docs")

        self.assertTrue('class a_useful_heuristic' in sections[5]['code_text'])
        self.assertTrue('for sections splitting' in sections[5]['docs_text'], "Class lost his docs")

        self.assertTrue('def basically' in sections[6]['code_text'])
        self.assertTrue('a documentation block' in sections[6]['docs_text'],
                        "Function lost its docs")

        self.assertTrue('if its_indentation' in sections[7]['code_text'])
        self.assertTrue('belongs to' in sections[7]['docs_text'], "If lost its docs")

        self.assertTrue('correspondence_of_the' in sections[8]['code_text'])
        self.assertTrue('naturally gives' in sections[8]['docs_text'], "If interior lost his docs")
        self.assertFalse('and_documentation' in sections[8]['code_text'], "Indent splitting broken")

        self.assertFalse(sections[9]['docs_text'], "There are no docs in the last section")


class RubyLanguage(FileTest):
    input_name = "ruby_test_sample.rb"
    output_name = input_name + ".html"

    def check(self, output):
        sections = self.pyccoon.sections
        # from subprocess import call
        # call(["open", os.path.join(self.folder, self.output_name)])
        # print(sections)

        for keyword in ["Title:", "Authors:", "Syntax:", "Example:", "See the documentation"]:
            self.assertTrue(keyword in sections[1]['docs_text'], "Inline comments were not glued")

        self.assertFalse('module' in sections[1]['code_text'],
                         "Scope keyword 'module' did not work")

        self.assertTrue('Render any' in sections[4]['docs_text']
                        and 'def render' in sections[4]['code_text']
                        and 'site = ' not in sections[4]['code_text'], "Wrong section splitting")

        self.assertTrue(sections[11]['code_text'].count('end') == 1,
                        "Indentation splitting does not work")
