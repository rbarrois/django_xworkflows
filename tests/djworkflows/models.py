# -*- coding: utf-8 -*-
# Copyright (c) 2011-2012 Raphaël Barrois

from django.db import models as djmodels

from django_xworkflows import models

class MyWorkflow(models.Workflow):
    states = ('foo', 'bar', 'baz')
    transitions = (
        ('foobar', 'foo', 'bar'),
        ('gobaz', ('foo', 'bar'), 'baz'),
        ('bazbar', 'baz', 'bar'),
    )
    initial_state = 'foo'


class MyAltWorkflow(models.Workflow):
    states = (
        ('a', 'StateA'),
        ('b', 'StateB'),
        ('c', 'StateC'),
    )
    transitions = (
        ('tob', ('a', 'c'), 'b'),
        ('toa', ('b', 'c'), 'a'),
        ('toc', ('a', 'b'), 'c'),
    )
    initial_state = 'a'


class MyWorkflowEnabled(models.WorkflowEnabled, djmodels.Model):
    state = MyWorkflow

    def gobaz(self, foo):
        return foo * 2


class WithTwoWorkflows(models.WorkflowEnabled, djmodels.Model):
    state1 = MyWorkflow()
    state2 = MyAltWorkflow()
