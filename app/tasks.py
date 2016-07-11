from darp.celery import app
from app.models import BiomSearchJob
from time import sleep


@app.task
def simulate_task(job_id):
    j = BiomSearchJob.objects.filter(id=job_id).first()
    sleep(60)
    j.completed = True
    j.save()
