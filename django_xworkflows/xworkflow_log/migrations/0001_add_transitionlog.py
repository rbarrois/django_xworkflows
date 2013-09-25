# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.conf import settings
from django.db import connection
from django.db import models


XWORKFLOWS_USER_MODEL = getattr(settings, 'XWORKFLOWS_USER_MODEL',
    getattr(settings, 'AUTH_USER_MODEL', 'auth.User'))

class Migration(SchemaMigration):

    def forwards(self, orm):

        if 'django_xworkflows_transitionlog' in connection.introspection.table_names():
            db.rename_table('django_xworkflows_transitionlog', 'xworkflow_log_transitionlog')
        else:
            # Adding model 'TransitionLog'
            db.create_table('xworkflow_log_transitionlog', (
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='workflow_object', null=True, to=orm['contenttypes.ContentType'])),
                ('content_id', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
                ('transition', self.gf('django.db.models.fields.CharField')(max_length=255)),
                ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm[XWORKFLOWS_USER_MODEL], null=True, blank=True)),
                ('timestamp', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ))

        db.send_create_signal('xworkflow_log', ['TransitionLog'])


    def backwards(self, orm):
        # Deleting model 'TransitionLog'
        db.delete_table('xworkflow_log_transitionlog')


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
            'Meta': {'ordering': "('-timestamp', 'user', 'transition')", 'object_name': 'TransitionLog'},
            'content_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'workflow_object'", 'null': 'True', 'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'transition': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['%s']" % XWORKFLOWS_USER_MODEL, 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['xworkflow_log']
