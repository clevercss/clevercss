
from clevercss import convert
print 'hi'

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

if __name__ == '__main__':
    main()
