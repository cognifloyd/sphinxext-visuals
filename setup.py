# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

long_desc = '''
This package contains the visuals Sphinx extension.

.. add description here ..
'''

requires = ['Sphinx>=1.3']

setup(
    name='sphinxext-visuals',
    version='0.1',
    url='http://github.com/cognifloyd/sphinxext-visuals',
    download_url='http://pypi.python.org/pypi/sphinxext-visuals',
    license='BSD',
    author='Jacob Floyd',
    author_email='cognifloyd@gmail.com',
    description='Sphinx "visuals" extension',
    long_description=long_desc,
    zip_safe=False,
    classifiers=[
        'Development Status :: 1 - Planning',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Sphinx :: Extension',
        #'Framework :: Sphinx :: Theme',
        'Topic :: Documentation',
        'Topic :: Utilities',
    ],
    platforms='any',
    packages=find_packages(),
    include_package_data=True,
    install_requires=requires,
    namespace_packages=['visuals'],
)
