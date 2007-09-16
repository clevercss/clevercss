#!/usr/bin/env python
import jinja
import clevercss
from docutils.core import publish_parts
from docutils.writers.html4css1 import Writer


TEMPLATE = u'''\
<!DOCTYPE HTML>
<html>
  <head>
    <title>CleverCSS Documentation</title>
    <style type="text/css">{{ css }}</style>
  </head>
  <body>
    <div id="wrapper">
      <div id="header">
        <h1>CleverCSS</h1>
        <h2>the pythonic way of webdesign</h2>
      </div>
      <div id="page">
        {{ body }}
      </div>
    </div>
  </body>
</html>
'''

STYLE = u'''\
background_color = #5EDFDF
highlight_color = #78AD1C
header_color = white
header_background = #A7E229
border_color = #348B8B
text_color = black

body:
  margin: 0
  padding: 2em 1em 2em 1em
  background-color: $background_color
  color: $text_color
  font->
    family: 'Georgia', serif

a:
  color: $highlight_color
  &:hover:
    color: $highlight_color.brighten(25)

p:
  text-align: justify
  line-height: 1.5em
  padding: 0.4em 0 0.4em 0
  margin: 0

li:
  line-height: 1.4em
  text-align: justify

h1, h2, h3:
  padding: 0
  margin: 0.8em 0 0 0
  a, a:hover:
    color: $text_color

h2:
  font-size: 1.8em

h3:
  font-size: 1.25em

pre:
  margin: 0
  padding: 0.8em 1.4em 0.8em 1.4em

tt, pre:
  font->
    family: 'Bitstream Vera Sans Mono', 'Consolas', 'Monaco', monospace
    size: 0.85em

#wrapper:
  width: 38em
  margin: 0 auto 0 auto
  border: 4px solid $border_color

#header:
  padding: 0.5em
  border-bottom: 0.15em solid $highlight_color
  background-color: $header_background

  h1, h2:
    font->
      family: 'Baskerville', 'Georgia', serif
      size: 2.5em
    padding: 0
    margin: 0
    color: $header_color

  h2:
    font-size: 1.5em

#page:
  padding: 0.8em 1.2em
  background: white
'''


def generate(source):
    parts = publish_parts(source,
        writer=Writer(),
        settings_overrides={
            'initial_header_level': 2
        }
    )
    return jinja.from_string(TEMPLATE).render(
        body=parts['body'],
        css=clevercss.convert(STYLE)
    )


def main():
    f = file('documentation.rst')
    try:
        dst = file('documentation.html', 'w')
        try:
            dst.write(generate(f.read().decode('utf-8')).encode('utf-8'))
        finally:
            dst.close()
    finally:
        f.close()


if __name__ == '__main__':
    main()
