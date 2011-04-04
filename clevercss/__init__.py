#!/usr/bin/env python
"""
    CleverCSS
    ~~~~~~~~~

    The Pythonic way of CSS files.

    To convert this into a normal css file just call the `convert`
    function in the clevercss module. It's that easy :-)

    Example::

        base_padding = 2px
        background_color = #eee
        text_color = #111
        link_color = #ff0000

        body:
            font-family: serif, sans-serif, 'Verdana', 'Times New Roman'
            color: $text_color
            padding->
                top: $base_padding + 2
                right: $base_padding + 3
                left: $base_padding + 3
                bottom: $base_padding + 2
            background-color: $background_color

        div.foo:
            width: "Hello World".length() * 20px
            foo: (foo, bar, baz, 42).join('/')

        a:
            color: $link_color
            &:hover:
                color: $link_color.darken(30%)
            &:active:
                color: $link_color.brighten(10%)

        div.navigation:
            height: 1.2em
            padding: 0.2em
            ul:
                margin: 0
                padding: 0
                list-style: none
                li:
                    float: left
                    height: 1.2em
                    a:
                        display: block
                        height: 1em
                        padding: 0.1em
            foo: (1 2 3).string()

        __END__
        this is ignored, but __END__ as such is completely optional.

    To get the converted example module as css just run this file as script
    with the "--eigen-test" parameter.

    Literals
    --------

    CleverCSS supports most of the standard CSS literals.  Some syntax
    elements are not supported by now, some will probably never.

    Strings:
        everything (except of dangling method calls and whitespace) that
        cannot be parsed with a different rule is considered being a
        string.  If you want to have whitespace in your strings or use
        something as string that would otherwise have a different semantic
        you can use double or single quotes.

        these are all valid strings::

            =
            foo-bar-baz
            "blub"
            'foo bar baz'
            Verdana

    Numbers
        Numbers are just that.  Numbers with unit postfix are values.

    Values
        Values are numbers with an associated unit.  Most obvious difference
        between those two are the different semantics in arithmetic
        operations.  Some units can be converted, some are just not compatible
        (for example you won't be able to convert 1em in percent because
         there is no fixed conversion possible)
        Additionally to the CSS supported colors this module supports the
        netscape color codes.

    Colors
        Colors are so far only supported in hexadecimal notation.  You can
        also use the `rgb()` literal to some amount.  But that means you
        cannot use "orange" as color.

    URLs:
        URLs work like strings, the only difference is that the syntax looks
        like ``url(...)``.

    Variables:
        variables are quite simple.  Once they are defined in the root section
        you can use them in every expression::

            foo = 42px

            div:
                width: $foo * 100;

    Lists:
        Sometimes you want to assign more than one element to a CSS rule.  For
        example if you work with font families.  In that situation just use
        the comma operator to define a list::

            font-family: Verdana, Arial, sans-serif

        Additionally lists have methods, you can for example do this (although
        probably completely useless in real world cases)::

            width: (1, 2, 3, 4).length() * 20


    Implicit Concatenation
    ----------------------

    CleverCSS ignores whitespace.  But whitespace keeps the tokens apart.  If
    the parser now stumbles upon something it doesn't know how to handle, it
    assumes that there was a whitespace.  In some situations CSS even requires
    that behavior::

        padding: 2px 3px

    But because CleverCSS has expressions this could lead to this situation::

        padding: $x + 1 $x + 2

    This if course works too because ``$x + 1`` is one expression and
    ``$x + 2`` another one.  This however can lead to code that is harder to
    read.  In that situation it's recommended to parentize the expressions::

        padding: ($x + 1) ($x + 2)

    or remove the whitespace between the operators::

        padding: $x+1 $x+2


    Operators
    ---------

    ``+``       add two numbers, a number and a value or two compatible
                values (for example ``1cm + 12mm``).  This also works as
                concatenate operator for strings.  Using this operator
                on color objects allows some basic color composition.
    ``-``       subtract one number from another, a number from a value
                or a value from a compatible one.  Like the plus operator
                this also works on colors.
    ``*``       Multiply numbers, numbers with a value.  Multiplying strings
                repeats it. (eg: ``= * 5`` gives '=====')
    ``/``       divide one number or value by a number.
    ``%``       do a modulo division on a number or value by a number.

    Keep in mind that whitespace matters. For example ``20% 10`` is something
    completely different than ``20 % 10``. The first one is an implicit
    concatenation expression with the values 20% and 10, the second one a
    modulo epression.  The same applies to ``no-wrap`` versus ``no - wrap``
    and others.

    Additionally there are two operators used to keep list items apart. The
    comma (``,``) and semicolon (``;``) operator both keep list items apart.

    If you want to group expressions you can use parentheses.

    Methods
    -------

    Objects have some methods you can call:

    - `Number.abs()`            get the absolute value of the number
    - `Number.round(places)`    round to (default = 0) places
    - `Value.abs()`             get the absolute value for this value
    - `Value.round(places)`     round the value to (default = 0) places
    - `Color.brighten(amount)`  brighten the color by amount percent of
                                the current lightness, or by 0 - 100.
                                brighening by 100 will result in white.
    - `Color.darken(amount)`    darken the color by amount percent of the
                                current lightness, or by 0 - 100.
                                darkening by 100 will result in black.
    - `String.length()`         the length of the string.
    - `String.upper()`          uppercase version of the string.
    - `String.lower()`          lowercase version of the string.
    - `String.strip()`          version with leading an trailing whitespace
                                removed.
    - `String.split(delim)`     return a list of substrings, splitted by
                                whitespace or delim.
    - `String.eval()`           eval a css rule inside of a string. For
                                example a string "42" would return the
                                number 42 when parsed. But this can also
                                contain complex expressions such as
                                "(1 + 2) * 3px".
    - `String.string()`         just return the string itself.
    - `List.length()`           number of elements in a list.
    - `List.join(delim)`        join a list by space char or delim.

    Additionally all objects and expressions have a `.string()` method that
    converts the object into a string, and a `.type()` method that returns
    the type of the object as string.

    If you have implicit concatenated expressions you can convert them into
    a list using the `list` method::

        (1 2 3 4 5).list()

    does the same as::

        1, 2, 3, 4, 5

    Spritemaps
    ----------

    Commonly in CSS, you'll have an image of all your UI elements, and then use
    background positioning to extract a part of that image. CleverCSS helps you
    with this, via the `spritemap(fn)` call. For example::

        ui = spritemap('ui.sprites')
        some_button = $ui.sprite('some_button.png')
        other_button = $ui.sprite('other_button.png')

        div.some_button:
            background: $some_button

        div.other_button:
            background: $other_button
            width: $other_button.width()
            height: $other_button.height()

    :copyright: Copyright 2007 by Armin Ronacher, Georg Brandl.
    :license: BSD License
"""

import consts
import utils
import expressions
import engine

VERSION = '0.2.1.dev'

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
