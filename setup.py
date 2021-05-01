#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2011-2020 Raphaël Barrois
# This code is distributed under the two-clause BSD license.


import subprocess

from setuptools import setup
from setuptools.command import build_py


class BuildWithMakefile(build_py.build_py):
    """Custom 'build' command that runs 'make build' first."""
    def run(self):
        subprocess.check_call(['make', 'build'])
        return super().run()


setup(
    cmdclass=dict(
        build_py=BuildWithMakefile,
    ),
)
