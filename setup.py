#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Use `python setup.py sdist upload` to release on PyPi
"""

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from pyccoon import __version__

readme = open('README.rst').read()
history = open('HISTORY.rst').read().replace('.. :changelog:', '')


requirements = open("requirements.txt").read().split("\n")

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='pyccoon',
    version=__version__,
    description='Side-to-side documentation generator, a descendant of Pycco and Docco.',
    long_description=readme + '\n\n' + history,
    author='Andrii Magalich',
    author_email='andrew.magalich@gmail.com',
    url='https://github.com/ckald/pyccoon',
    packages=['pyccoon'],
    package_dir={'pyccoon': 'pyccoon'},
    include_package_data=True,
    install_requires=requirements,
    license="MIT",
    zip_safe=False,
    keywords='pyccoon',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: Implementation :: PyPy'
    ],
    test_suite='tests',
    tests_require=test_requirements,

    entry_points="""
    [console_scripts]
    pyccoon = pyccoon.pyccoon:main
    """
)
