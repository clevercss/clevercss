=======================
CleverCSS Documentation
=======================

CleverCSS is a small markup language for CSS inspired by Python that can be used
to build a style sheet in a clean and structured way.  In many ways it's cleaner
and more powerful than CSS2 is.

The most obvious difference to CSS is the syntax: it is indentation based and
not flat.  While this is obviously against the Python Zen, it's nonetheless a
good idea for structural styles.


Nutshell
========

To get an idea of how CleverCSS works you can see a small example below.  Note
the indentation based syntax and how you can nest rules::

    ul#comments, ol#comments:
      margin: 0
      padding: 0

      li:
        padding: 0.4em
        margin: 0.8em 0 0.8em

        h3:
          font-size: 1.2em
        p:
          padding: 0.3em
        p.meta:
          text-align: right
          color: #ddd

Of course you can do the very same in CSS, but because of its flat nature the
code would look more verbose.  The following piece of code is the CleverCSS
output of the above file::

    ul#comments,
    ol#comments {
      margin: 0;
      padding: 0;
    }

    ul#comments li,
    ol#comments li {
      padding: 0.4em;
      margin: 0.8em 0 0.8em;
    }

    ul#comments li h3,
    ol#comments li h3 {
      font-size: 1.2em;
    }

    ul#comments li p,
    ol#comments li p {
      padding: 0.3em;
    }

    ul#comments li p.meta,
    ol#comments li p.meta {
      text-align: right;
      color: #dddddd;
    }

But that's only a small example of what you can do with CleverCSS.  Have a look
at the following introduction to CleverCSS.


Syntax and Semantics
====================

On the one hand you can easily convert an ordinary CSS file into a CleverCSS one
by indenting it correctly and removing braces.  On the other hand you have some
small syntactic and semantic differences that result from having inline
expressions in rules.


Literals
--------

CleverCSS allows you to use a limited amount of expressions in the attributes.
That means it has some limited understanding of the values it is dealing with.
To keep things simple, CleverCSS does not implement all the rules defined in the
recent CSS version, but most of the data types are supported:

