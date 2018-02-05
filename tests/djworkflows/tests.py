# -*- coding: utf-8 -*-
# Copyright (c) 2011-2013 Raphaël Barrois
# This code is distributed under the two-clause BSD license.

from __future__ import unicode_literals

import contextlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

from django.core import exceptions
from django.core import serializers
from django.db import models as django_models
from django import forms
from django import test
from django.template import engines as template_engines

import xworkflows

from django_xworkflows import models as xwf_models
from django_xworkflows.xworkflow_log import models as xwlog_models

from . import models


if sys.version_info[0] <= 2:
    def text_type(text):
        return unicode(text)  # noqa: F821
else:
    def text_type(text):
        return str(text)


@contextlib.contextmanager
def extra_pythonpath(pythonpath):
    old_path = os.environ.get('PYTHONPATH')
    if old_path is None:
        new_path = pythonpath
    else:
        new_path = '%s:%s' % (pythonpath, old_path)
    os.environ['PYTHONPATH'] = new_path
    yield
    if old_path is None:
        del os.environ['PYTHONPATH']
    else:
        os.environ['PYTHONPATH'] = old_path


@contextlib.contextmanager
def override_env(**kwargs):
    old_values = {}
    for k, v in kwargs.items():
        old_values[k] = os.environ.get(k)
        os.environ[k] = v
    yield

    for k, v in old_values.items():
        if v is None:
            del os.environ[k]
        else:
            os.environ[k] = v


class ModelTestCase(test.TestCase):
    def test_workflow(self):
        self.assertEqual(models.MyWorkflow.states,
                         models.MyWorkflowEnabled._workflows['state'].workflow.states)

    def test_field_attributes(self):
        field_def = models.MyWorkflowEnabled._meta.get_field('state')
        self.assertEqual(16, field_def.max_length)
        self.assertFalse(field_def.blank)
        self.assertFalse(field_def.null)
        self.assertEqual(models.MyWorkflow.initial_state.name, field_def.default)
        self.assertEqual(
            list((st.name, st.title) for st in models.MyWorkflow.states),
            field_def.choices,
        )

    def test_ald_field_attributes(self):
        field_def = models.WithTwoWorkflows._meta.get_field('state2')
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

        self.assertEqual('Foo', models.WithTwoWorkflows._workflows['state1'].workflow.states['foo'].title)
        self.assertEqual('StateA', models.WithTwoWorkflows._workflows['state2'].workflow.states['a'].title)

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
        self.assertEqual("Foo", o.get_state_display())
        self.assertEqual("AAA", o.get_other_display())

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

        # Also test with only
        qs_only = models.MyWorkflowEnabled.objects.only('other')
        self.assertEqual([val.state.name for val in qs_only.filter(state=foo)], ['foo'])
        self.assertEqual([val.state.name for val in qs_only.filter(state=bar)], ['bar'])

    def test_dumping(self):
        o = models.MyWorkflowEnabled()
        o.state = o.state.workflow.states.bar
        o.save()

        self.assertTrue(o.state.is_bar)

        data = serializers.serialize('json', models.MyWorkflowEnabled.objects.filter(pk=o.id))

        models.MyWorkflowEnabled.objects.all().delete()

        for obj in serializers.deserialize('json', data):
            obj.object.save()

        obj = models.MyWorkflowEnabled.objects.all()[0]
        self.assertTrue(obj.state.is_bar)

    def test_invalid_dump(self):
        data = '[{"pk": 1, "model": "djworkflows.myworkflowenabled", "fields": {"state": "blah"}}]'

        self.assertRaises(serializers.base.DeserializationError, list, serializers.deserialize('json', data))


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

        self.assertIn('foo -> bar', text_type(trlog))

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
        ab_datetime = models.SomeWorkflowLastTransitionLog.objects.get().timestamp

        self.obj.ba()
        self.assertEqual(1, models.SomeWorkflowLastTransitionLog.objects.count())

        tlog = models.SomeWorkflowLastTransitionLog.objects.get()
        self.assertEqual(self.obj, tlog.obj)
        self.assertEqual('ba', tlog.transition)
        self.assertEqual('b', tlog.from_state)
        self.assertEqual('a', tlog.to_state)
        self.assertTrue(tlog.timestamp > ab_datetime)


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
        ab_datetime = models.GenericWorkflowLastTransitionLog.objects.get().timestamp

        self.obj.ba()
        self.assertEqual(1, models.GenericWorkflowLastTransitionLog.objects.count())

        tlog = models.GenericWorkflowLastTransitionLog.objects.get()
        self.assertEqual(self.obj, tlog.modified_object)
        self.assertEqual('ba', tlog.transition)
        self.assertEqual('b', tlog.from_state)
        self.assertEqual('a', tlog.to_state)
        self.assertTrue(tlog.timestamp > ab_datetime)


class StateFieldMigrationTests(test.TestCase):
    def test_modelstate(self):
        from django.db.migrations import state as migrations_state
        mwe_mstate = migrations_state.ModelState.from_model(models.MyWorkflowEnabled)
        project_state = migrations_state.ProjectState()

        project_state.add_model(mwe_mstate)
        apps = project_state.apps

        model = apps.get_model('djworkflows.MyWorkflowEnabled')
        self.assertEqual(
            [st.name for st in models.MyWorkflow.states],
            [st.name for st in model._meta.fields[1].workflow.states],
        )


