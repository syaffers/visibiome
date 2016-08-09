from StringIO import StringIO
from app.models import BiomSearchJob
from biom import parse_table, load_table
from biom.exception import TableException
from darp.celery import app
from time import sleep


@app.task
def validate_input(job_id, input_str, input_type):
    """
    Async task to perform validation of input files/text. This function checks
    whether the input is a valid OTU table or BIOM file by parsing the input
    file/text. If it fails then chances are it is not a valid OTU table or
    BIOM file. If it succeeds, the function then checks if there is exactly
    one sample in the valid OTU table of BIOM file.
    """
    job = BiomSearchJob.objects.filter(id=job_id).first()
    try:
        if input_type == 1:
            str_stream = StringIO(input_str)
            otu_table = parse_table(str_stream)
        else:
            otu_table = load_table(input_str)

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

    except IOError:
        job.status = BiomSearchJob.STOPPED
        job.error_code = BiomSearchJob.FILE_IO_ERROR
        job.save()
        return False

    except TableException:
        job.status = BiomSearchJob.STOPPED
        job.error_code = BiomSearchJob.DUPLICATE_ID_ERROR
        job.save()
        return False

    except (IndexError, TypeError, ValueError):
        job.status = BiomSearchJob.STOPPED
        job.error_code = BiomSearchJob.FILE_VALIDATION_ERROR
        job.save()
        return False


@app.task
def simulate_task(job_id):
    j = BiomSearchJob.objects.filter(id=job_id).first()
    j.status = BiomSearchJob.PROCESSING
    j.save()
    sleep(60) # basically doing some tasks here
    j.status = BiomSearchJob.COMPLETED
    j.save()
