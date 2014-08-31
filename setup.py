#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


readme = open('README.rst').read()
history = open('HISTORY.rst').read().replace('.. :changelog:', '')


requirements = [
    "wheel==0.23.0",
    "pystache==0.6",
    "markdown==2.4.1",
    "Pygments==1.6"
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='pyccoon',
    version='0.1.0',
    description='Side-to-side documentation generator, a descedant of Pycco and Docco.',
    long_description=readme + '\n\n' + history,
    author='Andrii Magalich',
    author_email='andrew.magalich@gmail.com',
    url='https://github.com/ckald/pyccoon',
    packages=['pyccoon', ],
    package_dir={'pyccoon': 'pyccoon'},
    include_package_data=True,
    install_requires=requirements,
    license="BSD",
    zip_safe=False,
    keywords='pyccoon',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    test_suite='tests',
    tests_require=test_requirements
)