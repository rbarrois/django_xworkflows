# -*- coding: utf-8 -*-
# Copyright (c) 2011-2012 Raphaël Barrois

"""Specific versions of XWorkflows to use with Django."""

import datetime

from django.db import models
from django.conf import settings
from django.contrib.contenttypes import generic
from django.contrib.contenttypes import models as ct_models
from django.core import exceptions
from django.forms import fields
from django.forms import widgets
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext_lazy as _

from xworkflows import base


State = base.State
AbortTransition = base.AbortTransition
transition = base.transition


class StateSelect(widgets.Select):

    def render(self, name, value, attrs=None, choices=()):
        if isinstance(value, base.StateWrapper):
            state_name = value.state.name
        elif isinstance(value, base.State):
            state_name = value.name
        else:
            state_name = str(value)
        return super(StateSelect, self).render(name, state_name, attrs, choices)


class StateFieldProperty(object):
    """Property-like attribute for WorkflowEnabled classes.

    Similar to django.db.models.fields.subclassing.Creator, but doesn't raise
    AttributeError.
    """
    def __init__(self, field):
        self.field = field

    def __get__(self, instance, owner):
        """Retrieve the related attributed from a class / an instance.

        If retrieving from an instance, return the actual value; if retrieving
        from a class, return the workflow.
        """
        if instance:
            return instance.__dict__.get(self.field.name, self.field.workflow.initial_state)
        else:
            return self.field.workflow

    def __set__(self, instance, value):
        instance.__dict__[self.field.name] = self.field.to_python(value)


class StateField(models.Field):
    """Holds the current state of a WorkflowEnabled object."""

    default_error_messages = {
        'invalid': _(u"Choose a valid state."),
        'wrong_type': _(u"Please enter a valid value (got %r)."),
        'wrong_workflow': _(u"Please enter a value from the right workflow (got %r)."),
        'invalid_state': _(u"%s is not a valid state."),
    }
    description = _(u"State")

    def __init__(self, workflow, **kwargs):
        if isinstance(workflow, type):
            workflow = workflow()
        self.workflow = workflow
        kwargs['choices'] = list((st.name, st.title) for st in self.workflow.states)
        kwargs['max_length'] = max(len(st.name) for st in self.workflow.states)
        kwargs['blank'] = False
        kwargs['null'] = False
        kwargs['default'] = self.workflow.initial_state.name
        return super(StateField, self).__init__(**kwargs)

    def get_internal_type(self):
        return "CharField"

    def contribute_to_class(self, cls, name):
        """Contribute the state to a Model.

        Attaches a StateFieldProperty to wrap the attribute.
        """
        super(StateField, self).contribute_to_class(cls, name)
        setattr(cls, self.name, StateFieldProperty(self))

    def to_python(self, value):
        """Converts the DB-stored value into a Python value."""
        if isinstance(value, base.StateWrapper):
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
            res = base.StateWrapper(state, self.workflow)

        if res.state not in self.workflow.states:
            raise exceptions.ValidationError(self.error_messages['invalid'])

        return res

    def get_prep_value(self, value):
        """Prepares a value.

        Returns a State object.
        """
        return self.to_python(value)

    def get_db_prep_value(self, value, connection, prepared=False):
        """Convert a value to DB storage.

        Returns the state name.
        """
        if not prepared:
            value = self.get_prep_value(value)
        return value.state.name

    def value_to_string(self, obj):
        """Convert a field value to a string.

        Returns the state name.
        """
        statefield = self.to_python(self._get_val_from_obj(obj))
        return statefield.state.name

    def validate(self, value, model_instance):
        """Validate that a given value is a valid option for a given model instance.

        Args:
            value (xworkflows.base.StateWrapper): The base.StateWrapper returned by to_python.
            model_instance: A WorkflowEnabled instance
        """
        if not isinstance(value, base.StateWrapper):
            raise exceptions.ValidationError(self.error_messages['wrong_type'] % value)
        elif not value.workflow == self.workflow:
            raise exceptions.ValidationError(self.error_messages['wrong_workflow'] % value.workflow)
        elif not value.state in self.workflow.states:
            raise exceptions.ValidationError(self.error_messages['invalid_state'] % value.state)

    def formfield(self, form_class=fields.ChoiceField, widget=StateSelect, **kwargs):
        return super(StateField, self).formfield(form_class, widget=widget, **kwargs)


    try:
        import south
    except ImportError:
        pass
    else:
        def south_field_triple(self):
            """Return a suitable description of this field for South."""
            workflow_class = type(self.workflow)
            workflow = ("__import__('%(mod)s', globals(), locals(), '%(cls)s').%(cls)s"
                    % {'mod': workflow_class.__module__, 'cls': workflow_class.__name__})
            from south.modelsinspector import introspector
            args, kwargs = introspector(self)
            return ('django_xworkflows.models.StateField', [workflow] + args, kwargs)


