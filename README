Django-XWorkflows
=================

Use `XWorkflows <http://github.com/rbarrois/xworkflows/>`_ along with Django models.

Django-XWorkflows allow to bind a Django model to a workflow, with a few extra features:

- Auto-save after transitions
- Log each action into the database

Define a workflow and add it to a model::

    from django_xworkflows import models as xwf_models

    class MyWorkflow(xwf_models.Workflow):
        states = (
            ('new', _(u"New")),
            ('old', _(u"Old")),
        )
        transitions = (
            ('get_old', 'new', 'old'),
        )
        initial_state = 'new'

    class MyModel(xwf_models.WorkflowEnabled):

        state = xwf_models.StateField(MyWorkflow)

Use the workflow::

    >>> obj = MyModel()
    >>> obj.state  # Defaults to the initial_state
    State('new')
    >>> # Perform a transition
    >>> obj.get_old()
    >>> obj.state
    State('old')
    >>> # Object was saved to the database
    >>> obj.pk
    1
    >>> # Logs were saved to the database
    >>> xwf_models.TransitionLog.objects.all()
    [TransitionLog(MyModel: new -> old at 2012-04-14T12:10:00+0200)]

Links
-----

* Package on PyPI: http://pypi.python.org/pypi/django-xworkflows
* Repository and issues on GitHub: http://github.com/rbarrois/django_xworkflows
* Doc on http://readthedocs.org/docs/django-xworkflows/
* XWorkflows on GitHub: http://github.com/rbarrois/xworkflows
