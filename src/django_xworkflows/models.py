# coding: utf-8
"""Specific versions of XWorkflows to use with Django."""

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
Workflow = base.Workflow
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
        return self.to_python(value)

    def get_db_prep_value(self, value, connection, prepared=False):
        if not prepared:
            value = self.get_prep_value(value)
        return value.state.name

    def value_to_string(self, obj):
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
        attrs[state_field] = StateField(workflow)

    @classmethod
    def _copy_implems(mcs, workflow, state_field):
        return ImplementationList.copy_from(workflow.implementations,
                                            state_field=state_field)


class WorkflowEnabled(base.BaseWorkflowEnabled):
    """Base class for all django models wishing to use a Workflow."""
    __metaclass__ = WorkflowEnabledMeta

    def _get_FIELD_display(self, field):
        if isinstance(field, StateField):
            value = getattr(self, field.attname)
            return force_unicode(value.title)
        else:
            return super(WorkflowEnabled, self)._get_FIELD_display(field)


class ImplementationList(base.ImplementationList):
    """Internal; list of implementations for a workflow."""
    def _add_implem(cls, attrs, attrname, implem):
        attrs[attrname] = TransitionImplementation.copy_from(implem)


class TransitionImplementation(base.TransitionImplementation):
    """Internal; wraps the implementation of a transition for a workflow."""

    extra_kwargs = {'log': True, 'save': True, 'user': None}

    @classmethod
    def copy_from(cls, implem):
        return cls(implem.transition, implem.field_name, implem.implementation)

    def _call_implem(self, instance, cls_kwargs, *args, **kwargs):
        return super(TransitionImplementation, self)._call_implem(instance, cls_kwargs, *args, **kwargs)

    def _post_transition(self, instance, res, cls_kwargs, *args, **kwargs):
        save = cls_kwargs['save']
        log = cls_kwargs['log']
        user = cls_kwargs['user']
        super(TransitionImplementation, self)._post_transition(instance, res, cls_kwargs, *args, **kwargs)
        if save:
            instance.save()
        if log:
            TransitionLog.objects.create(modified_object=instance,
                                         transition=self.transition.name,
                                         user=user)


class TransitionLog(models.Model):
    """The log for a transition.

    Attributes:
        modified_object (django.db.model.Model): the object affected by this
            transition.
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
    modified_object = generic.GenericForeignKey(
            ct_field="content_type",
            fk_field="content_id")

    transition = models.CharField(_(u"transition"), max_length=255)
    user = models.ForeignKey(
        getattr(settings, 'XWORKFLOWS_USER_MODEL', 'auth.User'),
        blank=True,
        null=True,
        verbose_name=_(u"author"))
    timestamp = models.DateTimeField(_(u"performed at"), auto_now_add=True)

    class Meta:
        ordering = ('timestamp', 'user', 'transition')
        verbose_name = _(u'XWorkflow transition log')
        verbose_name_plural = _(u'XWorkflow transition logs')
