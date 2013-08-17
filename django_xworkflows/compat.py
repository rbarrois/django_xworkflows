# -*- coding: utf-8 -*-
# Copyright (c) 2011-2013 Raphaël Barrois
# This code is distributed under the two-clause BSD license.

from __future__ import unicode_literals

"""Compatibility helpers."""


import sys

is_python2 = (sys.version_info[0] == 2)

try:
    from django.utils import timezone
    now = timezone.now
    del timezone
except ImportError:
    import datetime
    now = datetime.datetime.now
    del datetime

try:
    from django.utils.encoding import force_text
except ImportError:
    from django.utils.encoding import force_unicode as force_text

try:
    from django.utils.encoding import python_2_unicode_compatible
except ImportError:
    def python_2_unicode_compatible(c):
        if not hasattr(c, '__unicode__'):
            c.__unicode__ = c.__str__
        return c
