# -*- coding: utf-8 -*-
# Copyright (c) 2011-2012 Raphaël Barrois

from django.core import exceptions
from django.core import serializers
from django.utils import unittest

import xworkflows
from django_xworkflows import models as xwf_models
from django_xworkflows.xworkflow_log import models as xwlog_models

from . import models


class ModelTestCase(unittest.TestCase):
    def test_workflow(self):
        self.assertEqual(models.MyWorkflow.states,
                         models.MyWorkflowEnabled._workflows['state'].states)

    def test_dual_workflows(self):
        self.assertIn('state1', models.WithTwoWorkflows._workflows)
        self.assertIn('state2', models.WithTwoWorkflows._workflows)

        self.assertEqual('Foo',
                models.WithTwoWorkflows._workflows['state1'].states['foo'].title)
        self.assertEqual('StateA',
                models.WithTwoWorkflows._workflows['state2'].states['a'].title)

    def test_instantiation(self):
        o = models.MyWorkflowEnabled()
        self.assertEqual(models.MyWorkflow.states['foo'], o.state)

    def test_class_attribute(self):
        self.assertEqual(models.MyWorkflow, models.MyWorkflowEnabled.state.__class__)

    def test_setting_state(self):
        o = models.MyWorkflowEnabled()
        self.assertEqual(models.MyWorkflow.states['foo'], o.state)

        o.state = models.MyWorkflow.states['bar']

        self.assertEqual(models.MyWorkflow.states['bar'], o.state)

    def test_setting_invalid_state(self):
        o = models.MyWorkflowEnabled()
        self.assertEqual(models.MyWorkflow.states['foo'], o.state)

        def set_invalid_state():
            o.state = models.MyAltWorkflow.states['a']

        self.assertRaises(exceptions.ValidationError, set_invalid_state)
        self.assertEqual(models.MyWorkflow.states['foo'], o.state)

    def test_queries(self):
        models.MyWorkflowEnabled.objects.all().delete()

        foo = models.MyWorkflow.states.foo
        bar = models.MyWorkflow.states.bar
        baz = models.MyWorkflow.states.baz

        models.MyWorkflowEnabled.objects.create(state=foo)
        models.MyWorkflowEnabled.objects.create(state=bar)

        self.assertEqual(1, len(models.MyWorkflowEnabled.objects.filter(state=foo)))
        self.assertEqual(1, len(models.MyWorkflowEnabled.objects.filter(state=bar)))
        self.assertEqual(0, len(models.MyWorkflowEnabled.objects.filter(state=baz)))

    def test_dumping(self):
        o = models.MyWorkflowEnabled()
        o.state = o.state.workflow.states.bar
        o.save()

        self.assertTrue(o.state.is_bar)

        data = serializers.serialize('json',
                models.MyWorkflowEnabled.objects.filter(pk=o.id))

        models.MyWorkflowEnabled.objects.all().delete()

        for obj in serializers.deserialize('json', data):
            obj.object.save()

        obj = models.MyWorkflowEnabled.objects.all()[0]
        self.assertTrue(obj.state.is_bar)

    def test_invalid_dump(self):
        data = '[{"pk": 1, "model": "djworkflows.myworkflowenabled", "fields": {"state": "blah"}}]'

        self.assertRaises(serializers.base.DeserializationError, list,
            serializers.deserialize('json', data))


class TransitionTestCase(unittest.TestCase):

    def setUp(self):
        self.obj = models.MyWorkflowEnabled()

    def test_transitions(self):
        self.assertEqual(models.MyWorkflow.states['foo'], self.obj.state)

        self.assertEqual(None, self.obj.foobar(save=False, log=False))

        self.assertTrue(self.obj.state.is_bar)

    def test_invalid_transition(self):
        self.assertTrue(self.obj.state.is_foo)

        self.assertRaises(xworkflows.InvalidTransitionError, self.obj.bazbar)

    def test_custom_transition_by_kw(self):
        self.assertEqual(models.MyWorkflow.states.foo, self.obj.state)
        self.obj.foobar()
        self.assertEqual('abab', self.obj.gobaz(foo='ab'))

    def test_custom_transition_no_kw(self):
        self.assertEqual(models.MyWorkflow.states.foo, self.obj.state)
        self.obj.foobar()
        self.assertEqual('abab', self.obj.gobaz('ab'))

    def test_logging(self):
        xwlog_models.TransitionLog.objects.all().delete()

        self.obj.save()
        self.obj.foobar(save=False)

        trlog = xwlog_models.TransitionLog.objects.all()[0]
        self.assertEqual(self.obj, trlog.modified_object)
        self.assertEqual('foobar', trlog.transition)
        self.assertEqual(None, trlog.user)

    def test_saving(self):
        self.obj.save()

        self.obj.foobar()

        obj = models.MyWorkflowEnabled.objects.get(pk=self.obj.id)

        self.assertTrue(obj.state.is_bar)
