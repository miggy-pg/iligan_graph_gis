# Generated by Django 4.2.2 on 2023-06-13 23:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('map', '0005_alter_marker_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='RoadIntersection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=35)),
                ('longitude', models.CharField(max_length=30)),
                ('latitude', models.CharField(max_length=30)),
            ],
        ),
    ]
