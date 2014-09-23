# -*- coding: utf-8 -*-
# Copyright (c) 2011-2013 Raphaël Barrois
# This code is distributed under the two-clause BSD license.

from __future__ import unicode_literals

"""Compatibility helpers."""


import django
import sys

is_python2 = (sys.version_info[0] == 2)

dj_major_minor = django.VERSION[:2]


# New in 1.4: timezone
if dj_major_minor >= (1, 4):
    from django.utils import timezone
    now = timezone.now
    del timezone
else:
    import datetime
    now = datetime.datetime.now
    del datetime


# New in 1.5: proper text
if dj_major_minor >= (1, 5):
    from django.utils.encoding import force_text
    from django.utils.encoding import python_2_unicode_compatible
else:
    from django.utils.encoding import force_unicode as force_text

    def python_2_unicode_compatible(c):
        if not hasattr(c, '__unicode__'):
            c.__unicode__ = c.__str__
        return c


# 1.7: Now migrating
if dj_major_minor >= (1, 7):
    from django.utils.deconstruct import deconstructible
else:
    def deconstructible(cls):
        return cls
