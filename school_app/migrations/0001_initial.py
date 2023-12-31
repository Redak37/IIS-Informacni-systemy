# Generated by Django 2.2.6 on 2019-10-21 12:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Course',
            fields=[
                ('abbrev', models.CharField(max_length=4, primary_key=True, serialize=False)),
                ('description', models.CharField(max_length=512)),
                ('price', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='CourseType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('courseType', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Equipment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.CharField(max_length=512)),
                ('cost', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Permission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Room',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address', models.CharField(max_length=255)),
                ('doorNumber', models.IntegerField()),
                ('capacity', models.IntegerField(default=1)),
            ],
        ),
        migrations.CreateModel(
            name='RoomType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('roomType', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tag', models.CharField(max_length=32)),
                ('description', models.CharField(max_length=512)),
            ],
        ),
        migrations.CreateModel(
            name='TypeOfTerm',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('termType', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('login', models.CharField(max_length=8, primary_key=True, serialize=False)),
                ('firstName', models.CharField(max_length=255)),
                ('lastName', models.CharField(max_length=255)),
                ('email', models.CharField(max_length=255)),
                ('phone', models.CharField(max_length=255)),
                ('password', models.CharField(max_length=255)),
                ('permission', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='school_app.Permission')),
            ],
        ),
        migrations.CreateModel(
            name='Term',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.CharField(max_length=512)),
                ('points', models.IntegerField(default=0)),
                ('date', models.DateTimeField()),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='school_app.Course')),
                ('lecturer', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='school_app.User')),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='school_app.Room')),
                ('termType', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='school_app.TypeOfTerm')),
            ],
        ),
        migrations.CreateModel(
            name='RoomEquipment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('count', models.IntegerField(default=1)),
                ('equipment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='school_app.Equipment')),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='school_app.Room')),
            ],
        ),
        migrations.AddField(
            model_name='room',
            name='roomType',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='school_app.RoomType'),
        ),
        migrations.CreateModel(
            name='CourseTags',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('TagID', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='school_app.Tag')),
                ('abbrev', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='school_app.Course')),
            ],
        ),
        migrations.AddField(
            model_name='course',
            name='courseType',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='school_app.CourseType'),
        ),
        migrations.AddField(
            model_name='course',
            name='garant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='school_app.User'),
        ),
        migrations.CreateModel(
            name='AssignedToCourse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='school_app.Course')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='school_app.User')),
            ],
        ),
    ]
