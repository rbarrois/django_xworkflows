# coding: utf-8
"""Specific versions of XWorkflows to use with Django."""

from django.db import models
from django.core import exceptions
from django.forms import fields
from django.forms import widgets
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext_lazy as _

from xworkflows import base


State = base.State
AbortTransition = base.AbortTransition


class StateSelect(widgets.Select):

    def render(self, name, value, attrs=None, choices=()):
        if isinstance(value, base.StateField):
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
            value (xworkflows.base.StateField): The base.StateField returned by to_python.
            model_instance: A WorkflowEnabled instance
        """
        if not isinstance(value, base.StateField):
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
    def _add_workflow(mcs, workflow, state_field, attrs):
        """Attach the workflow to a set of attributes.

        This sets the django-specific StateField.
        """
        attrs[state_field] = StateField(workflow)


class WorkflowEnabled(base.BaseWorkflowEnabled):
    """Base class for all django models wishing to use a Workflow."""
    __metaclass__ = WorkflowEnabledMeta

    def _get_FIELD_display(self, field):
        if isinstance(field, StateField):
            value = getattr(self, field.attname)
            return force_unicode(value.title)
        else:
            return super(WorkflowEnabled, self)._get_FIELD_display(field)


class Workflow(base.Workflow):
    def __init__(self, log_model='xworkflow_log.TransitionLog', *args, **kwargs):
        super(Workflow, self).__init__(*args, **kwargs)

        if log_model:
            app_label, model_label = log_model.rsplit('.', 1)
            log_model = models.get_model(app_label, model_label)
        self.log_model = log_model

    def db_log(self, transition, from_state, instance, user=None, *args, **kwargs):
        if self.log_model:
            self.log_model.objects.create(modified_object=instance,
                                         transition=transition.name,
                                         user=user)

    def log_transition(self, transition, from_state, instance,
            save=True, log=True, *args, **kwargs):
        super(Workflow, self).log_transition(
            transition, from_state, instance, *args, **kwargs)
        if save:
            instance.save()
        if log:
            self.db_log(transition, from_state, instance, *args, **kwargs)
