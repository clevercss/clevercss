from unittest import TestCase, main
from textwrap import dedent

from clevercss import rgb_to_hls

class RgbToHlsTestCase(TestCase):

    def test_01_rgb_to_hls(self):
        self.assertEqualHLS(rgb_to_hls(10, 100, 250),
                            [0.6042, 0.5098, 0.9600])

    def test_02_rgb_to_hls_underflow(self):
        self.assertEqualHLS(rgb_to_hls(-10, 100, 250),
                            [0.5962, 0.4706, 1.0833])

    def test_03_rgb_to_hls_overflow(self):
        self.assertEqualHLS(rgb_to_hls(10, 300, 250),
                            [0.4713, 0.6078, 1.4500])

    def assertEqualHLS(self, got, expected):
        self.assertEqual([round(x, 4) for x in got],
                         [round(x, 4) for x in expected])

from clevercss import hls_to_rgb

class HlsToRgbTestCase(TestCase):
    def test_01_hls_to_rgb(self):
        self.assertEqual(hls_to_rgb(0.6042, 0.5098, 0.9600),
                         (10, 100, 250))

    def test_02_hls_to_rgb_underflow(self):
        self.assertEqual(hls_to_rgb(0.5962, 0.4706, 1.0833),
                         (-10, 100, 250))

    def test_03_hls_to_rgb_overflow(self):
        self.assertEqual(hls_to_rgb(0.4713, 0.6078, 1.4500),
                         (10, 300, 250))

    def assertEqualHLS(self, got, expected):
        self.assertEqual([round(x, 4) for x in got],
                         [round(x, 4) for x in expected])

class HlsRgbFuzzyTestCase(TestCase):
    def test_01_hls_to_rgb_and_back_fuzzy(self):
        for i in xrange(100):
            self.do_fuzzy()

    def do_fuzzy(self):
        from random import seed, randint
        seed(0)
        rgb = tuple(randint(0, 255) for i in range(3))
        hls = rgb_to_hls(*rgb)
        hls2rgb = hls_to_rgb(*hls)
        self.assertEqual(rgb, hls2rgb)
        rgb2hls = rgb_to_hls(*hls2rgb)
        self.assertEqual(rgb2hls, hls)

from clevercss import convert

class ConvertTestCase(TestCase):
    def test_01_convert(self):
        self.assertEqual(convert('''body: 
            color: $color 
        ''',{'color':'#eee'}),
        u'body {\n  color: #eeeeee;\n}')
    
    def test_02_convert(self):
        self.assertEqual(convert('''body:
            background-color: $background_color
        ''', {'background_color': 'red.darken(10)'}),
        u'body {\n  background-color: #cc0000;\n}')
        
    def test_math(self):
        self.assertEqual(convert(dedent("""
        div:
            margin: -2px -2px
            padding: 2px + 2px
            top: 1px+1
            left: 5+5px
            right: 4px-5px
            bottom: 0 - 5px
        """)), dedent("""
        div {
          margin: -2px -2px;
          padding: 4px;
          top: 2px;
          left: 10px;
          right: -1px;
          bottom: -5px;
        }""").strip())

from clevercss import LineIterator

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
    

if __name__ == '__main__':
    main()
