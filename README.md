<p align="center">
<a href="http://ckald.github.io/pyccoon/">
<img src="https://www.dropbox.com/s/n6s0ngrjl69ct09/pyccoon.svg?dl=1" alt="Pyccoon" />
</a>
</p>

[![Build Status](https://travis-ci.org/ckald/pyccoon.svg?branch=master)](https://travis-ci.org/ckald/pyccoon)

Side-to-side documentation generator. Fork of the [Pycco](http://fitzgen.github.io/pycco/), grandfork of the [Docco](http://jashkenas.github.com/docco/). And an object-oriented one.

[See how it works](http://ckald.github.io/pyccoon/)

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
      - [ ] Replace Python Markdown with Mistune (because we need nice extensions http://mistune.readthedocs.org/en/latest/)
          - [ ] Restrict extensions to specific block types
          - [ ] Create LaTeX codeblocks (to avoid unnecessary `\begin{equation}...\end{equation}` in the docs and restrict MathJax parsing only to specific elements on the page)
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

Raccoon designed by <a href="http://www.thenounproject.com/cnpresler">Christy Presler</a> from the <a href="http://www.thenounproject.com">Noun Project</a>
