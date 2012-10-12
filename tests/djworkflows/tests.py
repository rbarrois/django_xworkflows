# -*- coding: utf-8 -*-
# Copyright (c) 2011-2012 Raphaël Barrois

from django import VERSION as django_version
from django.core import exceptions
from django.core import serializers
from django.db import models as django_models
from django import test
from django.utils import unittest

import xworkflows

from django_xworkflows import models as xwf_models
from django_xworkflows.xworkflow_log import models as xwlog_models

try:
    import south
    import south.creator.freezer
    import south.modelsinspector
except ImportError:
    south = None

from . import models


class ModelTestCase(test.TestCase):
    def test_workflow(self):
        self.assertEqual(models.MyWorkflow.states,
                         models.MyWorkflowEnabled._workflows['state'].workflow.states)

    def test_field_attributes(self):
        field_def = models.MyWorkflowEnabled._meta.get_field_by_name('state')[0]
        self.assertEqual(16, field_def.max_length)
        self.assertFalse(field_def.blank)
        self.assertFalse(field_def.null)
        self.assertEqual(models.MyWorkflow.initial_state.name, field_def.default)
        self.assertEqual(
            list((st.name, st.title) for st in models.MyWorkflow.states),
            field_def.choices,
        )

    def test_ald_field_attributes(self):
        field_def = models.WithTwoWorkflows._meta.get_field_by_name('state2')[0]
        self.assertEqual(19, field_def.max_length)
        self.assertFalse(field_def.blank)
        self.assertFalse(field_def.null)
        self.assertEqual(models.MyAltWorkflow.initial_state.name, field_def.default)
        self.assertEqual(
            list((st.name, st.title) for st in models.MyAltWorkflow.states),
            field_def.choices,
        )

    def test_dual_workflows(self):
        self.assertIn('state1', models.WithTwoWorkflows._workflows)
        self.assertIn('state2', models.WithTwoWorkflows._workflows)

        self.assertEqual('Foo',
                models.WithTwoWorkflows._workflows['state1'].workflow.states['foo'].title)
        self.assertEqual('StateA',
                models.WithTwoWorkflows._workflows['state2'].workflow.states['a'].title)

    def test_instantiation(self):
        o = models.MyWorkflowEnabled()
        self.assertEqual(models.MyWorkflow.states['foo'], o.state)

    def test_instantiation_from_empty(self):
        o = models.MyWorkflowEnabled(state=None)
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

    def test_display(self):
        o = models.MyWorkflowEnabled(other='aaa')
        self.assertEqual(u"Foo", o.get_state_display())
        self.assertEqual(u"AAA", o.get_other_display())

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

        if django_version[:3] >= (1, 4, 0):
            error_class = serializers.base.DeserializationError
        else:
            error_class = exceptions.ValidationError

        self.assertRaises(error_class, list,
            serializers.deserialize('json', data))


class InheritanceTestCase(test.TestCase):
    """Tests inheritance-related behaviour."""
    def test_simple(self):
        class BaseWorkflowEnabled(xwf_models.WorkflowEnabled, django_models.Model):
            state = xwf_models.StateField(models.MyWorkflow)

        class SubWorkflowEnabled(BaseWorkflowEnabled):
            pass

        obj = SubWorkflowEnabled()
        self.assertEqual(models.MyWorkflow.initial_state, obj.state)

    def test_abstract(self):
        class AbstractWorkflowEnabled(xwf_models.WorkflowEnabled, django_models.Model):
            state = xwf_models.StateField(models.MyWorkflow)
            class Meta:
                abstract = True

        class ConcreteWorkflowEnabled(AbstractWorkflowEnabled):
            pass

        obj = ConcreteWorkflowEnabled()
        self.assertEqual(models.MyWorkflow.initial_state, obj.state)


# Not a standard TestCase, since we're testing transactions.
class TransitionTestCase(test.TransactionTestCase):

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

    def test_hook(self):
        self.assertEqual(models.MyWorkflow.states.foo, self.obj.state)
        self.assertEqual('', self.obj.other)
        self.obj.foobar()
        self.assertEqual('aaa', self.obj.other)

    def test_logging(self):
        xwlog_models.TransitionLog.objects.all().delete()

        self.obj.save()
        self.obj.foobar(save=False)

        trlog = xwlog_models.TransitionLog.objects.all()[0]
        self.assertEqual(self.obj, trlog.modified_object)
        self.assertEqual('foobar', trlog.transition)
        self.assertEqual(None, trlog.user)
        self.assertEqual('foo', trlog.from_state)
        self.assertEqual('bar', trlog.to_state)

        self.assertIn('foo -> bar', unicode(trlog))

    def test_no_logging(self):
        """Tests disabled transition logs."""
        xwlog_models.TransitionLog.objects.all().delete()

        obj = models.WithTwoWorkflows()
        obj.save()

        # No log model on MyAltWorkflow
        obj.tob()
        self.assertFalse(xwlog_models.TransitionLog.objects.exists())

        # Log model provided for MyWorkflow
        obj.foobar()
        self.assertTrue(xwlog_models.TransitionLog.objects.exists())

    def test_saving(self):
        self.obj.save()

        self.obj.foobar()

        obj = models.MyWorkflowEnabled.objects.get(pk=self.obj.id)

        self.assertEqual(models.MyWorkflow.states.bar, obj.state)

    def test_no_saving(self):
        self.obj.save()
        self.assertEqual(84, self.obj.gobaz(42, save=False))

        obj = models.MyWorkflowEnabled.objects.get(pk=self.obj.id)
        self.assertEqual(models.MyWorkflow.states.foo, obj.state)

    def test_transactions(self):
        self.obj.save()

        self.assertRaises(ValueError, self.obj.gobaz, 21)

        obj = models.MyWorkflowEnabled.objects.get(pk=self.obj.id)

        self.assertEqual(models.MyWorkflow.states.foo, obj.state)


