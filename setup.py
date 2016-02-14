#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2011-2013 Raphaël Barrois
# This code is distributed under the two-clause BSD license.


import os
import re
import sys

from setuptools import setup

root_dir = os.path.abspath(os.path.dirname(__file__))


def get_version(package_name):
    version_re = re.compile(r"^__version__ = [\"']([\w_.-]+)[\"']$")
    package_components = package_name.split('.')
    path_components = package_components + ['__init__.py']
    with open(os.path.join(root_dir, *path_components)) as f:
        for line in f:
            match = version_re.match(line[:-1])
            if match:
                return match.groups()[0]
    return '0.1.0'


def parse_requirements(requirements_file):
    with open(requirements_file, 'r') as f:
        return [line for line in f if line.strip() and not line.startswith('#')]


if sys.version_info[0:2] < (2, 7):
    extra_tests_require = ['unittest2']
else:
    extra_tests_require = []


PACKAGE = 'django_xworkflows'
REQUIREMENTS_PATH = 'requirements.txt'


setup(
    name="django-xworkflows",
    version=get_version(PACKAGE),
    author="Raphaël Barrois",
    author_email="raphael.barrois+xworkflows@polytechnique.org",
    description=("A django app enabling Django models to use xworkflows."),
    license="BSD",
    keywords="django workflow state machine automaton",
    url="http://github.com/rbarrois/django_xworkflows",
    download_url="http://pypi.python.org/pypi/django-xworkflows/",
    packages=[
        'django_xworkflows',
        'django_xworkflows.xworkflow_log',
        'django_xworkflows.xworkflow_log.migrations',
        'django_xworkflows.management',
        'django_xworkflows.management.commands',
    ],
    setup_requires=[
        'setuptools>=0.8',
    ],
    install_requires=parse_requirements(REQUIREMENTS_PATH),
    tests_require=[] + extra_tests_require,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Topic :: Software Development :: Libraries :: Python Modules",
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests.runner.runtests',
    zip_safe=False,  # Prevent distribution as eggs for South.
)
