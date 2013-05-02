#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2011-2013 Raphaël Barrois
# This code is distributed under the two-clause BSD license.


import os
import re
from distutils.core import setup
from distutils import cmd

root = os.path.abspath(os.path.dirname(__file__))


def get_version(*module_dir_components):
    version_re = re.compile(r"^__version__ = ['\"](.*)['\"]$")
    module_root = os.path.join(root, *module_dir_components)
    module_init = os.path.join(module_root, '__init__.py')
    with open(module_init, 'r') as f:
        for line in f:
            match = version_re.match(line[:-1])
            if match:
                return match.groups()[0]
    return '0.1.0'

VERSION = get_version('django_xworkflows')


class test(cmd.Command):
    """Run the tests for this package."""
    command_name = 'test'
    description = 'run the tests associated with the package'

    user_options = [
        ('test-suite=', None, "A test suite to run (defaults to 'tests')"),
    ]

    def initialize_options(self):
        self.test_runner = None
        self.test_suite = None

    def finalize_options(self):
        self.ensure_string('test_suite', 'tests.runner.runtests')

    def run(self):
        """Run the test suite."""
        try:
            import unittest2 as unittest
        except ImportError:
            import unittest

        if self.verbose:
            verbosity=1
        else:
            verbosity=0

        loader = unittest.TestLoader()
        suite = unittest.TestSuite()

        if self.test_suite == 'tests':
            for test_module in loader.discover('.'):
                suite.addTest(test_module)
        else:
            suite.addTest(loader.loadTestsFromName(self.test_suite))

        result = unittest.TextTestRunner(verbosity=verbosity).run(suite)
        if not result.wasSuccessful():
            sys.exit(1)


setup(
    name="django-xworkflows",
    version=VERSION,
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
    requires=['xworkflows(>=0.4.0)', 'django(>=1.3)'],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Topic :: Software Development :: Libraries :: Python Modules",
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],
    cmdclass={'test': test},
)
