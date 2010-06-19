=========
CleverCSS
=========

CleverCSS is a small markup language for CSS inspired by Python that can be used
to build a style sheet in a clean and structured way.  In many ways it's cleaner
and more powerful than CSS2 is.

The most obvious difference to CSS is the syntax: it is indentation based and
not flat.  While this is obviously against the Python Zen, it's nonetheless a
good idea for structural styles.


New Syntax Additions
====================

Imports
----------
`(commit) <http://github.com/jabapyth/clevercss/commit/04536763f98bf5285194595a39e21c41d7c63b1a>`_

This works like normal css @imports, but expects a ccss file, which is then
parsed, allowing cross-sheet variables

Backstrings (literal CSS)
-------------------------------
`(commit) <http://github.com/WorldMaker/clevercss/commit/66b86c61454daae57a504185df359437c4883ae8>`_

Sometimes CleverCSS is a bit too clever for its own good and you just
want to pass something directly to CSS. For instance, functions that
aren't rgb() or url() need to be escaped. Added is a simple new
backtick-surrounded string format that will be passed verbatim without
further processing. Example::

  .gradient:
      background: `-moz-linear-gradient(...)`

Spritemaps
------------
`(commit) <http://github.com/jabapyth/clevercss/commit/f5a98c9b29d57b6543cc2cc87728061148c13588>`_

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
at the following documentation of CleverCSS for more details.
