# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

# 📁 Path to project: .../project/docs/source/conf.py (текущее расположение)
sys.path.insert(0, os.path.abspath("../.."))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "pyqt-chat-8740"
copyright = "2024, WillyWonka"
author = "WillyWonka"
release = "0.1"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = []
extensions += ["sphinx.ext.duration"]
extensions += ["sphinx.ext.doctest"]
extensions += ["sphinx.ext.autodoc"]

templates_path = ["_templates"]
exclude_patterns = []

language = "ru"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# html_theme = 'alabaster'
html_theme = "sphinx_book_theme"
html_static_path = ["_static"]
