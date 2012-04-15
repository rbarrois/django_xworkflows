# -*- coding: utf-8 -*-
# Copyright (c) 2011-2012 Raphaël Barrois

import datetime

from django.conf import settings
from django.contrib.contenttypes import generic
from django.contrib.contenttypes import models as ct_models
from django.db import models
from django.utils.translation import ugettext_lazy as _


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
    from_state = models.CharField(_(u"from state"), max_length=255)
    to_state = models.CharField(_(u"to state"), max_length=255)
    user = models.ForeignKey(
        getattr(settings, 'XWORKFLOWS_USER_MODEL', 'auth.User'),
        blank=True, null=True, verbose_name=_(u"author"))
    timestamp = models.DateTimeField(_(u"performed at"), default=datetime.datetime.now)

    class Meta:
        ordering = ('-timestamp', 'user', 'transition')
        verbose_name = _(u'XWorkflow transition log')
        verbose_name_plural = _(u'XWorkflow transition logs')

    def __unicode__(self):
        return u'%r: %s -> %s at %s' % (self.modified_object, self.from_state,
            self.to_state, self.timestamp.isoformat())
