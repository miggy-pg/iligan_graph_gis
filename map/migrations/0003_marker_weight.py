# Generated by Django 4.2.2 on 2023-06-12 06:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('map', '0002_rename_markername_marker_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='marker',
            name='weight',
            field=models.IntegerField(default=0),
        ),
    ]
