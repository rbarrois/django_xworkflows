# -*- coding: utf-8 -*-
# Copyright (c) 2011-2013 Raphaël Barrois
# This code is distributed under the two-clause BSD license.

from __future__ import unicode_literals

"""Specific versions of XWorkflows to use with Django."""

from django.db import models
from django.conf import settings
from django.contrib.contenttypes import models as ct_models
from django.core import exceptions
from django.forms import fields
from django.forms import widgets
from django.utils.translation import ugettext_lazy as _

from xworkflows import base

from . import compat


State = base.State
AbortTransition = base.AbortTransition
ForbiddenTransition = base.ForbiddenTransition
InvalidTransitionError = base.InvalidTransitionError
WorkflowError = base.WorkflowError

transition = base.transition


class StateSelect(widgets.Select):
    """Custom 'select' widget to handle state retrieval."""

    def render(self, name, value, attrs=None, *args):
        """Handle a few expected values for rendering the current choice.

        Extracts the state name from StateWrapper and State object.
        """
        if isinstance(value, base.StateWrapper):
            state_name = value.state.name
        elif isinstance(value, base.State):
            state_name = value.name
        else:
            state_name = str(value)
        return super(StateSelect, self).render(name, state_name, attrs, *args)


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
        'invalid': _("Choose a valid state."),
        'wrong_type': _("Please enter a valid value (got %r)."),
        'wrong_workflow': _("Please enter a value from the right workflow (got %r)."),
        'invalid_state': _("%s is not a valid state."),
    }
    description = _("State")

    DEFAULT_MAX_LENGTH = 16

    def __init__(self, workflow, **kwargs):
        if isinstance(workflow, type):
            workflow = workflow()
        self.workflow = workflow
        kwargs['choices'] = list(
            (st.name, st.title) for st in self.workflow.states)

        kwargs['max_length'] = max(
            kwargs.get('max_length', self.DEFAULT_MAX_LENGTH),
            max(len(st.name) for st in self.workflow.states))
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

    def south_field_triple(self):
        """Return a suitable description of this field for South."""
        from south.modelsinspector import introspector
        args, kwargs = introspector(self)

        state_def = tuple(
            (str(st.name), str(st.name)) for st in self.workflow.states)
        initial_state_def = str(self.workflow.initial_state.name)

        workflow = (
            "__import__('xworkflows', globals(), locals()).base.WorkflowMeta("
            "'%(class_name)s', (), "
            "{'states': %(states)r, 'initial_state': %(initial_state)r})" % {
                'class_name': str(self.workflow.__class__.__name__),
                'states': state_def,
                'initial_state': initial_state_def,
            })
        kwargs['workflow'] = workflow

        return ('django_xworkflows.models.StateField', args, kwargs)

    def deconstruct(self):
        """Deconstruction for migrations.

        Return a simpler object (_SerializedWorkflow), since our Workflows
        are rather hard to serialize: Django doesn't like deconstructing
        metaclass-built classes.
        """
        name, path, args, kwargs = super(StateField, self).deconstruct()

        # We want to display the proper class name, which isn't available
        # at the same point for _SerializedWorkflow and Workflow.
        if isinstance(self.workflow, _SerializedWorkflow):
            workflow_class_name = self.workflow._name
        else:
            workflow_class_name = self.workflow.__class__.__name__

        kwargs['workflow'] = _SerializedWorkflow(
            name=workflow_class_name,
            initial_state=str(self.workflow.initial_state.name),
            states=[str(st.name) for st in self.workflow.states],
        )
        del kwargs['choices']
        del kwargs['default']
        return name, path, args, kwargs


