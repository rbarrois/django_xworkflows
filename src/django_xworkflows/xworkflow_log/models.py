# -*- coding: utf-8 -*-
# Copyright (c) 2011-2012 Raphaël Barrois

from django.conf import settings
from django.db import models as django_models
from django.utils.translation import ugettext_lazy as _

from .. import models


class TransitionLog(models.GenericTransitionLog):
    """The log for a transition.

    Attributes:
        modified_object (django.db.model.Model): the object affected by this
            transition.
        from_state (str): the name of the origin state
        to_state (str): the name of the destination state
        transition (str): The name of the transition being performed.
        timestamp (datetime): The time at which the Transition was performed.
        user (django.contrib.auth.user): the user performing the transition; the
            actual model to use here is defined in the XWORKFLOWS_USER_MODEL
            setting.
    """
    # Additional keyword arguments to store, if provided
    EXTRA_LOG_ATTRIBUTES = (
        ('user', 'user', None),  # Store the 'user' kwarg to transitions.
    )

    user = django_models.ForeignKey(
        getattr(settings, 'XWORKFLOWS_USER_MODEL', 'auth.User'),
        blank=True, null=True, verbose_name=_(u"author"))