class LastTransitionLogTestCase(test.TestCase):
    def setUp(self):
        self.obj = models.SomeWorkflowEnabled.objects.create()

    def test_transitions(self):
        self.assertEqual(0, models.SomeWorkflowLastTransitionLog.objects.count())

        self.obj.ab()
        self.assertEqual(1, models.SomeWorkflowLastTransitionLog.objects.count())
        tlog = models.SomeWorkflowLastTransitionLog.objects.get()
        self.assertEqual(self.obj, tlog.obj)
        self.assertEqual('ab', tlog.transition)
        self.assertEqual('a', tlog.from_state)
        self.assertEqual('b', tlog.to_state)

    def test_two_transitions(self):
        self.assertEqual(0, models.SomeWorkflowLastTransitionLog.objects.count())

        self.obj.ab()
        self.assertEqual(1, models.SomeWorkflowLastTransitionLog.objects.count())

        self.obj.ba()
        self.assertEqual(1, models.SomeWorkflowLastTransitionLog.objects.count())

        tlog = models.SomeWorkflowLastTransitionLog.objects.get()
        self.assertEqual(self.obj, tlog.obj)
        self.assertEqual('ba', tlog.transition)
        self.assertEqual('b', tlog.from_state)
        self.assertEqual('a', tlog.to_state)


class GenericLastTransitionLogTestCase(test.TestCase):
    def setUp(self):
        self.obj = models.GenericWorkflowEnabled.objects.create()

    def test_transitions(self):
        self.assertEqual(0, models.GenericWorkflowLastTransitionLog.objects.count())

        self.obj.ab()
        self.assertEqual(1, models.GenericWorkflowLastTransitionLog.objects.count())
        tlog = models.GenericWorkflowLastTransitionLog.objects.get()
        self.assertEqual(self.obj, tlog.modified_object)
        self.assertEqual('ab', tlog.transition)
        self.assertEqual('a', tlog.from_state)
        self.assertEqual('b', tlog.to_state)

    def test_two_transitions(self):
        self.assertEqual(0, models.GenericWorkflowLastTransitionLog.objects.count())

        self.obj.ab()
        self.assertEqual(1, models.GenericWorkflowLastTransitionLog.objects.count())

        self.obj.ba()
        self.assertEqual(1, models.GenericWorkflowLastTransitionLog.objects.count())

        tlog = models.GenericWorkflowLastTransitionLog.objects.get()
        self.assertEqual(self.obj, tlog.modified_object)
        self.assertEqual('ba', tlog.transition)
        self.assertEqual('b', tlog.from_state)
        self.assertEqual('a', tlog.to_state)


@unittest.skipIf(south is None, "Couldn't import south.")
class SouthTestCase(test.TestCase):
    """Tests south-related behavior."""

    frozen_workflow = (
        "__import__('xworkflows', globals(), locals()).base.WorkflowMeta("
        "'MyWorkflow', (), {'states': (('foo', u'Foo'), ('bar', u'Bar'), "
        "('baz', u'Baz')), 'initial_state': 'foo'})")

    def test_south_triple(self):
        field = models.MyWorkflowEnabled._meta.get_field_by_name('state')[0]
        triple = field.south_field_triple()

        self.assertEqual(
            (
                'django_xworkflows.models.StateField',  # Class
                [],  # *args
                {
                    'default': "'foo'",
                    'max_length': '16',
                    'workflow': self.frozen_workflow},  # **kwargs
            ), triple)

    def test_freezing_model(self):
        frozen = south.modelsinspector.get_model_fields(models.MyWorkflowEnabled)

        self.assertEqual(self.frozen_workflow, frozen['state'][2]['workflow'])

    def test_freezing_app(self):
        frozen = south.creator.freezer.freeze_apps('djworkflows')
        self.assertEqual(self.frozen_workflow, frozen['djworkflows.myworkflowenabled']['state'][2]['workflow'])

    def test_frozen_orm(self):
        frozen = south.creator.freezer.freeze_apps('djworkflows')

        class FakeMigration(object):
            models = frozen

        frozen_orm = south.orm.FakeORM(FakeMigration, 'djworkflows')

        frozen_model = frozen_orm.MyWorkflowEnabled
        frozen_field = frozen_model._meta.get_field_by_name('state')[0]

        for state in models.MyWorkflow.states:
            frozen_state = frozen_field.workflow.states[state.name]
            self.assertEqual(state.name, frozen_state.name)

        self.assertEqual(models.MyWorkflow.initial_state.name,
            frozen_field.workflow.initial_state.name)
