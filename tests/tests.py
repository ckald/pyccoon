
import os
import unittest
from pyccoon import Pyccoon


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
        self.pyccoon = Pyccoon({
            'sourcedir':    folder,
            'outdir':       folder
        })
        with open(self.input_name, "w") as temp:
            temp.write(self.input)

        self.pyccoon.sources = [self.input_name]

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
        self.pyccoon.process()
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
