#!/usr/bin/env python

import unittest
from tests.magictest import MagicTest as TestCase

import clevercss
from clevercss import convert

class MinifiedConvertTestCase(TestCase):
    def test_01_min_convert(self):
        self.assertEqual(convert('''body:
            color: $color
        ''',{'color':'#eeeeee'}, minified=True),
        u'body{color:#eee}')

    def test_02_min_convert(self):
        self.assertEqual(convert('''body:
            background-color: $background_color
        ''', {'background_color': 'red.darken(10)'}, minified=True),
        u'body{background-color:#c00}')

    def test_02_min_convert_colors(self):
        self.assertEqual(convert('''body:
            background-color: #ffff00
            color: #fffafa
            p:
                background-color: #ff0000
                color: khaki
        ''', minified=True),
        u'body{background-color:#ff0;color:snow}body p{background-color:red;color:khaki}')

def all_tests():
    return unittest.TestSuite(case.toSuite() for case in [MinifiedConvertTestCase])


# vim: et sw=4 sts=4
