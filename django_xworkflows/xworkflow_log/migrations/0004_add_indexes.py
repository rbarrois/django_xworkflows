# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.conf import settings
from django.db import models


XWORKFLOWS_USER_MODEL = getattr(settings, 'XWORKFLOWS_USER_MODEL',
    getattr(settings, 'AUTH_USER_MODEL', 'auth.User'))

class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding index on 'TransitionLog', fields ['from_state']
        db.create_index('xworkflow_log_transitionlog', ['from_state'])

        # Adding index on 'TransitionLog', fields ['to_state']
        db.create_index('xworkflow_log_transitionlog', ['to_state'])

        # Adding index on 'TransitionLog', fields ['timestamp']
        db.create_index('xworkflow_log_transitionlog', ['timestamp'])

        # Adding index on 'TransitionLog', fields ['transition']
        db.create_index('xworkflow_log_transitionlog', ['transition'])

        # Adding index on 'TransitionLog', fields ['content_id']
        db.create_index('xworkflow_log_transitionlog', ['content_id'])


    def backwards(self, orm):
        # Removing index on 'TransitionLog', fields ['content_id']
        db.delete_index('xworkflow_log_transitionlog', ['content_id'])

        # Removing index on 'TransitionLog', fields ['transition']
        db.delete_index('xworkflow_log_transitionlog', ['transition'])

        # Removing index on 'TransitionLog', fields ['timestamp']
        db.delete_index('xworkflow_log_transitionlog', ['timestamp'])

        # Removing index on 'TransitionLog', fields ['to_state']
        db.delete_index('xworkflow_log_transitionlog', ['to_state'])

        # Removing index on 'TransitionLog', fields ['from_state']
        db.delete_index('xworkflow_log_transitionlog', ['from_state'])


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        XWORKFLOWS_USER_MODEL.lower(): {
            'Meta': {'object_name': XWORKFLOWS_USER_MODEL.split('.')[1]},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'xworkflow_log.transitionlog': {
            'Meta': {'ordering': "('-timestamp', 'transition')", 'object_name': 'TransitionLog'},
            'content_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'workflow_object'", 'null': 'True', 'to': "orm['contenttypes.ContentType']"}),
            'from_state': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'db_index': 'True'}),
            'to_state': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'transition': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['%s']" % XWORKFLOWS_USER_MODEL, 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['xworkflow_log']
