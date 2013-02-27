=================
Library internals
=================

.. module:: django_xworkflows.models
    :synopsis: XWorkflows bindings for Django

This page documents the internal mechanisms of django_xworkflows.

Binding to a workflow
=====================

The mechanism to bind a django model to a :class:`xworkflows.Workflow` relies on the :class:`WorkflowEnabled` and :class:`StateField` classes.


.. class:: StateField(django.db.models.Field)

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

Implementation wrappers
-----------------------

django_xworkflows provides two custom implementation wrappers specially suited for Django:

.. class:: DjangoImplementationWrapper(xworkflows.base.ImplementationWrapper)

    This wrapper simply adds two special attributes for interpretation in Django templates:

    .. attribute:: alters_data

        Set to ``True`` to prevent Django templating system to call a transition, e.g in
        ``{{ foo.confirm }}``

    .. attribute:: do_not_call_in_templates

        This attribute signals Django templating system (starting from Django 1.4)
        that the transition implementation should not be called, but its attributes
        should be made available.

        This allows such constructs:

        .. code-block:: html

            {% if obj.confirm.is_available %}
            <form method="POST" action="">
                <input type="submit" value="Confirm" />
            </form>
            {% endif %}


.. class:: TransactionalImplementationWrapper(DjangoImplementationWrapper)

    This specific wrapper runs all transition-related code, including :class:`hooks <xworkflows.base.Hook>`,
    in a single database transaction.


The :class:`TransactionalImplementationWrapper` can be enabled by setting it to
the :attr:`~xworkflows.Workflow.implementation_class` attribute of a :class:`xworkflows.Workflow` or
of a :class:`Workflow`::

    class MyWorkflow(models.Workflow):
        implementation_class = models.TransactionalImplementationWrapper


Workflow and logging
--------------------

.. class:: Workflow(xworkflows.Workflow)

    This :class:`xworkflows.Workflow` subclass performs a few customization:

    - Logging transition logs in database
    - Saving updated objects after the transition


    .. attribute:: log_model

        This holds the name of the model to use to log to the database.
        If empty, no database logging is performed.


    .. attribute:: log_model_class

        This holds the class of the model to use to log to the database.

        Takes precedence over :attr:`log_model`. If this attribute is empty but
        :attr:`log_model` has been provided, it will be filled at first access.


    .. method:: db_log(self, transition, from_state, instance, *args, **kwargs)

        .. fix VIM coloring **

        Logs the transition into the database, saving the following elements:

        - Name of the transition
        - Name of the initial state
        - :class:`~django.contrib.contenttypes.generic.GenericForeignKey` to the
          modified instance
        - :class:`~django.db.models.ForeignKey` to the user responsible for the transition
        - timestamp of the operation

        The default :class:`TransitionLog <BaseTransitionLog>` model is :class:`django_xworkflows.xworkflow_log.models.TransitionLog`,
        but an alternative one can be specified in :attr:`log_model` or :attr:`log_model_class`.

        .. hint:: Override this method to log to a custom TransitionLog with complex fields and storage.


    .. method:: log_transition(self, transition, from_state, instance, save=True, log=True, *args, **kwargs)

        .. fix VIM coloring **

        In addition to :meth:`xworkflows.Workflow.log_transition`, additional actions are performed:

        - If :attr:`save` is ``True``, the instance is saved.
        - If :attr:`log` is ``True``, the :func:`db_log` method is called to register the
          transition in the database.


Transition database logging
===========================

Transition logs can be stored in the database. This is performed by the :meth:`~Workflow.db_log` method of the :class:`Workflow` class.

The default method will save informations about the transition into an adapted model.
The actual model to log will be:

- The model whose class is set to the :attr:`Workflow.log_model_class` attribute
- The model whose name (in an ``app_label.ModelClass`` format) is set to the :attr:`Workflow.log_model` attribute
- The :class:`django_xworkflows.xworkflow_log.models.TransitionLog` model if ``django_xworkflows.xworkflow_log``
  belongs to :data:`settings.INSTALLED_APPS <django.setting.INSTALLED_APPS>`
- Nothing if none of the above match

Such models are expected to have a few fields, a good basis for writing your own is to
inherit from either :class:`BaseTransitionLog` or :class:`GenericTransitionLog` (which provides a default storage through a :class:`~django.contrib.contenttypes.generic.GenericForeignKey`).

The :class:`BaseTransitionLog` class provides all required fields for logging a transition.


