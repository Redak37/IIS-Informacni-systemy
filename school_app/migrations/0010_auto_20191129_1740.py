# Generated by Django 2.2.6 on 2019-11-29 17:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('school_app', '0009_course_rooms'),
    ]

    operations = [
        migrations.AlterField(
            model_name='course',
            name='rooms',
            field=models.ManyToManyField(blank=True, related_name='course_room', to='school_app.Room'),
        ),
    ]
