#!/usr/bin/env python

import unittest
from unittest import main
from tests.magictest import MagicTest as TestCase

from clevercss.utils import rgb_to_hls, hls_to_rgb

class RgbToHlsTestCase(TestCase):

    def rgb_to_hls(self):
        self._assertEqualHLS(rgb_to_hls(10, 100, 250),
                            [0.6042, 0.5098, 0.9600])

    def rgb_to_hls_underflow(self):
        self._assertEqualHLS(rgb_to_hls(-10, 100, 250),
                            [0.5962, 0.4706, 1.0833])

    def rgb_to_hls_overflow(self):
        self._assertEqualHLS(rgb_to_hls(10, 300, 250),
                            [0.4713, 0.6078, 1.4500])

    def _assertEqualHLS(self, got, expected):
        self.assertEqual([round(x, 4) for x in got],
                         [round(x, 4) for x in expected])

class HlsToRgbTestCase(TestCase):
    def hls_to_rgb(self):
        self.assertEqual(hls_to_rgb(0.6042, 0.5098, 0.9600),
                         (10, 100, 250))

    def hls_to_rgb_underflow(self):
        self.assertEqual(hls_to_rgb(0.5962, 0.4706, 1.0833),
                         (-10, 100, 250))

    def hls_to_rgb_overflow(self):
        self.assertEqual(hls_to_rgb(0.4713, 0.6078, 1.4500),
                         (10, 300, 250))

    def _assertEqualHLS(self, got, expected):
        self.assertEqual([round(x, 4) for x in got],
                         [round(x, 4) for x in expected])

class HlsRgbFuzzyTestCase(TestCase):
    def hls_to_rgb_and_back_fuzzy(self):
        for i in range(100):
            self._do_fuzzy()

    def _do_fuzzy(self):
        from random import seed, randint
        seed(0)
        rgb = tuple(randint(0, 255) for i in range(3))
        hls = rgb_to_hls(*rgb)
        hls2rgb = hls_to_rgb(*hls)
        self.assertEqual(rgb, hls2rgb)
        rgb2hls = rgb_to_hls(*hls2rgb)
        self.assertEqual(rgb2hls, hls)

def all_tests():
    return unittest.TestSuite(case.toSuite() for case in [RgbToHlsTestCase, HlsRgbFuzzyTestCase, HlsToRgbTestCase])

# vim: et sw=4 sts=4
