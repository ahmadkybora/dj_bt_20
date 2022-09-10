from django.db import models
from django.forms import CharField

# Create your models here.

class User(models.Model):
    user_id = CharField
    username = CharField
    language = CharField
    number_of_files_sent = CharField

# class Admin(models.Model):
#     admin_user_id = CharField
#     is_owner = CharField