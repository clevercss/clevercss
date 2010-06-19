from setuptools import setup
import os

f = open("README.rst")
try:
    try:
        readme_text = f.read()
    except:
        readme_text = ""
finally:
    f.close()

setup(
    name='CleverCSS',
    author='Armin Ronacher',
    author_email='armin.ronacher@active-4.com',
    maintainer='David Ziegler',
    maintainer_email='david.ziegler@gmail.com',
    version='0.2',
    url='http://sandbox.pocoo.org/clevercss/',
    download_url='http://github.com/dziegler/clevercss/tree',
    py_modules=['clevercss'],
    description='python inspired sass-like css preprocessor',
    long_description=readme_text,
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python'
    ],
    test_suite = 'tests.all_tests',
)
