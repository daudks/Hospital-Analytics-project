from django.db import models

class Dataset(models.Model):
    # Your fields here
    name = models.CharField(max_length=100)
    # Other fields...