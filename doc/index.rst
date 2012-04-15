Welcome to django-xworkflows's documentation!
=============================================

django-xworkflows is a django application adding xworkflows functionnalities to
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

    from django_xworkflows import models as xwf_models

    class MyModel(xwf_models.WorkflowEnabled):

        state = MyWorkflow()


Contents
========

.. toctree::
   :maxdepth: 2

   django
   xworkflow_log
   internals

Resources
=========

* Package on PyPI: http://pypi.python.org/pypi/django-xworkflows
* Repository and issues on GitHub: http://github.com/rbarrois/django-xworkflows
* Doc on http://readthedocs.org/doc/django-xworkflows/
* XWorkflows on GitHub: http://github.com/rbarrois/xworkflows

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

