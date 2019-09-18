#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
sys.path.insert(0, os.path.abspath('../executor/'))

source_suffix = '.rst'
master_doc = 'index'
project = 'KubePortal'
version = '0.2.0'
release = '0.2.0'
copyright = u'2019, Peter Tröger'
author = u'Peter Tröger'
language = "en"
exclude_patterns = ['formats', 'Thumbs.db', '.DS_Store', 'modules.rst']
pygments_style = 'sphinx'

html_theme = "sphinx_rtd_theme"
