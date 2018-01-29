#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2011-2013 Raphaël Barrois
# This code is distributed under the two-clause BSD license.


import codecs
import os
import re
import subprocess
import sys

from setuptools import setup, find_packages
from setuptools.command import build_py

root_dir = os.path.abspath(os.path.dirname(__file__))


def get_version(package_name):
    version_re = re.compile(r"^__version__ = [\"']([\w_.-]+)[\"']$")
    package_components = package_name.split('.')
    init_path = os.path.join(root_dir, *(package_components + ['__init__.py']))
    with codecs.open(init_path, 'r', 'utf-8') as f:
        for line in f:
            match = version_re.match(line[:-1])
            if match:
                return match.groups()[0]
    return '0.1.0'


def clean_readme(fname):
    """Cleanup README.rst for proper PyPI formatting."""
    with codecs.open(fname, 'r', 'utf-8') as f:
        return ''.join(
            re.sub(r':\w+:`([^`]+?)( <[^<>]+>)?`', r'``\1``', line)
            for line in f
            if not (line.startswith('.. currentmodule') or line.startswith('.. toctree'))
        )


class BuildWithMakefile(build_py.build_py):
    """Custom 'build' command that runs 'make build' first."""
    def run(self):
        subprocess.check_call(['make', 'build'])
        if sys.version_info[0] < 3:
            # Under Python 2.x, build_py is an old-style class.
            return build_py.build_py.run(self)
        return super().run()


PACKAGE = 'django_xworkflows'


setup(
    name=PACKAGE,
    version=get_version(PACKAGE),
    author="Raphaël Barrois",
    author_email="raphael.barrois+%s@polytechnique.org" % PACKAGE,
    description="A django app enabling Django models to use xworkflows.",
    long_description=clean_readme('README.rst'),
    license="BSD",
    keywords="django workflow state machine automaton",
    url="http://github.com/rbarrois/django_xworkflows",
    download_url="http://pypi.python.org/pypi/django-xworkflows/",
    packages=find_packages(exclude=['dev', 'tests*']),
    cmdclass={'build_py': BuildWithMakefile},
    include_package_data=True,
    setup_requires=[
        'setuptools>=0.8',
    ],
    install_requires=[
        'Django>=1.11',
        'xworkflows',
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
    ],
    test_suite='tests.runner.runtests',
    zip_safe=False,  # Prevent distribution as eggs for South.
)
