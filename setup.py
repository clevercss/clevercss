import os
from distutils.core import setup

fp = open(os.path.join(os.path.dirname(__file__), "README.rst"))
readme_text = fp.read()
fp.close()

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
