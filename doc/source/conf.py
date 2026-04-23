
# Configuration file for the Sphinx documentation builder.

import os
import sys

# Add the mock site packages to sys.path
sys.path.insert(0, os.path.abspath('../mock_site_packages'))
# Add scripts if needed
sys.path.insert(0, os.path.abspath('../../scripts')) 

# Project information
project = 'Lorenzetti'
copyright = '2025, Lorenzetti Team'
author = 'Lorenzetti Team'
release = '1.0.0'

# General configuration
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.todo',
    'sphinx.ext.mathjax',
    'breathe',
    'nbsphinx',
]

# Breathe configuration
breathe_projects = {
    "Lorenzetti": "../doxygen/xml/"
}
breathe_default_project = "Lorenzetti"

# Autodoc configuration
autodoc_mock_imports = ['ROOT', 'cppyy', 'maestro_lightning']
autodoc_typehints = 'description'

templates_path = ['_templates']
exclude_patterns = []

# HTML output
html_theme = 'sphinx_rtd_theme'
html_logo = '_static/images/logo.png'
html_static_path = ['_static']

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True
