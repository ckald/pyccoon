# -*- coding: utf-8 -*-

"""
![Pyccoon](pyccoon.svg)

"**Pyccoon**" is a side-to-side documentation generator.

It descended from [Pycco](https://github.com/fitzgen/pycco) — a Python port of
[Docco](http://jashkenas.github.com/docco/):
the original quick-and-dirty, hundred-line-long, literate-programming-style
documentation generator.

Pyccoon produces a static HTML website that displays your comments
alongside your code. Comments are formatted by
[Markdown](http://daringfireball.net/projects/markdown/syntax),
while the code is syntax highlighted by [Pygments](http://pygments.org/).
[MathJax](https://www.mathjax.org/) helps with the $\TeX$ notes.

**This website is the result of running Pyccoon against its source.**

Most probably you might want to use Pyccoon if you have a small-to-medium project
(for example, a certain static documentation generator) with a lot of explaining to do
or if you are a scientist that tries to sync the code with the context of research:

$$
    \frac{d y(t)}{d t} = \underset{h \rightarrow 0}{lim} \frac{y(t + h) - y(t)}{h}
$$

Pyccoon generates the documentation folder structured correspondingly to the code. To create
documentation `docs` for the project in `src` folder, run the following:

    pyccoon -s src -d docs

[Pyccoon](https://github.com/ckald/pyccoon) is released on GitHub under the MIT license.
"""

__author__ = 'Andrii Magalich'
__email__ = 'andrew.magalich@gmail.com'
__version__ = '0.1.5'

from .pyccoon import Pyccoon