class ProjectMigrationTests(test.TestCase):
    DEMO_PROJECT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'demo_project')

    def setUp(self):
        self.debug = os.environ.get('DEBUG', '0') != '0'
        self.dirname = tempfile.mkdtemp(prefix='tmp_djxwf_tests_')
        self.source_models = os.path.join(self.DEMO_PROJECT_PATH, 'workflow_app', 'models.py')
        self.target_models = os.path.join(self.dirname, 'demo_project', 'workflow_app', 'models.py')

    def tearDown(self):
        def log_error(fn, path, excinfo):
            sys.stderr.write("Error while deleting %r: %r raised %r\n" % (
                path, fn, excinfo))

        shutil.rmtree(self.dirname, onerror=log_error)

    def setup_django_project(self):
        shutil.copytree(
            self.DEMO_PROJECT_PATH,
            os.path.join(self.dirname, 'demo_project'),
        )

    def step_models(self, step):
        """Somewhat "patch" the models for this step.

        Keep lines ending in '# step:x,y,z' where the current step is listed, or
        unmarked lines.

        This should allow us to test various changes, including adding/removing
        models and fields.
        """
        CONDITIONAL_LINE_RE = r'^.*# step:(\d+,)*\d+$'
        CONDITIONAL_STEP_LINE_RE = r'^.*# step:(\d+,)*{}(,\d+)*$'.format(step)
        with open(self.source_models, 'r') as src:
            lines = [
                l for l in src
                if (re.match(CONDITIONAL_STEP_LINE_RE, l.rstrip())
                    or not re.match(CONDITIONAL_LINE_RE, l.rstrip()))
            ]

        if self.debug:
            sys.stderr.write("\n>>> Writing lines matching step %d (%d lines).\n" % (step, len(lines)))
        with open(self.target_models, 'w') as dst:
            dst.write(''.join(lines))

    def test_makemigrations(self):
        self.setup_django_project()
        manage_py = os.path.join(self.dirname, 'demo_project', 'manage.py')

        verbosity_flag = '--verbosity=1' if self.debug else '--verbosity=0'

        for step in [1, 2, 3, 4, 5]:
            self.step_models(step)
            with extra_pythonpath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))):
                with override_env(DJANGO_SETTINGS_MODULE='demo_project.settings'):
                    subprocess.check_call([manage_py, 'makemigrations', verbosity_flag, 'workflow_app'])
                    subprocess.check_call([manage_py, 'migrate', verbosity_flag])

        # Run internal tests
        with extra_pythonpath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))):
            with override_env(DJANGO_SETTINGS_MODULE='demo_project.settings'):
                subprocess.check_call([manage_py, 'test', verbosity_flag, 'workflow_app'])


class TemplateTestCase(test.TestCase):
    """Tests states and transitions behavior in templates."""

    uTrue = text_type(True)
    uFalse = text_type(False)

    def setUp(self):
        self.obj = models.MyWorkflowEnabled()
        self.context = {'obj': self.obj, 'true': self.uTrue, 'false': self.uFalse}

    def render_fragment(self, fragment):
        tpl = template_engines['django'].from_string(fragment)
        return tpl.render(self.context)

    @unittest.skipIf(int(xworkflows.__version__.split('.')[0]) >= 1, "Behaviour changed in xworkflows-1.0.0")
    def test_state_display_is_title(self):
        self.assertEqual(self.render_fragment("{{obj.state}}"), self.obj.state.state.title)

    @unittest.skipIf(int(xworkflows.__version__.split('.')[0]) < 1, "Behaviour changed in xworkflows-1.0.0")
    def test_state_display_is_name(self):
        self.assertEqual(self.render_fragment("{{obj.state}}"), self.obj.state.state.name)

    def test_state(self):
        self.assertEqual(self.render_fragment("{{ obj.state.is_foo }}"), self.uTrue)
        self.assertEqual(
            self.render_fragment("{% if obj.state == 'foo' %}{{ true }}{% else %}{{ false }}{% endif %}"),
            self.uTrue,
        )

        self.assertEqual(self.render_fragment("{{ obj.state.is_bar }}"), self.uFalse)
        self.assertEqual(
            self.render_fragment("{% if obj.state == 'bar' %}{{ true }}{% else %}{{ false }}{% endif %}"),
            self.uFalse,
        )

    def test_django_magic(self):
        """Ensure that ImplementationWrappers have magic django attributes."""
        self.assertTrue(self.obj.foobar.alters_data)
        self.assertTrue(self.obj.foobar.do_not_call_in_templates)

    def test_transaction_attributes(self):
        self.assertEqual(self.render_fragment("{{ obj.foobar|safe}}"), text_type(self.obj.foobar))
        self.assertEqual(self.render_fragment("{{ obj.foobar.is_available }}"), self.uTrue)
        self.assertEqual(models.MyWorkflow.states.foo, self.obj.state)

        self.assertEqual(self.render_fragment("{{ obj.bazbar|safe}}"), text_type(self.obj.bazbar))
        self.assertEqual(self.render_fragment("{{ obj.bazbar.is_available }}"), self.uFalse)
        self.assertEqual(models.MyWorkflow.states.foo, self.obj.state)


class WidgetTestCase(test.TestCase):

    class MyWorkflowEnabledModelForm(forms.ModelForm):
        class Meta:
            model = models.MyWorkflowEnabled
            fields = ('state',)

    def test_StateSelect_widget(self):
        form = self.MyWorkflowEnabledModelForm()
        html = form.as_p()
        # Just make sure that it can be rendered.
        self.assertIn('<p>', html)
