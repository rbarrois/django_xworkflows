# -*- coding: utf-8 -*-
# Copyright (c) 2011-2012 Raphaël Barrois

"""Rebuild missing from_state/to_state fields on TransitionLog objects."""


from django.contrib.contenttypes import models as ctype_models
from django.core.management import base
from django.db import models


class Command(base.LabelCommand):
    args = "<app.Model> <app.Model> ..."
    help = "Rebuild TransitionLog from_state/to_state fields for selected models."

    def handle_label(self, label, **options):
        self.stdout.write('Rebuilding TransitionLog states for %s\n' % label)

        app_label, model_label = label.rsplit('.', 1)
        model = models.get_model(app_label, model_label)

        if not hasattr(model, '_workflows'):
            raise base.CommandError("Model %s isn't attached to a workflow." % label)

        for field_name, state_field in model._workflows.items():
            self._handle_field(label, model, field_name, state_field.workflow, **options)

    def _handle_field(self, label, model, field_name, workflow, **options):
        if not hasattr(workflow, 'log_model') or not workflow.log_model:
            raise base.CommandError("Field %s of %s does not log to a model." % (field_name, label))

        log_model = workflow._get_log_model_class()
        model_type = ctype_models.ContentType.objects.get_for_model(model)
        verbosity = int(options.get('verbosity', 1))

        if verbosity:
            self.stdout.write('%r.%s: ' % (model, field_name))

        for pk in model.objects.order_by('pk').values_list('pk', flat=True):
            previous_state = workflow.initial_state

            qs = (log_model.objects.filter(content_type=model_type, content_id=pk)
                                   .order_by('timestamp'))
            if verbosity >= 2:
                self.stdout.write('\n  %d:' % pk)

            for log in qs:
                try:
                    transition = workflow.transitions[log.transition]
                except KeyError:
                    self.stderr.write(u"Unknown transition %s in log %d for %s %d\n" % (log.transition, log.pk, label, pk))
                    continue

                updated = False
                if not log.from_state:
                    log.from_state = previous_state
                    updated = True
                if not log.to_state:
                    log.to_state = workflow.transitions[log.transition].target
                    updated = True

                previous_state = log.to_state
                if updated:
                    log.save()
                    if verbosity:
                        self.stdout.write('.')

        if verbosity:
            self.stdout.write('\n')
