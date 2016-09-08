from MySQLdb.cursors import DictCursor
from StringIO import StringIO
from app.models import BiomSearchJob
from betadiversity_scripts.JSon_metadata import create_json_samples_metadata
from betadiversity_scripts.MNBetadiversity import calculate_MNmatrix
from betadiversity_scripts.PCOA import pcoa
from betadiversity_scripts.config import server_db
from betadiversity_scripts.dendrogam_d3_json import json_for_dendrogam
from betadiversity_scripts.heatmap import (heatmap_files,
    get_sorted_representative_id)
from betadiversity_scripts.select_samples import (return_represent_sample,
    return_rep_original_samples)
from biom.parse import parse_biom_table
from biom import parse_table, load_table
from biom.exception import TableException
from vzb.celery import app
from django.conf import settings
from qiime import __version__ as qiime_ver
from time import sleep
import MySQLdb
import json
import numpy as np
import os
import re
import sys


@app.task
def validate_biom(job, file_path):
    """
    Async task to perform validation of input files/text. This function checks
    whether the input is a valid BIOM file by parsing the input file. If it
    fails then chances are it is not a valid BIOM file. If it succeeds, the
    function then checks if there is exactly one sample in the valid OTU table
    of BIOM file.

    :param job: BiomSearchJob object passed from search.py
    :param file_path: String containing file path to uploaded file
    """
    try:
        otu_table = load_table(file_path)

        if len(otu_table.ids()) == 1:
            job.status = BiomSearchJob.QUEUED
            # HACK: HARDCODE! Bad practice!
            job.sample_name = otu_table.ids()[0]
            job.save()
            m_n_betadiversity.delay(job.id)
        else:
            job.status = BiomSearchJob.STOPPED
            job.error_code = BiomSearchJob.SAMPLE_COUNT_ERROR
            job.save()

    except IOError:
        job.status = BiomSearchJob.STOPPED
        job.error_code = BiomSearchJob.FILE_IO_ERROR
        job.save()

    except TableException:
        job.status = BiomSearchJob.STOPPED
        job.error_code = BiomSearchJob.DUPLICATE_ID_ERROR
        job.save()

    except (IndexError, TypeError, ValueError):
        job.status = BiomSearchJob.STOPPED
        job.error_code = BiomSearchJob.FILE_VALIDATION_ERROR
        job.save()


