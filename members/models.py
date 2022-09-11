from django.db import models

# Create your models here.
class User(models.Model):

    user_id = models.CharField(max_length=200, verbose_name="آی دی")
    username = models.CharField(max_length=200, verbose_name="نام کاربری")
    language = models.CharField(max_length=200, verbose_name="زبان")
    number_of_files_sent = models.CharField(max_length=200, verbose_name="تعداد ارسال فایل")

    def __str__(self) -> str:
        return "%s %s" % (self.first_name, self.last_name)

    def getAll(self):
        return self.objects.all()

    def create(self, data=[]):
        self.objects.create(data)
        return self.save()

    def getById(self, data):
        return self.objects.get(data=data)

    def ascOrdesc(self, data):
        return self.objects.all().orderby(data)

# class Admin(models.Model):
#     admin_user_id = CharField
#     is_owner = CharField