# -*- coding: utf-8 -*-
# Copyright (c) 2011-2012 Raphaël Barrois

from . import models

from django.contrib import admin


class TransitionLogAdmin(admin.ModelAdmin):
    actions = None
    date_hierarchy = 'timestamp'
    list_display = ('modified_object', 'transition', 'from_state', 'to_state', 'user', 'timestamp',)
    list_filter = ('content_type', 'transition',)
    read_only_fields = ('user', 'modified_object', 'transition', 'timestamp',)
    search_fields = ('transition', 'user__username',)

    def has_add_permission(self, request):
        return False

    # Allow viewing objects but not actually changing them
    def has_change_permission(self, request, obj=None):
        return request.method == 'GET'

    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register(models.TransitionLog, TransitionLogAdmin)
