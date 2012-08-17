#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2011-2012 Raphaël Barrois


import os
import re
from setuptools import setup

root_dir = os.path.abspath(os.path.dirname(__file__))


def get_version():
    version_re = re.compile(r"^__version__ = '([\w_.]+)'$")
    with open(os.path.join(root_dir, 'src', 'django_xworkflows', '__init__.py')) as f:
        for line in f:
            match = version_re.match(line[:-1])
            if match:
                return match.groups()[0]
    return '0.0.1'


setup(
    name="django-xworkflows",
    version=get_version(),
    author="Raphaël Barrois",
    author_email="raphael.barrois@polyconseil.fr",
    description=("A django app enabling Django models to use xworkflows."),
    license="BSD",
    keywords="django workflow state machine automaton",
    url="http://github.com/rbarrois/django_xworkflows",
    download_url="http://pypi.python.org/pypi/django-xworkflows/",
    package_dir={'': 'src'},
    packages=[
        'django_xworkflows',
        'django_xworkflows.xworkflow_log',
        'django_xworkflows.xworkflow_log.migrations',
        'django_xworkflows.management',
        'django_xworkflows.management.commands',
    ],
    install_requires=['xworkflows >=0.4.0', 'django >=1.3'],
    tests_require=['unittest2'],
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
