#!/usr/bin/env python

import unittest
from magictest import MagicTest as TestCase

from textwrap import dedent

import clevercss
from clevercss import convert
from clevercss.line_iterator import LineIterator

class SpriteMapTestCase(TestCase):
    def convert_spritemap(self):
        self.assertEqual(convert(open('tests/example_sprites.ccss').read(), fname='tests/example_sprites.ccss'),
            correct)

correct = '''body {
  background-image: url(big.png) -0px -0px;
  width: 20px;
  height: 20px;
}

body div.other,
body .some {
  background-image: url(big.png) -0px -20px;
}'''
def all_tests():
    return unittest.TestSuite(case.toSuite() for case in [SpriteMapTestCase])

# vim: et sw=4 sts=4
