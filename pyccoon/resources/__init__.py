"""
Read Pycco static resources into module variables
"""
import os

realpath = os.path.realpath(__file__)

with open(os.path.join(os.path.dirname(realpath), "pycco.html"), 'rb') as f:
    html = f.read()

with open(os.path.join(os.path.dirname(realpath), "pycco.css"), 'rb') as f:
    css = f.read()

with open(os.path.join(os.path.dirname(realpath), "default_config.yaml"),'rb') as f:
    default_config = f.read()


css_filename = 'pyccoon.css'

static_files = [
    ('pyccoon.svg', 'pyccoon.svg'),
    ('pyccoon_icon.svg', 'pyccoon_icon.svg')
]
