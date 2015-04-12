from django.db import models
from django_xworkflows import models as xwf_models


class ProjectWorkflow(xwf_models.Workflow):
    initial_state = 'new'
    states = [
        ('new', u"New"),
        ('developing', u"Developing"),
        ('review', u"Review"),
        ('done', u"Done"),
        ('cancelled', u"Cancelled"),
    ]

    transitions = [
        ('start_developing', 'new', 'developing'),
        ('end_developing', 'developing', 'review'),
        ('approve', 'review', 'done'),
        ('reject', 'review', 'developing'),
        ('cancel', ['new', 'developing', 'review'], 'cancelled'),
    ]


class Project(xwf_models.WorkflowEnabled, models.Model):
    name = models.CharField(max_length=100)
    state = xwf_models.StateField(ProjectWorkflow)

