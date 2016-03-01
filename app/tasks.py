from darp.celery import app
from app import models


def fibs(x):
    if x == 0 or x == 1:
        return x
    return fibs(x - 1) + fibs(x - 2)


@app.task
def run_fibs(job_id, x):
    j = models.Job.objects.filter(id=job_id).first()
    j.set_result(fibs(x))
    j.set_completed(True)
    j.save()
