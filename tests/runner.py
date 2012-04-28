#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2011-2012 Raphaël Barrois

import os
import sys

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
        ]
    )

from django.test import simple


def runtests(*test_args):
    if not test_args:
        test_args = ('djworkflows',)
    runner = simple.DjangoTestSuiteRunner(failfast=False)
    failures = runner.run_tests(test_args)
    sys.exit(failures)


if __name__ == '__main__':
    runtests(*sys.argv[1:])

