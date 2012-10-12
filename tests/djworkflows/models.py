# -*- coding: utf-8 -*-
# Copyright (c) 2011-2012 Raphaël Barrois

from django.db import models
import xworkflows

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

    implementation_class = dxmodels.TransactionalImplementationWrapper


class MyAltWorkflow(dxmodels.Workflow):
    states = (
        ('a', 'StateA'),
        ('b', 'StateB'),
        ('c', 'StateC'),
        ('something_very_long', u"A very long name"),
    )
    transitions = (
        ('tob', ('a', 'c'), 'b'),
        ('toa', ('b', 'c'), 'a'),
        ('toc', ('a', 'b'), 'c'),
    )
    initial_state = 'a'

    log_model = ''


class MyWorkflowEnabled(dxmodels.WorkflowEnabled, models.Model):
    OTHER_CHOICES = (
        ('aaa', u"AAA"),
        ('bbb', u"BBB"),
    )

    state = dxmodels.StateField(MyWorkflow)
    other = models.CharField(max_length=4, choices=OTHER_CHOICES)

    def fail_if_fortytwo(self, res, *args, **kwargs):
        if res == 42:
            raise ValueError()

    @dxmodels.transition(after=fail_if_fortytwo)
    def gobaz(self, foo, save=True):
        return foo * 2

    @xworkflows.on_enter_state(MyWorkflow.states.bar)
    def hook_enter_baz(self, *args, **kwargs):
        self.other = 'aaa'


class WithTwoWorkflows(dxmodels.WorkflowEnabled, models.Model):
    state1 = dxmodels.StateField(MyWorkflow())
    state2 = dxmodels.StateField(MyAltWorkflow())


class SomeWorkflowLastTransitionLog(dxmodels.BaseLastTransitionLog):
    MODIFIED_OBJECT_FIELD = 'obj'
    obj = models.OneToOneField('djworkflows.SomeWorkflowEnabled')


class SomeWorkflow(dxmodels.Workflow):
    states = (
        ('a', 'A'),
        ('b', 'B'),
    )
    transitions = (
        ('ab', 'a', 'b'),
        ('ba', 'b', 'a'),
    )
    initial_state = 'a'

    log_model_class = SomeWorkflowLastTransitionLog


class SomeWorkflowEnabled(dxmodels.WorkflowEnabled, models.Model):
    state = dxmodels.StateField(SomeWorkflow)


class GenericWorkflowLastTransitionLog(dxmodels.GenericLastTransitionLog):
    pass


class GenericWorkflow(dxmodels.Workflow):
    states = (
        ('a', 'A'),
        ('b', 'B'),
    )
    transitions = (
        ('ab', 'a', 'b'),
        ('ba', 'b', 'a'),
    )
    initial_state = 'a'

    log_model_class = GenericWorkflowLastTransitionLog


class GenericWorkflowEnabled(dxmodels.WorkflowEnabled, models.Model):
    state = dxmodels.StateField(GenericWorkflow)
