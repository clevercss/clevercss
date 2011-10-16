import unittest
from unittest import TestCase, main
from textwrap import dedent
from magictest import MagicTest as TestCase

from clevercss import convert

class MediaTypeTestCase(TestCase):

    def test_01_global_media_type(self):
        self._assertConversion(
            """
            @media print:
              a:
                text-decoration: none""",

            """
            @media print {

              a {
                text-decoration: none;
              }

            }""")

    def test_02_leading_media_type(self):
        self._assertConversion(
            """
            @media print:
              a:
                text-decoration: none
            a:
              font-weight: bold""",

            """
            @media print {

              a {
                text-decoration: none;
              }

            }


            a {
              font-weight: bold;
            }""")

    def test_03_trailing_media_type(self):
        self._assertConversion(
            """
            a:
              font-weight: bold
            @media print:
              a:
                text-decoration: none""",

            """
            a {
              font-weight: bold;
            }

            @media print {

              a {
                text-decoration: none;
              }

            }""")

    def test_04_change_media_type(self):
        self._assertConversion(
            """
            @media aural:
              a:
                font-weight: bold
            @media print:
              a:
                text-decoration: none""",

            """
            @media aural {

              a {
                font-weight: bold;
              }

            }


            @media print {

              a {
                text-decoration: none;
              }

            }""")

    def test_05_repeat_media_type(self):
        self._assertConversion(
            """
            @media print:
              strong:
                font-weight: bold
            @media print:
              a:
                text-decoration: none""",

            """
            @media print {

              strong {
                font-weight: bold;
              }

              a {
                text-decoration: none;
              }

            }""")

    def test_06_nested_media_type(self):
        self._assertConversion(
            """
            @media print:
              #content:
                background: none
                @media handheld:
                  strong:
                    font-weight: bold
              a:
                text-decoration: none""",

            """
            @media print {

              #content {
                background: none;
              }

            }


            @media handheld {

              #content strong {
                font-weight: bold;
              }

            }


            @media print {

              a {
                text-decoration: none;
              }

            }""")

    def test_06_minimal_media_type(self):
        self._assertConversion(
            """
            @media print:
              #content:
                background: none
                @media handheld:
                  strong:
                    font-weight: bold
              a:
                text-decoration: none

            a:
                color: red

            @media handheld:
                td:
                    background-color: green""",
            """
            @media print{
              #content{
                background:none}
            }
            @media handheld{
              #content strong{
                font-weight:bold}
            }
            @media print{
              a{
                text-decoration:none}
            }
            a{
                color:#f00}
            @media handheld{
                td{
                    background-color:green}
            }
            """,
            minified=True)

    def _assertConversion(self, ccss, css, minified=False):
        got = convert(dedent(ccss), minified=minified)
        expected = dedent(css).lstrip()
        if minified:
            expected = ''.join(line.lstrip(' ') for line in expected.splitlines())
        assert got == expected, '\n' + expected.replace('\n', r'\n') + '\n' + got.replace('\n', r'\n')

def all_tests():
    return unittest.TestSuite(case.toSuite() for case in [MediaTypeTestCase])

if __name__ == '__main__':
    main()
