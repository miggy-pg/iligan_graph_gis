# Generated by Django 4.2.2 on 2023-06-12 08:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('map', '0004_rename_weight_marker_category_level'),
    ]

    operations = [
        migrations.AlterField(
            model_name='marker',
            name='name',
            field=models.CharField(max_length=35),
        ),
    ]
