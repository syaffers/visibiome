from StringIO import StringIO
from app.models import BiomSearchJob
from biom import parse_table
from biom.exception import TableException
from darp.celery import app
from time import sleep


@app.task
def validate_input(job_id, text, input_type):
    job = BiomSearchJob.objects.filter(id=job_id).first()
    try:
        if input_type == 1:
            str_stream = StringIO(text)
            otu_table = parse_table(str_stream)
        else:
            otu_table = parse_table(open(text))

        if len(otu_table.ids()) == 1:
            job.status = BiomSearchJob.QUEUED
            job.save()
            simulate_task.delay(job.id)
            return True
        else:
            job.status = BiomSearchJob.STOPPED
            job.error_code = BiomSearchJob.SAMPLE_COUNT_ERROR
            job.save()
            return False

    except TableException:
        job.status = BiomSearchJob.STOPPED
        job.error_code = BiomSearchJob.DUPLICATE_ID_ERROR
        job.save()
        return False

    except IndexError:
        job.status = BiomSearchJob.STOPPED
        job.error_code = BiomSearchJob.FILE_VALIDATION_ERROR
        job.save()
        return False

    except ValueError:
        job.status = BiomSearchJob.STOPPED
        job.error_code = BiomSearchJob.FILE_VALIDATION_ERROR
        job.save()
        return False


@app.task
def simulate_task(job_id):
    j = BiomSearchJob.objects.filter(id=job_id).first()
    sleep(60)
    j.status = BiomSearchJob.COMPLETED
    j.save()
