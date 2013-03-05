#!/usr/bin/env python
"""
    CleverCSS
    ~~~~~~~~~

    The Pythonic way of CSS files.

    To convert a CleverCSS file into a normal css file just call the `convert`
    function in the clevercss module. It's that easy :-)
    """

from clevercss import consts
from clevercss import utils
from clevercss import expressions
from clevercss import engine

VERSION = '0.2.2.dev'

class Context(dict):
    def __init__(self, *args, **kwargs):
        if args == (None,):
            args = ()
        super(Context, self).__init__(*args, **kwargs)

def convert(source, context=None, fname=None, minified=False):
    """Convert CleverCSS text into normal CSS."""
    context = Context(context)
    context.minified = minified
    return engine.Engine(source, fname=fname).to_css(context)

__all__ = ['convert', 'VERSION', '__doc__']

# vim: et sw=4 sts=4
