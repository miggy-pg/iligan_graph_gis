from django.db import models

NODE_TYPE = (
    (None, "Select the type"),
    ("establishment", "Establishment"),
    ("intersection", "Intersection"),
    ("start_dest", "Start/Destination"),
)


class Marker(models.Model):
    name = models.CharField(blank=True, null=True, max_length=35)
    type = models.CharField(
        blank=True, null=True, max_length=14, default="establishment", choices=NODE_TYPE
    )
    longitude = models.FloatField(blank=True, null=True, max_length=30)
    latitude = models.FloatField(blank=True, null=True, max_length=30)
    category_level = models.IntegerField(blank=True, null=True, default=0)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name
