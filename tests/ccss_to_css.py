#!/usr/bin/env python

import os
import sys
import unittest
from tests.magictest import MagicTest as TestCase

from textwrap import dedent

import clevercss
from clevercss import convert
from clevercss.line_iterator import LineIterator

from clevercss.errors import *

def eigen_test():
    filename = os.path.join(os.path.dirname(__file__), 'eigentest.ccss')
    ccss = open(filename).read()
    return clevercss.convert(ccss)

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

    def test_math(self):
        self.assertEqual(convert(dedent("""
        div:
            margin: -2px -2px
            padding: 2px + 2px
            top: 1px+1
            left: 5+5px
            right: 4px-5px
            bottom: 0 - 5px
            text-shadow: 0px -1px 8px #fff
        """)), dedent("""
        div {
          margin: -2px -2px;
          padding: 4px;
          top: 2px;
          left: 10px;
          right: -1px;
          bottom: -5px;
          text-shadow: 0px -1px 8px #ffffff;
        }""").strip())

    def test_eigen(self):
        if sys.version_info >= (3, 0):
            # round() behavior changed in Python 3
            # http://docs.python.org/3/whatsnew/3.0.html#builtins
            a_hover_color = '#4c0000'
        else:
            a_hover_color = '#4d0000'
        self.assertEqual(eigen_test(),dedent("""
        body {
          font-family: serif, sans-serif, Verdana, 'Times New Roman';
          color: #111111;
          padding-top: 4px;
          padding-right: 5px;
          padding-left: 5px;
          padding-bottom: 4px;
          background-color: #eeeeee;
        }

        div.foo {
          width: 220px;
          foo: foo/bar/baz/42;
        }

        a {
          color: #ff0000;
        }

        a:hover {
          color: %(a_hover_color)s;
        }

        a:active {
          color: #ff1a1a;
        }

        div.navigation {
          height: 1.2em;
          padding: 0.2em;
          foo: '1 2 3';
        }

        div.navigation ul {
          margin: 0;
          padding: 0;
          list-style: none;
        }

        div.navigation ul li {
          float: left;
          height: 1.2em;
        }

        div.navigation ul li a {
          display: block;
          height: 1em;
          padding: 0.1em;
        }
        """ % {'a_hover_color': a_hover_color}).strip())

    def test_import_line(self):
      """
      Tests the @import url() command. assumes the code is running in the main
      directory. (i.e. python -c 'from tests import *; main()' from the same
      dir as clevercss)
      """
      self.assertEqual(convert(dedent("""
      @import url(tests/example.ccss)

      div:
          color: $arg
      """)), dedent("""
      #test1 {
        color: blue;
      }

      #test2 {
        color: blue;
      }

      #test3 {
        color: blue;
      }

      div {
        color: blue;
      }""").strip())


    def test_multiline_rule(self):
        self.assertEqual(convert(dedent("""
        ul.item1 li.item1,
        ul.item2 li.item2,
        ul.item3 li.item3:
            font-weight: bold
        """)), dedent("""
        ul.item1 li.item1,
        ul.item2 li.item2,
        ul.item3 li.item3 {
          font-weight: bold;
        }""").strip())

    def backstring(self):
        self.assertEqual(convert(dedent('''
        div.round:
            background-image: `-webkit-gradient(top left, bottom right, from(#fff), to(#000))`
        ''')), dedent('''\
        div.round {
          background-image: -webkit-gradient(top left, bottom right, from(#fff), to(#000));
        }'''))


class MacroTestCase(TestCase):
    def simpleMacro(self):
        ccss = dedent('''
        def simple:
            color: red
            font-size: 3px+10px
        body:
            $simple
            width:200px
        .other:
            $simple
        ''')
        css = dedent('''\
        body {
          color: red;
          font-size: 13px;
          width: 200px;
        }

        .other {
          color: red;
          font-size: 13px;
        }''')
        self.assertEqual(convert(ccss), css)

    def test_undefined_macro(self):
        ccss = dedent('''
        body:
            $simple
            width:200px
        .other:
            $simple
        ''')
        self.assertRaises(ParserError, convert, ccss)

class LineIterTestCase(TestCase):
    def test_comments(self):
        line_iter = LineIterator(dedent(
        """
        /* block */
        /* multiblock
        */

        aa, /* comment */bb:
            x:1 // comment

        """))
        self.assertEqual("\n".join([s[1] for s in line_iter]),
            "aa, bb:\n    x:1")


def all_tests():
    return unittest.TestSuite(case.toSuite() for case in [ConvertTestCase, LineIterTestCase, MacroTestCase])

# vim: et sw=4 sts=4
