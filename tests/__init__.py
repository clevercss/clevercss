
import unittest

import color_convert
import ccss_to_css

def all_tests():
    return unittest.TestSuite(getattr(mod, 'all_tests')() for mod in [color_convert, ccss_to_css])

