# coding: utf-8
"""Specific versions of XWorkflows to use with Django."""

from django.db import models
from django.conf import settings
from django.contrib.contenttypes import generic
from django.contrib.contenttypes import models as ct_models
from django.core import exceptions

from django.utils.translation import ugettext_lazy as _

from xworkflows import base


Workflow = base.Workflow
AbortTransition = base.AbortTransition


class StateField(models.CharField):
    """Holds the current state of a WorkflowEnabled object."""

    default_error_messages = {
        'invalid': _(u"Choose a valid state."),
    }
    description = _(u"State")

    __metaclass__ = models.SubfieldBase

    def __init__(self, workflow, **kwargs):
        self.workflow = workflow
        kwargs['choices'] = ((st.name, st.title) for st in self.workflow.states)
        kwargs['max_length'] = max(len(st.name) for st in self.workflow.states)
        kwargs['blank'] = False
        kwargs['null'] = False
        kwargs['default'] = self.workflow.initial_state.name
        return super(StateField, self).__init__(**kwargs)

    def get_internal_type(self):
        return "CharField"

    def to_python(self, value):
        """Converts the DB-stored value into a Python value."""
        if isinstance(value, base.StateField):
            res = value
        else:
            if isinstance(value, base.State):
                state = value
            elif value is None:
                state = self.workflow.initial_state
            else:
                try:
                    state = self.workflow.states[value]
                except KeyError:
                    raise exceptions.ValidationError(self.error_messages['invalid'])
            res = base.StateField(state, self.workflow)

        if res.state not in self.workflow.states:
            raise exceptions.ValidationError(self.error_messages['invalid'])

        return res

    def get_prep_value(self, value):
        return self.to_python(value)

    def get_db_prep_value(self, value, connection, prepared=False):
        if not prepared:
            value = self.get_prep_value(value)
        return value.state.name

    def value_to_string(self, obj):
        statefield = self.to_python(self._get_val_from_obj(obj))
        return statefield.state.name


class WorkflowEnabledMeta(base.WorkflowEnabledMeta, models.base.ModelBase):
    """Metaclass for WorkflowEnabled objects."""

    @classmethod
    def _add_workflow(mcs, workflow, state_field, attrs):
        attrs[state_field] = StateField(workflow)

    @classmethod
    def _copy_implems(mcs, workflow, state_field):
        return ImplementationList.copy_from(workflow.implementations,
                                            state_field=state_field)


class WorkflowEnabled(base.BaseWorkflowEnabled, models.Model):
    """Base class for all django models wishing to use a Workflow."""
    __metaclass__ = WorkflowEnabledMeta


class ImplementationList(base.ImplementationList):
    """Internal; list of implementations for a workflow."""
    def _add_implem(cls, attrs, attrname, implem):
        attrs[attrname] = TransitionImplementation.copy_from(implem)


class TransitionImplementation(base.TransitionImplementation):
    """Internal; wraps the implementation of a transition for a workflow."""

    @classmethod
    def copy_from(cls, implem):
        return cls(implem.transition, implem.field_name, implem.implementation)

    def _call_implem(self, instance, save=True, log=True, user=None, *args, **kwargs):
        return super(TransitionImplementation, self)._call_implem(instance, *args, **kwargs)

    def _post_transition(self, instance, res, save=True, log=True, user=None, *args, **kwargs):
        super(TransitionImplementation, self)._post_transition(instance, res, *args, **kwargs)
        if save:
            instance.save()
        if log:
            TransitionLog.objects.create(obj=instance,
                                         transition=self.transition.name,
                                         user=user)


class TransitionLog(models.Model):
    """The log for a transition.

    Attributes:
        obj (django.db.model.Model): the object affected by this transition.
        transition (str): The name of the transition being performed.
        user (django.contrib.auth.user): the user performing the transition; the
            actual model to use here is defined in the XWORKFLOWS_USER_MODEL
            setting.
        timestamp (datetime): The time at which the Transition was performed.
    """

    content_type = models.ForeignKey(ct_models.ContentType,
                                     verbose_name=_(u"Content type"),
                                     related_name="workflow_object",
                                     blank=True, null=True)
    content_id = models.PositiveIntegerField(_(u"Content id"), blank=True, null=True)
    obj = generic.GenericForeignKey(ct_field="content_type", fk_field="content_id")

    transition = models.CharField(max_length=255)
    user = models.ForeignKey(
        getattr(settings, 'XWORKFLOWS_USER_MODEL', 'auth.User'),
        blank=True,
        null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('timestamp', 'user', 'transition')


