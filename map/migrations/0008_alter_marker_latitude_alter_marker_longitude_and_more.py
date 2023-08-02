# Generated by Django 4.2.2 on 2023-06-18 14:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('map', '0007_delete_roadintersection_marker_type_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='marker',
            name='latitude',
            field=models.FloatField(max_length=30),
        ),
        migrations.AlterField(
            model_name='marker',
            name='longitude',
            field=models.FloatField(max_length=30),
        ),
        migrations.AlterField(
            model_name='marker',
            name='type',
            field=models.CharField(choices=[(None, 'Select the type'), ('establishment', 'Establishment'), ('intersection', 'Intersection'), ('start_dest', 'Start/Destination')], default='establishment', max_length=14),
        ),
    ]