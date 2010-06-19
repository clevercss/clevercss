
import unittest

import color_convert
import ccss_to_css
import minify

def all_tests():
    return unittest.TestSuite(getattr(mod, 'all_tests')() for mod in [color_convert, ccss_to_css, minify])

