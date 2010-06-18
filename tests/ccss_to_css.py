#!/usr/bin/env python

import unittest
from magictest import MagicTest as TestCase
from clevercss import convert

class ConvertTestCase(TestCase):
    def convert(self):
        self.assertEqual(convert('''body: 
            color: $color 
        ''',{'color':'#eee'}),
        u'body {\n  color: #eeeeee;\n}')
    
    def convert2(self):
        self.assertEqual(convert('''body:
            background-color: $background_color
        ''', {'background_color': 'red.darken(10)'}),
        u'body {\n  background-color: #cc0000;\n}')

    def convert_rgba(self):
        self._test_attr('background-color','rgba(0, 255, 100%, 0.3)', 'rgba(0, 255, 255, 0.3)')

    def convert_rgba_float(self):
        self._test_attr('background-color','rgba(0, 255, 100%, .3)', 'rgba(0, 255, 255, 0.3)')

    def convert_float(self):
        self._test_attr('top','.3', '0.3')

    def _test_attr(self, attr, ccval, cssval):
        self.assertEqual(convert('body:\n  %s: %s\n' % (attr, ccval)), 'body {\n  %s: %s;\n}' % (attr, cssval))

def all_tests():
    return unittest.TestSuite(case.toSuite() for case in [ConvertTestCase])

# vim: et sw=4 sts=4
