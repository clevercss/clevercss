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

def all_tests():
    return unittest.TestSuite(case.toSuite() for case in [ConvertTestCase])

# vim: et sw=4 sts=4
