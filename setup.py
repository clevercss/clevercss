"""\
=========
CleverCSS
=========

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
at the following documentation of CleverCSS for more details.
"""
from setuptools import setup
setup(
    name='CleverCSS',
    author='Armin Ronacher',
    author_email='armin.ronacher@active-4.com',
    maintainer='David Ziegler',
    maintainer_email='david.ziegler@gmail.com',
    version='0.1.4',
    url='http://sandbox.pocoo.org/clevercss/',
    download_url='http://github.com/dziegler/clevercss/tree',
    py_modules=['clevercss'],
    description='funky css preprocessor dammit',
    long_description=__doc__,
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python'
    ],
    entry_points = {
        'console_scripts':[
            'clevercss = clevercss:main'
        ]
    },
    
)