class WorkflowEnabledMeta(base.WorkflowEnabledMeta, models.base.ModelBase):
    """Metaclass for WorkflowEnabled objects."""

    @classmethod
    def _find_workflows(mcs, attrs):
        """Find workflow definition(s) in a WorkflowEnabled definition.

        This method overrides the default behavior from xworkflows in order to
        use our custom StateField objects.
        """
        workflows = {}
        for k, v in attrs.items():
            if isinstance(v, StateField):
                workflows[k] = v
        return workflows

    @classmethod
    def _add_workflow(mcs, field_name, state_field, attrs):
        """Attach the workflow to a set of attributes.

        Constructs the ImplementationWrapper for transitions, and adds them to
        the attributes dict.

        Args:
            field_name (str): name of the attribute where the StateField lives
            state_field (StateField): StateField describing that attribute
            attrs (dict): dictionary of attributes for the class being created
        """
        # No need to override the 'field_name' from attrs: it already contains
        # a valid value, and that would clash with django model inheritance.
        pass


class BaseWorkflowEnabled(base.BaseWorkflowEnabled):
    """Base class for all django models wishing to use a Workflow."""

    def _get_FIELD_display(self, field):
        if isinstance(field, StateField):
            value = getattr(self, field.attname)
            return compat.force_text(value.title)
        else:
            return super(BaseWorkflowEnabled, self)._get_FIELD_display(field)


# Workaround for metaclasses on python2/3.
# Equivalent to:
# Python2
#
# class WorkflowEnabled(BaseWorkflowEnabled):
#     __metaclass__ = WorkflowEnabledMeta
#
# Python3
#
# class WorkflowEnabled(metaclass=WorkflowEnabledMeta):
#     pass

WorkflowEnabled = WorkflowEnabledMeta(str('WorkflowEnabled'), (BaseWorkflowEnabled,), {'__module__': __name__})


def get_default_log_model():
    """The default log model depends on whether the xworkflow_log app is there."""
    if 'django_xworkflows.xworkflow_log' in settings.INSTALLED_APPS:
        return 'xworkflow_log.TransitionLog'
    else:
        return ''


class DjangoImplementationWrapper(base.ImplementationWrapper):
    """Restrict execution of transitions within templates"""
    # django < 1.4
    alters_data = True
    # django >= 1.4
    do_not_call_in_templates = True


class TransactionalImplementationWrapper(DjangoImplementationWrapper):
    """Customize the base ImplementationWrapper to run into a db transaction."""

    def __call__(self, *args, **kwargs):
        with compat.atomic():
            return super(TransactionalImplementationWrapper, self).__call__(*args, **kwargs)


@compat.deconstructible
class _SerializedWorkflow(object):
    """Serialized workflow for django.db.migrations.

    Wraps an actual Workflow object, but without the metaclass magic.

    This class makes it easy to retrieve a Workflow object from its class name,
    initial state and list of states; without going through a class declaration.
    """
    def __init__(self, name, initial_state, states):
        self._name = name
        self._initial_state = initial_state
        self._states = states

        # Create a new django_xworkflows.models.Workflow subclass,
        # using the provided fields.
        workflow_class = base.WorkflowMeta(
            # When constructing from django.db.migrations, we might get a unicode instead of a str for the name; 
            # this breaks calls to super()
            str(self._name),
            (Workflow,),
            {
                'states': [(st, st) for st in states],
                'initial_state': initial_state,
            },
        )
        self._workflow_class = workflow_class
        self._workflow = workflow_class()

    def __getattr__(self, attr):
        # Forward calls to the created Workflow object.
        return getattr(self._workflow, attr)

    def deconstruct(self):
        """Serialization for migrations; simply return our __init__ arguments."""
        return (
            'django_xworkflows.models._SerializedWorkflow',
            (),
            {
                'name': self._name,
                'initial_state': self._initial_state,
                'states': self._states,
            },
        )