class WorkflowEnabledMeta(base.WorkflowEnabledMeta, models.base.ModelBase):
    """Metaclass for WorkflowEnabled objects."""

    @classmethod
    def _find_workflows(mcs, attrs):
        """Find workflow definition(s) in a WorkflowEnabled definition."""
        workflows = {}
        for k, v in attrs.iteritems():
            if isinstance(v, StateField):
                workflows[k] = v
        return workflows

    @classmethod
    def _add_workflow(mcs, field_name, state_field, attrs):
        """Attach the workflow to a set of attributes.

        This sets the django-specific StateField.
        """
        attrs[field_name] = state_field


class WorkflowEnabled(base.BaseWorkflowEnabled):
    """Base class for all django models wishing to use a Workflow."""
    __metaclass__ = WorkflowEnabledMeta

    def _get_FIELD_display(self, field):
        if isinstance(field, StateField):
            value = getattr(self, field.attname)
            return force_unicode(value.title)
        else:
            return super(WorkflowEnabled, self)._get_FIELD_display(field)


class BaseTransitionLog(models.Model):
    """Abstract model for a minimal database logging setup.

    Attributes:
        modified_object (django.db.model.Model): the object affected by this
            transition.
        from_state (str): the name of the origin state
        to_state (str): the name of the destination state
        transition (str): The name of the transition being performed.
        timestamp (datetime): The time at which the Transition was performed.
    """

    content_type = models.ForeignKey(ct_models.ContentType,
                                     verbose_name=_(u"Content type"),
                                     related_name="workflow_object",
                                     blank=True, null=True)
    content_id = models.PositiveIntegerField(_(u"Content id"), blank=True, null=True)
    modified_object = generic.GenericForeignKey(
            ct_field="content_type",
            fk_field="content_id")

    transition = models.CharField(_(u"transition"), max_length=255)
    from_state = models.CharField(_(u"from state"), max_length=255)
    to_state = models.CharField(_(u"to state"), max_length=255)
    timestamp = models.DateTimeField(_(u"performed at"), default=datetime.datetime.now)

    class Meta:
        ordering = ('-timestamp', 'transition')
        verbose_name = _(u'XWorkflow transition log')
        verbose_name_plural = _(u'XWorkflow transition logs')
        abstract = True

    def __unicode__(self):
        return u'%r: %s -> %s at %s' % (self.modified_object, self.from_state,
            self.to_state, self.timestamp.isoformat())


def get_default_log_model():
    """The default log model depends on whether the xworkflow_log app is there."""
    if 'django_xworkflows.xworkflow_log' in settings.INSTALLED_APPS:
        return 'xworkflow_log.TransitionLog'
    else:
        return ''


class Workflow(base.Workflow):
    """Extended workflow that handles object saving and logging to the database."""

    #: Save log to this django model
    log_model = get_default_log_model()

    def __init__(self, log_model=None, *args, **kwargs):
        super(Workflow, self).__init__(*args, **kwargs)

        if log_model is None:
            log_model = self.log_model

        if log_model:
            app_label, model_label = log_model.rsplit('.', 1)
            log_model = models.get_model(app_label, model_label)
        self.log_model = log_model

    def db_log(self, transition, from_state, instance, user=None, *args, **kwargs):
        """Logs the transition into the database."""
        if self.log_model:
            self.log_model.objects.create(modified_object=instance,
                                         transition=transition.name,
                                         user=user)

    def log_transition(self, transition, from_state, instance,
            save=True, log=True, *args, **kwargs):
        """Generic transition logging."""
        super(Workflow, self).log_transition(
            transition, from_state, instance, *args, **kwargs)
        if save:
            instance.save()
        if log:
            self.db_log(transition, from_state, instance, *args, **kwargs)
