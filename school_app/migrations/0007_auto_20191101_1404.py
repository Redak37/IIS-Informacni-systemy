# Generated by Django 2.2.6 on 2019-11-01 13:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('school_app', '0006_course_confirmed'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='lecturers',
            field=models.ManyToManyField(blank=True, related_name='lecturers', to='school_app.User'),
        ),
        migrations.AlterField(
            model_name='course',
            name='garant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='garant', to='school_app.User'),
        ),
    ]