class Workflow(base.Workflow):
    """Extended workflow that handles object saving and logging to the database.

    Attributes:
        log_model (str): the name of the log model to use; if empty, logging to
            database will be disabled.
        log_model_class (obj): the class for the log model; resolved once django
            is completely loaded.
    """
    #: Behave properly in Django templates
    implementation_class = DjangoImplementationWrapper

    #: Save log to this django model (name of the model)
    log_model = get_default_log_model()

    #: Save log to this django model (actual class)
    log_model_class = None

    def __init__(self, *args, **kwargs):
        # Fetch 'log_model' if overridden.
        log_model = kwargs.pop('log_model', self.log_model)

        # Fetch 'log_model_class' if overridden.
        log_model_class = kwargs.pop('log_model_class', self.log_model_class)

        super(Workflow, self).__init__(*args, **kwargs)

        self.log_model = log_model
        self.log_model_class = log_model_class

    def _get_log_model_class(self):
        """Cache for fetching the actual log model object once django is loaded.

        Otherwise, import conflict occur: WorkflowEnabled imports <log_model>
        which tries to import all models to retrieve the proper model class.
        """
        if self.log_model_class is not None:
            return self.log_model_class

        app_label, model_label = self.log_model.rsplit('.', 1)
        self.log_model_class = compat.get_model(app_label, model_label)
        return self.log_model_class

    def db_log(self, transition, from_state, instance, *args, **kwargs):
        """Logs the transition into the database."""
        if self.log_model:
            model_class = self._get_log_model_class()

            extras = {}
            for db_field, transition_arg, default in model_class.EXTRA_LOG_ATTRIBUTES:
                extras[db_field] = kwargs.get(transition_arg, default)

            return model_class.log_transition(
                    modified_object=instance,
                   transition=transition.name,
                   from_state=from_state.name,
                   to_state=transition.target.name,
                   **extras)

    def log_transition(self, transition, from_state, instance, *args, **kwargs):
        """Generic transition logging."""
        save = kwargs.pop('save', True)
        log = kwargs.pop('log', True)
        super(Workflow, self).log_transition(
            transition, from_state, instance, *args, **kwargs)
        if save:
            instance.save()
        if log:
            self.db_log(transition, from_state, instance, *args, **kwargs)


@compat.python_2_unicode_compatible
class BaseTransitionLog(models.Model):
    """Abstract model for a minimal database logging setup.

    Class attributes:
        MODIFIED_OBJECT_FIELD (str): name of the field storing the modified
            object.
        EXTRA_LOG_ATTRIBUTES ((db_field, kwarg, default) list): Describes extra
            transition kwargs to store:
            - db_field is the name of the attribute where data should be stored
            - kwarg is the name of the keyword argument of the transition to
              record
            - default is the default value to store if no value was provided for
              kwarg in the transition's arguments

    Attributes:
        modified_object (django.db.model.Model): the object affected by this
            transition.
        from_state (str): the name of the origin state
        to_state (str): the name of the destination state
        transition (str): The name of the transition being performed.
        timestamp (datetime): The time at which the Transition was performed.
    """
    MODIFIED_OBJECT_FIELD = ''
    EXTRA_LOG_ATTRIBUTES = ()

    transition = models.CharField(_("transition"), max_length=255,
        db_index=True)
    from_state = models.CharField(_("from state"), max_length=255,
        db_index=True)
    to_state = models.CharField(_("to state"), max_length=255,
        db_index=True)
    timestamp = models.DateTimeField(_("performed at"),
        default=compat.now, db_index=True)

    class Meta:
        ordering = ('-timestamp', 'transition')
        verbose_name = _('XWorkflow transition log')
        verbose_name_plural = _('XWorkflow transition logs')
        abstract = True

    def get_modified_object(self):
        if self.MODIFIED_OBJECT_FIELD:
            return getattr(self, self.MODIFIED_OBJECT_FIELD, None)
        return None

    @classmethod
    def log_transition(cls, transition, from_state, to_state, modified_object, **kwargs):
        kwargs.update({
            'transition': transition,
            'from_state': from_state,
            'to_state': to_state,
            cls.MODIFIED_OBJECT_FIELD: modified_object,
        })
        return cls.objects.create(**kwargs)

    def __str__(self):
        return '%r: %s -> %s at %s' % (self.get_modified_object(),
            self.from_state, self.to_state, self.timestamp.isoformat())


