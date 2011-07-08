from django.core import exceptions
from django.utils import unittest

import xworkflows
from . import models


class ModelTestCase(unittest.TestCase):
    def test_workflow(self):
        self.assertEqual(models.MyWorkflow.states,
                         models.MyWorkflowEnabled._workflows['state'].states)

    def test_dual_workflows(self):
        self.assertIn('state1', models.WithTwoWorkflows._workflows)
        self.assertIn('state2', models.WithTwoWorkflows._workflows)

        self.assertEqual('foo',
                models.WithTwoWorkflows._workflows['state1'].states['foo'].title)
        self.assertEqual('StateA',
                models.WithTwoWorkflows._workflows['state2'].states['a'].title)

    def test_instantiation(self):
        o = models.MyWorkflowEnabled()
        self.assertEqual(models.MyWorkflow.states['foo'], o.state)

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

    def test_transitions(self):
        o = models.MyWorkflowEnabled()
        self.assertEqual(models.MyWorkflow.states['foo'], o.state)

        self.assertEqual(None, o.foobar(save=False, log=False))

        self.assertTrue(o.state.is_bar)

    def test_invalid_transition(self):
        o = models.MyWorkflowEnabled()
        self.assertTrue(o.state.is_foo)

        self.assertRaises(xworkflows.InvalidTransitionError, o.bazbar)
