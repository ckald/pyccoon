<p align="center">
<a href="http://ckald.github.io/pyccoon/">
<img src="https://www.dropbox.com/s/n6s0ngrjl69ct09/pyccoon.svg?dl=1" alt="Pyccoon" />
</a>
</p>

[![PyPi package](https://badge.fury.io/py/pyccoon.png)](http://badge.fury.io/py/pyccoon)
[![Build Status](https://travis-ci.org/ckald/pyccoon.svg?branch=master)](https://travis-ci.org/ckald/pyccoon)
[![Downloads](https://pypip.in/d/pyccoon/badge.png)](https://pypi.python.org/pypi/pyccoon)

Side-to-side documentation generator. Fork of the [Pycco](http://fitzgen.github.io/pycco/), grandfork of the [Docco](http://jashkenas.github.com/docco/). And an object-oriented one.

[See how it works](http://ckald.github.io/pyccoon/)

# Installation

At the moment the release on the PyPi is being prepared. In the meanwhile, to use the Pyccoon

```bash
git clone https://github.com/ckald/pyccoon.git
cd pyccoon
python setup.py install
```

And you're done. Pyccoon is compatible with Python 2.6, 2.7, 3.3, 3.4 and PyPy. Latest test results can be seen on the [Travis CI project page](https://travis-ci.org/ckald/pyccoon).

# Usage

To generate the project documentation

```bash
pyccoon -s <source folder> -d <documentation folder>
```

For additional CLI options, see `pyccoon --help`

At the moment Pyccoon supports Python, Ruby, Javascript, PHP and C/C++ source files. Other project files will be simply copied to the documentation folder. For additional configuration, create a config file of the kind:

```js
{
    // Documentation title
    "project_name": "pyccoon v0.1.0 documentation",
    // Skip files matching any of the list of regular expressions
    "skip_files": [".+\\.pyc", "__pycache__", "\\.travis.yml", "\\.git", "\\.DS_Store"],
    // Copy files without processing (useful if you have some binary files)
    "copy_files": ["pyccoon.svg", "pyccoon_icon.svg", ".+\\.html", ".+\\.css", "\\.pyccoon"],
    // MathJax (http://mathjax.org) support - sometimes we want nice formulas
    "mathjax": false
}
```

# Development roadmap

  - [x] Initial version
      - [x] Python
      - [x] Ruby
      - [x] JavaScript (incomplete, but will do)
      - [x] C/C++ (incomplete)
      - [x] PHP (incomplete)
  - [x] Better page layout
  - [x] Documentation website
  - [ ] Write test suites and extend supported languages list:
      - [x] Python
      - [ ] Ruby
      - [ ] PHP
      - [ ] JavaScript
      - [ ] C/C++
      - [ ] CoffeScript
      - [ ] Perl
      - [ ] SQL
      - [ ] Scheme
      - [ ] Lua
      - [ ] Erlang
      - [ ] Tcl
      - [ ] Haskell
      - [ ] CSS, LESS, SASS
  - [ ] Fix bugs:
      - [x] Fix `--watch` option
      - [x] Broken cross-referencing (wikilinks)
      - [x] Fix multiple Python versions compatibility
      - [ ] Replace Python Markdown with [Mistune](http://mistune.readthedocs.org/en/latest/) (because we want nice extensions)
          - [ ] Restrict extensions to specific block types
          - [ ] Create LaTeX codeblocks (to avoid unnecessary `\begin{equation}...\end{equation}` in the docs and restrict MathJax parsing only to specific elements on the page)
      - [ ] Use `glob`: replace config file regular expressions with more natural wildcards (also support matching against the whole path, not only filename)
      - [ ] Add (actually, fix) line numbers feature (tricky)
      - [ ] Test against multilanguage projects (i.e., what happens if there are `index.html` and `__init__.py` in one folder?)
      - [ ] Link index files instead of renaming (`__init__.py` -> `index.html`)
  - [ ] Release on PyPi
  - [ ] Additional features:
      - [ ] Object retrieval and cross-linking ("jump to definition" for classes, functions)
      - [ ] Search
      - [ ] Extended docblocks parsing (capturing shortcuts and aliases for cross-linking)
      - [ ] Mixed documents parsing: HTML/JS/CSS, HTML/PHP, etc.
      - [ ] `TODO:` statements, linting and coverage reports

-------

# Acknowledgements

  * [Nick Fitzgerald](http://github.com/fitzgen) as an author of [Pycco](https://github.com/fitzgen/pycco) that was a starting point of the development
  * [Jeremy Ashkenas](https://github.com/jashkenas) as an author of original idea - [Docco](https://github.com/jashkenas/docco)
  * Raccoon designed by [Christy Presler](http://www.thenounproject.com/cnpresler) from the [Noun Project](http://www.thenounproject.com/)
