import os

f = open("README.rst")
try:
    try:
        readme_text = f.read()
    except:
        readme_text = ""
finally:
    f.close()

from distutils.core import setup

setup(
    name='CleverCSS',
    author='Armin Ronacher',
    author_email='armin.ronacher@active-4.com',
    version='0.1',
    url='http://sandbox.pocoo.org/clevercss/',
    py_modules=['clevercss'],
    description='funky css preprocessor dammit',
    long_description=readme_text,
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python']
)
