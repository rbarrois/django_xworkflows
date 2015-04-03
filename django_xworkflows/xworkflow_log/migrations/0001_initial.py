# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TransitionLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('transition', models.CharField(max_length=255, verbose_name='transition', db_index=True)),
                ('from_state', models.CharField(max_length=255, verbose_name='from state', db_index=True)),
                ('to_state', models.CharField(max_length=255, verbose_name='to state', db_index=True)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now, verbose_name='performed at', db_index=True)),
                ('content_id', models.PositiveIntegerField(db_index=True, null=True, verbose_name='Content id', blank=True)),
                ('content_type', models.ForeignKey(verbose_name='Content type', blank=True, to='contenttypes.ContentType', null=True)),
                ('user', models.ForeignKey(verbose_name='author', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ('-timestamp', 'transition'),
                'abstract': False,
                'verbose_name': 'XWorkflow transition log',
                'verbose_name_plural': 'XWorkflow transition logs',
            },
            bases=(models.Model,),
        ),
    ]
