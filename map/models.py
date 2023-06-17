from django.db import models

NODE_TYPE = (
    (None, 'Select the type'),
    ('establishment', 'Establishment'),
    ('intersection', 'Intersection'),
    ('start_dest', 'Start/Destination'),
)

class Marker(models.Model):
    name = models.CharField(blank=False, null=True, max_length=35)
    type = models.CharField(blank=False, max_length=14, default='establishment', choices=NODE_TYPE)
    longitude = models.CharField(blank=False, max_length=30)
    latitude = models.CharField(blank=False, max_length=30)
    category_level = models.IntegerField(blank=False, default=0)


    def __str__(self):
        return self.name
    
    def __unicode__(self):
        return self.name
    
