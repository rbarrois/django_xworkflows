=================
Library internals
=================

.. module:: django_xworkflows
    :synopsis: XWorkflows bindings for Django

This page documents the internal mechanisms of django_xworkflows.

Binding to a workflow
---------------------

The mechanism to bind a django model to a :class:`xworkflows.Workflow` relies on the :class:`WorkflowEnabled` and :class:`StateField` classes.


.. class:: StateField(django.models.Field)

    This class is a simple Django :class:`~django.models.Field`, specifically tuned for a
    :class:`Workflow`.

    It is internally backed by a :class:`~django.models.CharField`
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


.. class:: WorkflowEnabledMeta(xworkflows.base.WorkflowEnabledMeta)

    .. note:: This is a private API

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


Transitions
===========

Transitions mostly follow XWorkflows' mechanism.

.. class:: TransactionalImplementationWrapper(xworkflows.base.ImplementationWrapper)

    This specific wrapper runs all transition-related code
    (:attr:`~xworkflows.base.ImplementationWrapper.check`,
    :attr:`~xworkflows.base.ImplementationWrapper.before`,
    implementation,
    :attr:`~xworkflows.base.Workflow.log_transition`,
    :attr:`~xworkflows.base.ImplementationWrapper.after`) in a single database transaction.


The :class:`TransactionalImplementationWrapper` can be enabled either by setting it to
the :attr:`~xworkflows.base.Workflow.implementation_class` attribute of a simple :class:`xworkflows.Workflow`,
or by using the django-specific :class:`Workflow`.


.. class:: Workflow(xworkflows.Workflow)

    This :class:`xworkflows.Workflow` subclass performs a few customization:

    - Using :class:`TransactionalImplementationWrapper` to run transitions in a transaction
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

        The default :class:`TransitionLog` model is :class:`xworkflow_log.models.TransitionLog`,
        but an alternative one can be specified in :attr:`log_model`.

        .. hint:: Override this method to log to a custom TransitionLog without generic foreign keys.


.. class:: xworkflow_log.models.TransitionLog(BaseTransitionLog)

    This specific :class:`TransitionLog` also stores the user responsible for the
    transition, if provided.

    The exact :class:`~django.db.models.Model` to use for that foreign key can be set
    in the :const:`XWORKFLOWS_USER_MODEL` setting (defaults to ``'auth.User'``, which
    uses :class:`django.contrib.auth.models.User`).