**Numbers**
    Numbers one of the simplest types.  ``0``, ``-23```, ``42.23`` are all valid
    examples.  Note that ``23px`` is not a number.  We refer to this as a value.

**Values**
    Numbers with a unit suffix are called values.  They behave different when
    used in arithmetic expressions.

**Colors**
    Colors are either defined in hexadecimal format, using the ``rgb(...)``
    literal or with one of the 140 color names CleverCSS supports (and happen to
    be identical to the common Netscape color names).  Colors are not
    automatically converted into their hexadecimal color code, see the note on
    type conversions below.

**Lists**
    Some attributes in CSS support multiple values.  For example `font-family`
    accepts multiple font faces.  You can use commas or semicolons to create
    lists, note that it's so far not possible to create lists for one element!

**Variables**
    Variables are short names prefixed with a dollar sign.

**Strings**
    Strings are basically everything that is not handled otherwise.  If you want
    to enforce a value to be a string you can quote it.  These are all examples
    of valid strings::

        foo
        "foo and bar"
        =

    Especially the last one might surprise you.


Rules and Selectors
-------------------

The syntax for selectors is the same as for CSS, but instead of using braces to
group the attributes that belong to a particular selector, CleverCSS uses
indentation.  It's important not to forget the trailing colon that indicates a
block::

    list, of, selectors:
      list
      of
      attributes
      ...

Additionally you can nest rules in a block so that you don't have to write the
selectors a second time::

    #main:
      p:
        ...

Does exactly the same as::

    #main p:
      ...


Parent References
-----------------

Per default, nested rulesets are joined with a whitespace, the normal CSS rule
separator.  Sometimes you want to use a greater than sign or any other rule
separator.  You can do so by using the ampersand sign::

    body:
      & > div.header:
        padding: 3px

Basically the nested rule is moved one layer up and the ampersand is replaced
with the parent rule::

    body > div.header {
      padding: 3px;
    }

You can also use this to add pseudo-classes to links::

    a:
      &:hover:
        color: red
      &:visited:
        color: blue

This would output a CSS like this::

    a:hover {
      color: red;
    }

    a:visited {
      color: blue;
    }

**Note:** multiple occurrences of the ampersand symbol are replaced!


Attributes
----------

Attributes work exactly like in CSS, except of not being ended by semicolons.
Additionally CleverCSS has a group operator (``->``) that allows grouping
attributes with the same, dash delimited prefix. Example::

    #main p
      font->
        family: Verdana, sans-serif
        size: 1.1em
        style: italic

This code will generate the following CSS::

    #main p {
        font-family: Verdana, sans-serif;
        font-size: 1.1em;
        font-style: italic;
    }


Constants
---------

CleverCSS allows you to define stylesheet-wide constants from both within your
stylesheet, and the Python code if executed from a custom script.  But constants
defined in the stylesheet will always override constants supplied from the
python code.

You can define constants at top level using the equals sign, and use them in
attributes by prefixing it with a dollar sign::

    background_color = #ccc

    #main:
      background-color: $background_color

One important thing is that constants don't work like Python variables.  When a
constant is assigned, CleverCSS will not evaluate it but store the expression.
Thus you can reference variables in a variable definition that don't exist
"yet"::

    foo = $bar
    bar = 42

If you somehow manage to create circular references (foo points to bar, which
points back to foo), CleverCSS will give you a error message that points to the
problematic variable.


Implicit Concatenation
----------------------

If you have multiple expressions next to each other, delimited by nothing more
than a whitespace character, you have created an implicitly concatenated
expression. That means that once it's evaluated and converted to CSS, it will be
delimited by a space character::

    padding: $foo + 2 + 3 $foo - 2

Will result in (assuming $foo is 10)::

    padding: 15 8;

Concatenated expressions have a lower priority than lists, so this works too::

    font-family: Verdana, Times New Roman, sans-serif

Which will result in the very same, just with a semicolon at the end.


Arithmetic
----------

CleverCSS has a limited understanding of the values it is dealing with.  That
allows it to perform some mathematical operations on it.  CleverCSS recognizes
the following operators: ``+``, ``-``, ``*``, ``/`` and ``%``.  Additionally you
can use parentheses to group and override the default operator priorities.

If all your operands are numbers the return value will be a number too, for all
for those operators.  If you want to calculate with numbers and values the
return value will be a value.  Calculating with only values is possible too but
in that situation the units must be either the same or convertible.  Keep in
mind that ``1cm * 1cm`` would result in ``1qcm`` which is not a unit CSS
provides and thus invalid.

If you're dealing with strings, you can use the plus operator to concatenate
multiple strings.  You can also multiply strings with numbers, see the examples
below::

    // calculations with numbers / values
    42px + 2                    -> 44px
    10px * 2                    -> 20px
    1cm + 1mm                   -> 11mm
    (1 + 2) * 3                 -> 9

    // string concatenation
    foo + bar                   -> foobar
    "blub blah" + "baz"         -> 'blub blahbaz'

You can also calculate with numbers::

    #fff - #ccc                 -> #333333
    cornflowerblue - coral      -> #00169d

You can also add or subtract a number from it and it will do so for all three
channels (red, green, blue)::

    crimson - 20                -> #c80028


Methods
-------

All objects have methods you can call, depending on their type.  To call a
method on an object you just use a dot, the name of the method and parentheses
around arguments.  Also keep in mind that without the parentheses it's just a
string::

    foo.bar()           // calls bar on foo without arguments
    foo.bar.baz()       // calls baz on "foo.bar" without arguments
    blub.blah(1, 2)     // calls blah on blub with two arguments 1 and 2

The following methods exists on the objects:

- `Number.abs()`, get the absolute value of the number
- `Number.round(places)`, round to (default = 0) places
- `Value.abs()`, get the absolute value for this value
- `Value.round(places)`, round the value to (default = 0) places
- `Color.brighten(amount)`, brighten the color by amount percent of the current
  lightness, or by 0 - 100.  Brightening by 100 percent will result in white.
- `Color.darken(amount)`, darken the color by amount percent of the current
  lightness, or by 0 - 100.  Darkening by 100 percent will result in black.
- `String.length()`, the length of the string.
- `String.upper()`, uppercase version of the string.
- `String.lower()`, lowercase version of the string.
- `String.strip()`, version with leading an trailing whitespace removed.
- `String.split(delim)`, return a list of substrings, split at whitespace or
  delim.
- `String.eval()`, eval a CSS rule inside of a string. For example a string "42"
  would return the number 42 when parsed. But this can also contain complex
  expressions such as ``(1 + 2) * 3px``.
- `String.string()`, just return the string itself.
- `List.length()`, number of elements in a list.
- `List.join(delim)`, join a list by space char or delim.

Additionally all objects and expressions have a `.string()` method that converts
the object into a string, and a `.type()` method that returns the type of the
object as string.

If you have implicitly concatenated expressions you can convert them into a list
using the `list` method::

    (1 2 3 4 5).list()

does the same as::

    1, 2, 3, 4, 5


Note on Colors
--------------

Colors in CleverCSS are special.  Because CleverCSS recognizes over 100 color
names, false positives are very likely.  But most of the time you wouldn't notice
that because colors are not converted into their hexadecimal equivalent if not
forced (by adding a second number that alters the value).  A second way to
convert a number to the hexadecimal representation is calling the `hex()`
method::

    lavenderblush.hex()         -> #fff0f5

The whole thing works differently for colors defined using the `rgb()` literal.
Those are converted to hexadecimal representation right away::

    rgb(255, 255, 255)          -> #ffffff


Library Usage
=============

If you want to use CleverCSS in your application, the following few steps help
you getting started quickly.


Installing CleverCSS
--------------------

If you have the `easy_install`_ utility installed, you can install CleverCSS
with the following command::

    sudo easy_install CleverCSS

(if you are on a Windows box, omit the sudo and make sure you are executing the
command as system administrator)

If you don't have `easy_install`, you can download the most recent version of
CleverCSS from the `cheeseshop`_.


Using The Library
-----------------

Using CleverCSS is straightforward.  If you want to use it from within Python,
you can just import `clevercss` and call the `convert()` function with the
clevercss source code.  If you want to provide defaults for variables you can
pass it a dict of strings with valid CleverCSS expressions.

Here a small example::

    import clevercss
    print clevercss.convert('''
    body:
      background-color: $background_color
    ''', {'background_color: 'red.darken(10)'})

If you want to use it from the shell, you can use the `clevercss.py` script.
For usage help use this command::

    clevercss.py --help


.. _easy_install: http://peak.telecommunity.com/dist/ez_setup.py
.. _cheeseshop: http://pypi.python.org/pypi/CleverCSS/
