#!/usr/bin/env python3
# coding: utf_8

"""
Mikado.py is a Python suite whose purpose is to find and resolve genic loci in a
genomic annotation. This is the library it relies onto.
"""

__title__ = "Mikado.py"
__version__ = '0.9.6'
__author__ = 'Luca Venturini'
__license__ = 'GPL3'
__copyright__ = 'Copyright 2015 Luca Venturini'

import Mikado.exceptions
import Mikado.utilities
import Mikado.parsers
import Mikado.serializers
import Mikado.loci_objects
import Mikado.configuration
import Mikado.scales