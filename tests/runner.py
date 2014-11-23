#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2011-2013 Raphaël Barrois
# This code is distributed under the two-clause BSD license.

from __future__ import unicode_literals

import os
import sys

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
            }
        },
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'tests.djworkflows',
            'django_xworkflows',
            'django_xworkflows.xworkflow_log',
        ],
        MIDDLEWARE_CLASSES=[],
    )

if django.VERSION[:2] >= (1, 7):
    django.setup()

from django.test import simple


def runtests(*test_args):
    if not test_args:
        test_args = ('djworkflows',)
    runner = simple.DjangoTestSuiteRunner(failfast=False)
    failures = runner.run_tests(test_args)
    sys.exit(failures)


if __name__ == '__main__':
    runtests(*sys.argv[1:])

