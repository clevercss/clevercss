from unittest import TestCase, main
from textwrap import dedent

from clevercss import convert

class MediaTypeTestCase(TestCase):

    def test_01_global_media_type(self):
        self.assertConversion(
            """
            @media print:
              a:
                text-decoration: none""",

            """
            @media print {

            a {
              text-decoration: none;
            }

            } /* @media print */""")

    def test_02_leading_media_type(self):
        self.assertConversion(
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

            } /* @media print */



            a {
              font-weight: bold;
            }""")

    def test_03_trailing_media_type(self):
        self.assertConversion(
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

            } /* @media print */""")

    def test_04_change_media_type(self):
        self.assertConversion(
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

            } /* @media aural */



            @media print {

            a {
              text-decoration: none;
            }

            } /* @media print */""")

    def test_05_repeat_media_type(self):
        self.assertConversion(
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

            } /* @media print */""")

    def test_06_nested_media_type(self):
        self.assertConversion(
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

            } /* @media print */



            @media handheld {

            #content strong {
              font-weight: bold;
            }

            } /* @media handheld */



            @media print {

            a {
              text-decoration: none;
            }

            } /* @media print */""")

    def assertConversion(self, ccss, css):
        got = convert(dedent(ccss))
        expected = dedent(css).lstrip()
        assert got == expected, '\n' + got

if __name__ == '__main__':
    main()
