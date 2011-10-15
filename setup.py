#!/usr/bin/env python
from setuptools import setup
import os
from sys import version_info

fp = open(os.path.join(os.path.dirname(__file__), "README.rst"))
readme_text = fp.read()
fp.close()

req_modules = ['cssutils']
if version_info[0] == 2 and version_info[1] < 7:
    req_modules.append('ordereddict')

setup(
    name='CleverCSS',
    author='Armin Ronacher',
    author_email='armin.ronacher@active-4.com',
    maintainer='David Ziegler',
    maintainer_email='david.ziegler@gmail.com',
    version='0.2.2.dev',
    url='http://sandbox.pocoo.org/clevercss/',
    download_url='https://github.com/guileen/clevercss3/tree',
    py_modules=['extract_sprites'],
    packages=['clevercss'],
    description='python inspired sass-like css preprocessor',
    long_description=readme_text,
    install_requires = req_modules,
    entry_points = {
        'console_scripts': ['ccss = clevercss.ccss:main']
    },
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Utilities'
    ],
    test_suite = 'tests.all_tests',
)
