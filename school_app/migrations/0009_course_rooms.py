# Generated by Django 2.2.6 on 2019-11-29 17:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('school_app', '0008_assignedtocourse_confirmed'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='rooms',
            field=models.ManyToManyField(related_name='course_room', to='school_app.Room'),
        ),
    ]