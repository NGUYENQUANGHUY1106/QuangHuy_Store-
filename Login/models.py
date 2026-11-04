from django.db import models

# Create your models here.

class User(models.Model) :
    username  = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=10)
    avatar = models.FileField()
    password = models.CharField(max_length=200)

    class Meta :
        db_table = 'user'