# -*- coding: utf-8 -*-
__author__ = 'Christoph Burgmer'
"""
SuRF plugin

Support for librdf
"""
from setuptools import setup

setup(
    name='surf.librdf',
    version='1.0.0',
    description='surf librdf wrapper plugin',
    long_description = 'Allows the retrieval / persistence of surf resources from / to librdf supported persistent stores',
    license = 'New BSD SOFTWARE', 
    author="Christoph Burgmer",
    author_email="cburgmer at ira dot uka",
    url = 'http://code.google.com/p/surfrdf/',
    classifiers=[
      'Development Status :: 3 - Alpha',
      'Intended Audience :: Developers',
      'License :: OSI Approved :: BSD License',
      'Operating System :: OS Independent',
      'Programming Language :: Python :: 2.5',
    ],
    keywords = 'python SPARQL RDF resource mapper',
    #requires_python = '>=2.5', # Future in PEP 345
    packages=['surf_librdf'],
    install_requires=['SuRF>=1.0.0'],
    test_suite = "surf_librdf.test",
    entry_points={
    'surf.plugins.reader': 'librdf = surf_librdf.reader:ReaderPlugin',
    'surf.plugins.writer': 'librdf = surf_librdf.writer:WriterPlugin',
    }
)
