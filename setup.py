#!/usr/bin/env python
import os
from distutils.core import setup

def find_packages(root):
    # so we don't depend on setuptools; from the Storm ORM setup.py
    packages = []
    for directory, subdirectories, files in os.walk(root):
        if '__init__.py' in files:
            packages.append(directory.replace(os.sep, '.'))
    return packages


setup(
    name = 'CleverCSS',
    author = 'Armin Ronacher',
    maintainer = 'David Ziegler',
    version='0.2.dev',
    description='python inspired sass-like css preprocessor',
    license = 'BSD',
    url = 'https://github.com/isolationism/clevercss',
    py_modules=['clevercss'],
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python'
    ],
    test_suite = 'tests.all_tests',
    download_url='http://github.com/isolationism/clevercss/tree',
    packages = find_packages('clevercss'),
)

