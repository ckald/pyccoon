
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
        os.unlink(self.output_name)
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
        self.assertIn("pydoc-return", repr(output), "Single word PyDoc expression not converted")
        self.assertIn("pydoc-param", repr(output), "Multiple words PyDoc expression not converted")
        self.assertIn(":pre:", repr(output), "PyDoc expression in `pre` converted")


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
        assert "FIXME: not converted" in repr(output),\
            "FIXME in multiline `pre` converted"


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
            self.assertIn(item[0], output, item[1])
