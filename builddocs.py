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
    <div id="header">
      <h1>CleverCSS</h1>
      <h2>the pythonic way of webdesign</h2>
    </div>
    <div id="page">
      {{ body }}
    </div>
  </body>
</html>
'''

STYLE = u'''\
highlight_color = #B51F1F
header_color = white
header_background = #B51F1F

body:
  margin: 0
  padding: 1.5em 2.4em 2em 2.4em
  background-color: white
  color: black
  font->
    family: 'Georgia', serif

a:
  color: $highlight_color

p:
  text-align: justify
  line-height: 1.6em
  padding: 0.4em 0 0.4em 0
  margin: 0

li:
  line-height: 1.4em

h1, h2, h3:
  padding: 0
  margin: 0.8em 0 0 0
  a:
    color: black

h2:
  font-size: 1.8em

h3:
  font-size: 1.25em

pre:
  margin: 0
  padding: 0.8em 1.4em 0.8em 1.4em
  font->
    family: 'Bitstream Vera Sans Mono', 'Consolas', 'Monaco', monospace
    size: 0.85em


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
  max-width: 38em
  border-left: 2em solid $highlight_color
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
