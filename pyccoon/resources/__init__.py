"""
Read Pycco static resources into module variables
"""
import os

with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "pycco.html"), 'rb') as f:
    html = f.read()

with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "pycco.css"), 'rb') as f:
    css = f.read()
css_filename = 'pyccoon.css'

static_files = [
    ('pyccoon.svg', 'pyccoon.svg'),
    ('pyccoon_icon.svg', 'pyccoon_icon.svg')
]
