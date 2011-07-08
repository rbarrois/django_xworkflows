#!/usr/bin/env python
# coding: utf-8

import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
        name = "django-xworkflows",
        version = "0.1",
        author = "Raphaël Barrois",
        author_email = "raphael.barrois@polyconseil.fr",
        description = ("A django app enabling Django models to use xworkflows."),
        license = "BSD",
        keywords = "django workflow state machine automaton",
        url = "http://packages.python.org/django-xworkflows",
        package_dir = {'': 'src'},
        packages = ['django_xworkflows'],
        long_description=read('README.rst'),
        install_requires = ['xworkflows', 'django >=1.3'],
        tests_require = ['unittest2'],
        classifiers=[
            "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Topic :: Software Development :: Libraries :: Python Modules",
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    test_suite='tests.runner.runtests',
)
