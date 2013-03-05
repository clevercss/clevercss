from unittest import TestCase, main

import unittest

from tests import color_convert
from tests import ccss_to_css
from tests import minify
from tests import spritemap_test
from tests import mediatype

def all_tests():
    return unittest.TestSuite(getattr(mod, 'all_tests')() for mod in [color_convert,
        ccss_to_css, minify, spritemap_test, mediatype])