class GenericTransitionLog(BaseTransitionLog):
    """Abstract model for a minimal database logging setup.

    Specializes BaseTransitionLog to use a GenericForeignKey.

    Attributes:
        modified_object (django.db.model.Model): the object affected by this
            transition.
        from_state (str): the name of the origin state
        to_state (str): the name of the destination state
        transition (str): The name of the transition being performed.
        timestamp (datetime): The time at which the Transition was performed.
    """
    MODIFIED_OBJECT_FIELD = 'modified_object'

    content_type = models.ForeignKey(ct_models.ContentType,
                                     verbose_name=_("Content type"),
                                     blank=True, null=True)
    content_id = models.PositiveIntegerField(_("Content id"),
        blank=True, null=True, db_index=True)
    modified_object = compat.GenericForeignKey(
            ct_field="content_type",
            fk_field="content_id")

    class Meta:
        ordering = ('-timestamp', 'transition')
        verbose_name = _('XWorkflow transition log')
        verbose_name_plural = _('XWorkflow transition logs')
        abstract = True


class BaseLastTransitionLog(BaseTransitionLog):
    """Alternate abstract model holding only the latest transition."""

    class Meta:
        verbose_name = _('XWorkflow last transition log')
        verbose_name_plural = _('XWorkflow last transition logs')
        abstract = True

    @classmethod
    def _update_or_create(cls, unique_fields, **kwargs):
        last_transition, created = cls.objects.get_or_create(defaults=kwargs, **unique_fields)
        if not created:
            for field, value in kwargs.items():
                setattr(last_transition, field, value)
            last_transition.timestamp = compat.now()
            last_transition.save()

        return last_transition

    @classmethod
    def log_transition(cls, transition, from_state, to_state, modified_object, **kwargs):
        kwargs.update({
            'transition': transition,
            'from_state': from_state,
            'to_state': to_state,
        })

        non_defaults = {
            cls.MODIFIED_OBJECT_FIELD: modified_object,
        }

        return cls._update_or_create(non_defaults, **kwargs)


class GenericLastTransitionLog(BaseLastTransitionLog):
    """Abstract model for a minimal database logging setup.

    Specializes BaseLastTransitionLog to use a GenericForeignKey.

    Attributes:
        modified_object (django.db.model.Model): the object affected by this
            transition.
        from_state (str): the name of the origin state
        to_state (str): the name of the destination state
        transition (str): The name of the transition being performed.
        timestamp (datetime): The time at which the Transition was performed.
    """
    MODIFIED_OBJECT_FIELD = 'modified_object'

    content_type = models.ForeignKey(ct_models.ContentType,
                                     verbose_name=_("Content type"),
                                     related_name='last_transition_logs',
                                     blank=True, null=True)
    content_id = models.PositiveIntegerField(_("Content id"),
        blank=True, null=True, db_index=True)
    modified_object = compat.GenericForeignKey(
            ct_field="content_type",
            fk_field="content_id")

    class Meta:
        verbose_name = _('XWorkflow last transition log')
        verbose_name_plural = _('XWorkflow last transition logs')
        abstract = True
        unique_together =  ('content_type', 'content_id')

    @classmethod
    def _update_or_create(cls, unique_fields, **kwargs):
        modified_object = unique_fields.pop(cls.MODIFIED_OBJECT_FIELD)
        content_type = ct_models.ContentType.objects.get_for_model(modified_object.__class__)
        content_id = modified_object.id

        unique_fields['content_type'] = content_type
        unique_fields['content_id'] = content_id

        return super(GenericLastTransitionLog, cls)._update_or_create(unique_fields, **kwargs)

