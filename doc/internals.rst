=================
Library internals
=================

.. module:: django_xworkflows.models
    :synopsis: XWorkflows bindings for Django

This page documents the internal mechanisms of django_xworkflows.

Binding to a workflow
=====================

The mechanism to bind a django model to a :class:`xworkflows.Workflow` relies on the :class:`WorkflowEnabled` and :class:`StateField` classes.


.. class:: StateField(django.models.Field)

    This class is a simple Django :class:`~django.db.models.Field`, specifically tuned for a
    :class:`Workflow`.

    It is internally backed by a :class:`~django.db.models.CharField`
    containing the :attr:`~xworkflows.base.State.name` of the state.

    Reading the value always returns a :class:`xworkflows.base.StateWrapper`,
    writing checks that the value is a valid state or a valid state name.

    .. attribute:: workflow

        Mandatory; holds the :class:`Workflow` to which this :class:`StateField` relates

    .. attribute:: choices

        The workflow states, as a list of ``(name, title)`` tuples, for use in forms.

    .. attribute:: default

        The name of the inital state of the workflow

    .. attribute:: max_length

        The length of the longest state name in the workflow.

    .. attribute:: blank

        Such a field cannot be blanked (otherwise, the workflow wouldn't have a meaning).

    .. attribute:: null

        Since the field cannot be empty, is cannot be null either.

    .. method:: south_field_triple(self)

        Returns the south description of this field.
        When unfreezing, a fake :class:`Workflow` will be retrieved with the same
        states and initial_state as present at freezing time.

        This allows reading states that no longer exist in the workflow.


.. class:: WorkflowEnabled(models.Model)

    This class inherits from Django's :class:`~django.db.models.Model` class, performing
    some transformations on the subclass: each ``attr = StateField(SomeWorkflow, ...)``
    attribute will enable XWorkflows' transition detection and wrapping.

    Most of this job is performed through :class:`WorkflowEnabledMeta`.

    .. method:: _get_FIELD_display(self, field)

        This method overrides the default django one to retrieve the
        :attr:`~xworkflows.base.State.title` from a :class:`StateField` field.


Transitions
===========

Transitions mostly follow XWorkflows' mechanism.

.. class:: TransactionalImplementationWrapper(xworkflows.base.ImplementationWrapper)

    This specific wrapper runs all transition-related code
    (:attr:`transition_check hooks <xworkflows.transition_check>`,
    :attr:`before_transition hooks <xworkflows.before_transition>`,
    implementation,
    :attr:`~xworkflows.base.Workflow.log_transition`,
    :attr:`after_transition hooks <xworkflows.after_transition>`) in a single database transaction.


The :class:`TransactionalImplementationWrapper` can be enabled by setting it to
the :attr:`~xworkflows.Workflow.implementation_class` attribute of a :class:`xworkflows.Workflow` or
of a :class:`Workflow`::

    class MyWorkflow(models.Workflow):
        implementation_class = models.TransactionalImplementationWrapper


.. class:: Workflow(xworkflows.Workflow)

    This :class:`xworkflows.Workflow` subclass performs a few customization:

    - Logging transition logs in database
    - Saving updated objects after the transition


    .. attribute:: log_model

        This holds the model to use to log to the database.
        If empty, no database logging is performed.


    .. method:: db_log(self, transition, from_state, instance, user=None, *args, **kwargs)

        .. fix VIM coloring **

        Logs the transition into the database, saving the following elements:

        - Name of the transition
        - Name of the initial state
        - :class:`~django.contrib.contenttypes.generic.GenericForeignKey` to the
          modified instance
        - :class:`~django.db.models.ForeignKey` to the user responsible for the transition
        - timestamp of the operation

        The default :class:`BaseTransitionLog` model is :class:`django_xworkflows.xworkflow_log.models.TransitionLog`,
        but an alternative one can be specified in :attr:`log_model`.

        .. hint:: Override this method to log to a custom :class:`BaseTransitionLog` without generic foreign keys.


    .. method:: log_transition(self, transition, from_state, instance, save=True, log=True, *args, **kwargs)

        .. fix VIM coloring **

        In addition to :func:`xworkflows.Workflow.log_transition`, additional actions are performed:

        - If :attr:`save` is ``True``, the instance is saved.
        - If :attr:`log` is ``True``, the :func:`db_log` method is called to register the
          transition in the database.


Transition logs
===============


.. class:: BaseTransitionLog

    This abstract model describes which fields are expected when logging a transition to the database.

    The default for all :class:`WorkflowEnabled` subclasses will be to log to
    :class:`django_xworkflows.xworkflow_log.models.TransitionLog` instances.

    This behaviour can be altered by setting the :attr:`~Workflow.log_model` attribute of :class:`Workflow` definition.

    .. attribute:: modified_object

        A :class:`~django.contrib.contenttypes.generic.GenericForeignKey` to the :class:`WorkflowEnabled` being modified.

    .. attribute:: transition

        The name of the transition performed

        :type: str

    .. attribute:: from_state

        The name of the source state for the transition

        :type: str

    .. attribute:: to_state

        The name of the destination state for the transition

        :type: str

    .. attribute:: timestamp

        The time at which the transition occurred.

        :type: datetime.datetime



.. module:: django_xworkflows.xworkflow_log.models
    :synopsis: Keep an example :class:`~django_xworkflows.models.BaseTransitionLog` model,
      with admin and translations.

An example :class:`~django_xworkflows.models.BaseTransitionLog` model is available in the ``django_xworkflows.xworkflow_log`` application.
Including it to :attr:`~django.conf.settings.INSTALLED_APPS` will enable database
logging of transitions for all :class:`~django_xworkflows.models.WorkflowEnabled` subclasses.

.. class:: TransitionLog(BaseTransitionLog)

    This specific :class:`~django_xworkflows.models.BaseTransitionLog` also stores the user responsible for the
    transition, if provided.

    The exact :class:`~django.db.models.Model` to use for that foreign key can be set
    in the :const:`XWORKFLOWS_USER_MODEL` setting (defaults to ``'auth.User'``, which
    uses :class:`django.contrib.auth.models.User`).


Internals
=========


.. note:: These classes are private API.

.. currentmodule:: django_xworkflows.models

.. class:: WorkflowEnabledMeta(xworkflows.base.WorkflowEnabledMeta)

    This metaclass is responsible for parsing a class definition, detecting all
    :class:`StateField` and collecting/defining the associated :class:`TransactionalImplementationWrapper`.

    .. method:: _find_workflows(mcs, attrs)

        Collect all :class:`StateField` from the given :attr:`attrs` (the default version
        collects :class:`Workflow` subclasses instead)

    .. method:: _add_workflow(mcs, field_name, state_field, attrs)

        Perform necessay actions to register the :class:`Workflow` stored in
        a :class:`StateField` defined at :attr:`field_name` into the given
        attributes dict.

        It differs from the base implementation which adds a
        :class:`~xworkflows.base.StateProperty` instead of keeping the :class:`StateField`.

        :param str field_name: The name of the attribute at which the :class:`StateField` was defined
        :param state_field: The :class:`StateField` wrapping the :class:`Workflow`
        :type state_field: :class:`StateField`
        :param dict attrs: The attributes dictionary to update.
