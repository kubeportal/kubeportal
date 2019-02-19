from django.db import models

class Cluster(models.Model):
    name = models.CharField(max_length=10)
    url = models.CharField(max_length=100)

    class Meta:
        permissions = (
            ('access', 'Can access cluster API'),
            )