@app.task
def m_n_betadiversity(job_id):
    job = BiomSearchJob.objects.filter(id=job_id).first()
    job.status = BiomSearchJob.PROCESSING
    job.save()

    regexp = re.compile("[^A-Za-z0-9]")
    userdir = settings.MEDIA_ROOT + "{user_id}/{job_id}/".format(
        user_id=job.user_id, job_id=job.id
    )
    userbiom = job.biom_file.path

    # Changing Animal/Human to Animal_Human for database table processing
    # HACK: any way to do this cleaner?
    user_choice = map(
        lambda x: x.replace("/", "_"), map(str, job.criteria.all())
    )
    # Due to database table naming, this is necessary
    if 'All' in user_choice:
        user_choice[user_choice.index('All')] = 'All_eco'

    # TODO: Still hack-y! Find a better way to include the 10k files
    largedata = settings.TEN_K_DATA_PATH

    try:
        # load submitted biom file/text into otutableS
        print("Getting file {}...".format(userbiom))
        otutableS = load_table(userbiom)
        n_sample_otu_matrix = np.asarray(
            [v for v in otutableS.iter_data(axis="sample")]
        )

        # get observation IDs and sample IDs from submitted biom file
        print("Loading data from file...")
        n_otu_id = otutableS.ids(axis="observation")
        n_sample_id = list(otutableS.ids(axis="sample"))

        # trying to parse GreenGenes IDs
        try:
            # stringify tuple of observation IDs
            notuids = str(tuple(map(int, n_otu_id)))
        except ValueError:
            # stop the job if non integer strings were found
            job.status = BiomSearchJob.STOPPED
            job.error_code = BiomSearchJob.STRICT_GREENGENES_ID
            job.save()
            return

        # preparing SQL query to get 16s copy number of each observation IDs
        query_str = """
            SELECT 16s_copy_number
            FROM OTUS_unified
            WHERE otu_id IN {sample_list_tuple}
            ORDER BY FIELD(otu_id, {sample_list_string})
        """.format(sample_list_tuple=notuids, sample_list_string=notuids[1:-1])

        # perform query
        print("Querying...")
        conn = MySQLdb.connect(**server_db)
        curs = conn.cursor(DictCursor)
        curs.execute(query_str)

        # convert 16s otu copy numbers into doubles for math manipulations
        otu_copy_number = np.array(
            [float(rec["16s_copy_number"]) for rec in curs.fetchall()]
        )
        conn.close()

        # if there are observation IDs which are not in DB, exit with message
        if len(otu_copy_number) != len(n_otu_id):
            job.status = BiomSearchJob.STOPPED
            job.error_code = BiomSearchJob.OTU_NOT_EXIST
            job.save()

        # otherwise if all observation IDs are in the DB
        else:
            n_sample_otu_matrix = n_sample_otu_matrix / otu_copy_number
            print("Making sample array...")
            # retrieve the samples need to compute diversity against using
            # representatives
            mMatrix, Msample = return_represent_sample(largedata, user_choice)

            # if submatrix of 10k matrix and queried sample is returned
            # properly
            if len(mMatrix) != 0 and len(Msample) != 0:
                print("Performing M-N Betadiversity calculations...")
                mnMatrix = calculate_MNmatrix(
                    # legacy code
                    # mMatrix, Msample, n_sample_otu_matrix, n_otuid
                    mMatrix, Msample, n_sample_otu_matrix, n_otu_id
                )
                n_sam = [str(n_sample_id[0])]


                #================== END OF MAIN COMPUTATION ==================#

                # 1000 dendogram
                print("Making 1000 dendrogram...")
                d3Dendro = json_for_dendrogam(mnMatrix, Msample + n_sam)
                filename = userdir + "d3dendrogram.json"
                with open(filename, "w") as json_output_file:
                    print("Writing to file {}...".format(filename))
                    json.dump(d3Dendro, json_output_file, sort_keys=True,
                              indent=4)

                # pcoa for 1000 samples
                print("Making 1000 PCOA...")
                pcoa(mnMatrix, Msample + n_sam, userdir)

                # get top ranking representative OTU IDs
                # legacy code
                # m_repsampleid = get_sortedrepresentativeid(
                m_repsampleid = get_sorted_representative_id(
                    mnMatrix, Msample + n_sample_id, 251
                )
                # MN calculation for representative samples
                mMatrix, Msample = return_rep_original_samples(
                    list(m_repsampleid), largedata, user_choice, 250
                )
                mnMatrix = calculate_MNmatrix(
                    mMatrix, Msample, n_sample_otu_matrix, n_otu_id
                )

                # for top 251 dendogram
                print("Making 250 dendrogram...")
                d3Dendro = json_for_dendrogam(mnMatrix, Msample + n_sample_id)
                filename = userdir + "d3dendrogram_sub.json"
                with open(filename, "w") as json_output_file:
                    print("Writing to file {}...".format(filename))
                    json.dump(d3Dendro, json_output_file, sort_keys=True,
                              indent=4)

                # for closest 250 samples
                print("Making 250 PCOA...")
                pcoa(mnMatrix, Msample + n_sam, userdir + "250_")
                submnMatrix, submn_sample_id = heatmap_files(
                    mnMatrix, Msample, n_sample_id, userdir, 21
                )

                # for 21 dendogram
                print("Making 20 dendrogram...")
                d3Dendro = json_for_dendrogam(submnMatrix, submn_sample_id)
                filename = userdir + "d3dendrogram_sub_sub.json"
                with open(filename, "w") as json_output_file:
                    print("Writing to file {}...".format(filename))
                    json.dump(d3Dendro, json_output_file, sort_keys=True,
                              indent=4)

                samplejson = create_json_samples_metadata(
                    submnMatrix[0, :], submn_sample_id, submn_sample_id[1:],
                    userdir
                )

                sample_filename = "_".join(regexp.split(n_sample_id[0]))
                filename = userdir + sample_filename + ".json"
                with open(filename, "w") as json_output_file:
                    json.dump(samplejson, json_output_file, sort_keys=True,
                              indent=4)

                job.status = BiomSearchJob.COMPLETED
                job.save()

            else:
                job.status = BiomSearchJob.STOPPED
                job.error_code = BiomSearchForm.UNKNOWN_ERROR
                job.save()

    except:
        print "Unexpected error:", sys.exc_info()
        job.status = BiomSearchJob.STOPPED
        job.error_code = BiomSearchJob.UNKNOWN_ERROR
        job.save()


@app.task
def save_text(job, input_str):
    """
    Async task to perform saving of input text. This function saves the input
    text into a file to be processed later. Once the file is saved, validation
    will follow immediately.

    :param job: BiomSearchJob object passed from search.py
    :param input_str: String containing user input text
    """
    file_path = \
        settings.MEDIA_ROOT + \
        '{user_id}/{job_id}/{user_id}-{job_id}.txt'.format(
            user_id=job.user_id, job_id=job.id
        )

    if not os.path.exists(os.path.dirname(file_path)):
        try:
            os.makedirs(os.path.dirname(file_path))
        # Guard against race condition
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                job.status = BiomSearchJob.STOPPED
                job.error_code = BiomSearchJob.UNKNOWN_ERROR
                raise

    with open(file_path, "wb") as f:
        f.write(input_str)

    job.biom_file = file_path
    job.save()
    validate_biom.delay(job, file_path)


@app.task
def simulate_task(job_id):
    j = BiomSearchJob.objects.filter(id=job_id).first()
    j.status = BiomSearchJob.PROCESSING
    j.save()
    sleep(60) # basically doing some tasks here
    j.status = BiomSearchJob.COMPLETED
    j.save()
