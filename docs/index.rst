django-xworkflows documentation
===============================

django-xworkflows is a django application adding `xworkflows <http://github.com/rbarrois/xworkflows/>`_ functionnalities to
django models.


Getting started
===============

First, install the required packages::

    pip install django-xworkflows

In your ``settings.py``, add ``django_xworkflows`` to your :py:obj:`INSTALLED_APPS`::

    INSTALLED_APPS = (
        '...',
        'django_xworkflows',
    )

Define a workflow::

    from django_xworkflows import models as xwf_models

    class MyWorkflow(xwf_models.Workflow):
        log_model = ''  # Disable logging to database

        states = (
            ('new', _(u"New")),
            ('old', _(u"Old")),
        )
        transitions = (
            ('get_old', 'new', 'old'),
        )
        initial_state = 'new'

And add it to a model::

    from django import models
    from django_xworkflows import models as xwf_models

    class MyModel(xwf_models.WorkflowEnabled, models.Model):

        state = xwf_models.StateField(MyWorkflow)

The :attr:`state` field of :class:`MyModel` is now defined as a :class:`django.db.models.CharField`,
whose :attr:`choices` and :attr:`default` are configured according to the related
:class:`django_xworkflows.models.Workflow`.


Integration with django
=======================

After each successful transition, a :func:`save()` is performed on the object.
This behaviour is controlled by passing the extra argument ``save=False`` when calling the transition method.

If the :class:`~django_xworkflows.models.Workflow` has a definition for the :attr:`~django_xworkflows.models.Workflow.log_model` attribute (as a ``<app>.<Model>`` string),
an instance of that model will be created for each successful transition.

If the :mod:`django_xworkflows.xworkflow_log` application is installed,
:attr:`~django_xworkflows.models.Workflow.log_model` defaults to
:class:`~django_xworkflows.xworkflow_log.models.TransitionLog`.
Otherwise, it defaults to ``''`` (db logging disabled).

This behaviour can be altered by:

* Setting the :attr:`~django_xworkflows.models.Workflow.log_model` attribute to ``''``
* Calling the transition method with ``log=False`` (no logging to database)
* Overriding the :func:`~django_xworkflows.models.Workflow.db_log` method of the :class:`~django_xworkflows.models.Workflow`.
* Overriding the :func:`~django_xworkflows.models.Workflow.log_transition`
  method of the :class:`~django_xworkflows.models.Workflow`; this controls both ``log`` and ``save`` behaviours.


Contents
========

.. toctree::
   :maxdepth: 2

   internals
   changelog

Resources
=========

* Package on PyPI: http://pypi.python.org/pypi/django-xworkflows
* Repository and issues on GitHub: http://github.com/rbarrois/django_xworkflows
* Doc on https://django-xworkflows.readthedocs.io/
* XWorkflows on GitHub: http://github.com/rbarrois/xworkflows
* XWorkflows doc on https://xworkflows.readthedocs.io/

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

