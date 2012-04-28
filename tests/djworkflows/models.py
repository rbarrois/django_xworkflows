# -*- coding: utf-8 -*-
# Copyright (c) 2011-2012 Raphaël Barrois

from django.db import models

from django_xworkflows import models as dxmodels

class MyWorkflow(dxmodels.Workflow):
    states = (
        ('foo', u"Foo"),
        ('bar', u"Bar"),
        ('baz', u"Baz"),
    )
    transitions = (
        ('foobar', 'foo', 'bar'),
        ('gobaz', ('foo', 'bar'), 'baz'),
        ('bazbar', 'baz', 'bar'),
    )
    initial_state = 'foo'


class MyAltWorkflow(dxmodels.Workflow):
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


class MyWorkflowEnabled(dxmodels.WorkflowEnabled, models.Model):
    state = dxmodels.StateField(MyWorkflow)

    @dxmodels.transition()
    def gobaz(self, foo):
        return foo * 2


class WithTwoWorkflows(dxmodels.WorkflowEnabled, models.Model):
    state1 = dxmodels.StateField(MyWorkflow())
    state2 = dxmodels.StateField(MyAltWorkflow())
