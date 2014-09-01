"""
Read Pycco static resources into module variables
"""
import os

with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "pycco.html"), 'r') as f:
    html = f.read()

with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "pycco.css"), 'r') as f:
    css = f.read()

static_files = ['pyccoon.svg', 'pyccoon_icon.svg']
