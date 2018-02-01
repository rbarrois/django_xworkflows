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


# Note: Some of the lines below end with a 'step:x,y,z' comment.
# This comment marks that the line should only be included at migration
# emulation step x, y and z.


class Author(models.Model):                                         # step:2,3,4,5
    name = models.CharField(max_length=100)                         # step:2,3,4,5


class Project(xwf_models.WorkflowEnabled, models.Model):
    name = models.CharField(max_length=100)
    state = xwf_models.StateField(ProjectWorkflow)
    author = models.OneToOneField(                                  # step:2,3,4,5
        Author, null=True, on_delete=models.CASCADE)                # step:2,3,4,5


class SubProject(xwf_models.WorkflowEnabled, models.Model):         # step:3,4,5
    name = models.CharField(max_length=100)                         # step:3,4,5
    project = models.ForeignKey(Project, on_delete=models.CASCADE)  # step:3,4,5
    state = xwf_models.StateField(ProjectWorkflow)                  # step:4,5


class MetaProject(xwf_models.WorkflowEnabled, models.Model):        # step:5
    name = models.CharField(max_length=100)                         # step:5
    state = xwf_models.StateField(ProjectWorkflow)                  # step:5


class MetaNote(models.Model):                                           # step:5
    project = models.ForeignKey(MetaProject, on_delete=models.CASCADE)  # step:5