.. class:: BaseTransitionLog(models.Model)

    This class provides minimal functions for logging a transition to the database.

    .. attribute:: transition

        This attribute holds the name of the performed transition, as a string.

    .. attribute:: from_state

        Name of the source state, as a string.

    .. attribute:: to_state

        Name of the target state, as a string.

    .. attribute:: timestamp

        Timestamp of the operation, as a :class:`~django.db.models.DateTimeField`.


    .. attribute:: MODIFIED_OBJECT_FIELD

        Name of the field where the modified instance should be passed.
        Logging the transition will likely fail if this is not provided.

    .. attribute:: EXTRA_LOG_ATTRIBUTES

        It may be useful to log extra transition kwarg (``user``, ...) to the database.
        This attribute describes how to log those extra keyword arguments.

        It takes the form of a list of 3-tuples ``(db_field, kwarg, default)``.
        When logging to the database, the ``db_field`` attribute of the :class:`BaseTransitionLog` instance
        will be filled with the keyword argument passed to the transition at ``kwarg``, if
        any. Otherwise, ``default`` will be used.


    .. method:: get_modified_object(self)

        Abstract the lookup of the modified object through :attr:`MODIFIED_OBJECT_FIELD`.


    .. method:: log_transition(cls, transition, from_state, to_state, modified_object, **kwargs)

        .. Fix VIM coloring ***

        Save a new transition log from the given transition name, origin state name, target state name,
        modified object and extra fields.


.. class:: GenericTransitionLog(BaseTransitionLog)

    An extended version of :class:`BaseTransitionLog` uses a :class:`~django.contrib.contenttypes.generic.GenericForeignKey`
    to store the modified object.

    .. attribute:: content_type

        A foreign key to the :class:`~django.contrib.contenttypes.models.ContentType` of
        the modified object

    .. attribute:: content_id

        The primary key of the modified object

    .. attribute:: modified_object

        The :class:`~django.contrib.contenttypes.generic.GenericForeignKey` pointing to the
        modified object.


.. class:: BaseLastTransitionLog(BaseTransitionLog)

    This alternate :class:`BaseTransitionLog` has been tuned to store only the last transition log
    for an object, typically with a :class:`~django.db.models.OneToOneField`.

    It handles update or creation on its own.


.. class:: GenericLastTransitionLog(BaseLastTransitionLog)

    This class is to :class:`BaseLastTransitionLog` what :class:`GenericTransitionLog` is to :class:`BaseTransitionLog`.
    It holds the modified object through a :class:`~django.contrib.contenttypes.generic.GenericForeignKey`, with the
    adequate ``unique_together`` setting.


Here is an example of a custom ``TransitionLog`` model::

    # Note that we inherit from BaseTransitionLog, not GenericTransitionLog.
    class MyDocumentTransitionLog(django_xworkflows.models.BaseTransitionLog):

        # This is where we'll store the modified object
        document = models.ForeignKey(Document)

        # Extra data to keep about transitions
        user = models.ForeignKey(auth_models.User, blank=True, null=True)
        client = models.ForeignKey(api_models.Client, blank=True, null=True)
        source_ip = models.CharField(max_length=24, blank=True)

        # Set the name of the field where the modified object goes
        MODIFIED_OBJECT_FIELD = 'document'

        # Define extra logging attributes
        EXTRA_LOG_ATTRIBUTES = (
            ('user', 'user', None),
            ('client', 'api_client', None),  # Transitions are called with 'api_client' kwarg
            ('source_ip', 'ip', ''),  # Transitions are called with 'ip' kwarg
        )


.. module:: django_xworkflows.xworkflow_log.models
    :synopsis: Keep an example :class:`~django_xworkflows.models.BaseTransitionLog` model,
      with admin and translations.

An example :class:`TransitionLog` model is available in the ``django_xworkflows.xworkflow_log`` application.
Including it to :data:`settings.INSTALLED_APPS` will enable database
logging of transitions for all :class:`~django_xworkflows.models.WorkflowEnabled` subclasses.

.. class:: TransitionLog(GenericTransitionLog)

    This specific :class:`~django_xworkflows.models.GenericTransitionLog` also stores
    the user responsible for the transition, if provided.

    The exact :class:`~django.db.models.Model` to use for that foreign key can be set
    in the :const:`XWORKFLOWS_USER_MODEL` django setting (defaults to ``'auth.User'``, which
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
