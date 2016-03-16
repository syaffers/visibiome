import requests

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.forms.models import model_to_dict
from django.contrib.auth.models import User


def upload_path_handler(instance, filename):
    filename = filename.split('.')
    name, ext = filename[0:-1], filename[-1]
    file_path = 'uploads/{user_id}/{name}.{ext}'.format(
        user_id=instance.user_id, name=name, ext=ext)
    return file_path


class Guest(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    status = models.BooleanField(default=False)

    def __str__(self):
        is_or_is_not = "" if self.status else "not "
        return "{uname} is {is_or_is_not}a guest".format(
            uname=self.user.username, is_or_is_not=is_or_is_not)


class Job(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    result = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def set_result(self, result):
        self.result = result


class BiomSearchJob(models.Model):
    user = models.ForeignKey(User)
    completed = models.BooleanField(default=False)
    criteria = models.CharField(default="all", max_length=200)
    input_file = models.FileField(
        default=None, upload_to=upload_path_handler)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def set_result(self, result):
        self.result = result


@receiver(post_save, sender=Job, dispatch_uid="job_post_save")
def notify_job_update(sender, instance, **kwargs):
    requests.post("http://127.0.0.1/notify", json={
        'topic': 'job.' + str(instance.id),
        'args': [model_to_dict(instance)]
    })
