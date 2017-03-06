from MySQLdb.cursors import DictCursor
from app.models import BiomSearchJob, BiomSample
from betadiversity_scripts.MNBetadiversity import make_m_n_distmtx
from betadiversity_scripts.config import server_db
from betadiversity_scripts.visualizations import (generate_samples_metadata, generate_pcoa_file,
    generate_dendrogram_file, generate_barcharts)
from betadiversity_scripts.select_samples import query_samples
from biom import load_table
from biom.exception import TableException
from vzb.celery import app
from django.conf import settings
from django.db import transaction
from django.utils import timezone
import MySQLdb
import numpy as np
import pandas as pd
import sys
import traceback
import os
import pdb
import sys
import re

import cPickle
from betadiversity_scripts import gnatsearch as gs
from betadiversity_scripts import microbiomeUtils as mu
#from betadiversity_scripts.microbiomeUtils import SearchEngine

def gnat_unifrac(l_data_path, criteria, n_otu_matrix, n_otu_ids, job_dir_path, n_sample_ids, job):
    print "GNATing..."

    engine = gs.SearchEngine(n_otu_matrix, n_otu_ids, n_sample_ids, l_data_path, criteria)
    try:
        engine.gnatsearch()
        engine.shortReport()
        m_n_distmtx, m_n_sample_ids, rankingDF = engine.make_m_n_distmtx()
    finally:
        engine.close() ## closes Database connection

    print("Making top hit correspondence barcharts...")
    barchartDicts = generate_barcharts(engine.GNATresults, job_dir_path)

    print("Making dendrogram...")
    filepath = os.path.join(job_dir_path, "d3dendrogram.json")
    generate_dendrogram_file(m_n_distmtx, m_n_sample_ids, filepath)

    # pcoa for available samples
    print("Making PCOA...")
    filepath = os.path.join(job_dir_path, "pcoa_1000.json")
    generate_pcoa_file(m_n_distmtx, m_n_sample_ids, n_sample_ids, filepath)

    sample_filename = job.file_safe_name() + ".json"
    filepath = os.path.join(job_dir_path, sample_filename)
    ## this interface has been updated to cope with multiple rankings
    print "Making sample metadata file (from GNAT results) with barchart info"
    generate_samples_metadata(rankingDF, n_sample_ids, filepath, barcharts=barchartDicts)
    print "Done"
    job.status = BiomSearchJob.COMPLETED
    job.save()

def bray_curtis(l_data_path, criteria, n_otu_matrix, n_otu_ids, job_dir_path, n_sample_ids, job):
    # query the representatives
    print("Getting representatives...")
    m_distmtx, m_sample_ids = query_samples(l_data_path, criteria, 1000)

    # combine both sample ids from user samples and representatives
    m_n_sample_ids = m_sample_ids + n_sample_ids

    # if representatives matrix and sample IDs are not empty
    if len(m_distmtx) != 0 and len(m_sample_ids) != 0:
        print("Performing M-N Betadiversity calculations (reps)...")
        m_n_distmtx = make_m_n_distmtx(m_distmtx, m_sample_ids, n_otu_matrix, n_otu_ids)
        m_n_df = pd.DataFrame(m_n_distmtx, columns=m_n_sample_ids, index=m_n_sample_ids)

        # 1000 dendogram
        print("Making 1000 dendrogram...")
        filepath = os.path.join(job_dir_path, "d3dendrogram.json")
        generate_dendrogram_file(m_n_distmtx, m_n_sample_ids, filepath)

        # pcoa for 1000 samples
        print("Making 1000 PCOA...")
        filepath = os.path.join(job_dir_path, "pcoa_1000.json")
        generate_pcoa_file(m_n_distmtx, m_n_sample_ids, n_sample_ids, filepath)

        """THE CODE BELOW IS NO LONGER USED AND SHOULD BE REMOVED ACCORDINGLY"""
        # # get top ranking representative OTU IDs
        # n_top_rep_sample_ids = get_sorted_representative_id(m_n_distmtx, m_n_sample_ids)
        #
        # # query actual samples
        # print("Getting actual samples from representatives...")
        # m_distmtx, m_sample_ids = query_samples(l_data_path, criteria, 250, n_top_rep_sample_ids)
        # # combine both sample ids from user samples and actual samples
        # m_n_sample_ids = m_sample_ids + n_sample_ids
        #
        # # MN calculation for actual samples
        # print("Performing M-N Betadiversity calculations (actual)...")
        # m_n_distmtx = make_m_n_distmtx(m_distmtx, m_sample_ids, n_otu_matrix, n_otu_ids)
        #
        # # for top 250 dendogram
        # print("Making 250 dendrogram...")
        # filepath = os.path.join(job_dir_path, "d3dendrogram_sub.json")
        # generate_dendrogram_file(m_n_distmtx, m_n_sample_ids, filepath)
        #
        # # for closest 250 samples
        # print("Making 250 PCOA...")
        # filepath = os.path.join(job_dir_path, "pcoa_250.csv")
        # generate_pcoa_file(m_n_distmtx, m_n_sample_ids, filepath)
        #
        # # for closest 250 heatmap
        # print("Making 250 heatmap...")
        # top_m_n_distmtx, top_m_n_sample_ids = generate_heatmap_files(
        #     m_n_distmtx, m_n_sample_ids, job_dir_path, 20 + len(n_sample_ids)
        # )
        #
        # # for 20 dendogram
        # print("Making 20 dendrogram...")
        # filepath = os.path.join(job_dir_path, "d3dendrogram_sub_sub.json")
        # generate_dendrogram_file(top_m_n_distmtx, top_m_n_sample_ids, filepath)
        """THE CODE ABOVE IS NO LONGER USED AND SHOULD BE REMOVED ACCORDINGLY"""

        print("Making sample metadata file...")
        sample_filename = job.file_safe_name() + ".json"
        filepath = os.path.join(job_dir_path, sample_filename)
        generate_samples_metadata(m_n_df, n_sample_ids, filepath)

        print("Done!")
        job.status = BiomSearchJob.COMPLETED
        job.save()

    else:
        job.status = BiomSearchJob.STOPPED
        job.error_code = BiomSearchJob.UNKNOWN_ERROR
        job.save()


@app.task
def validate_biom(job, file_path):
    """Async task to perform validation of input files/text. This function
    checks whether the input is a valid BIOM file by parsing the input file. If
    it fails then chances are it is not a valid BIOM file. If it succeeds, the
    function then checks if there is exactly one sample in the valid OTU table
    of BIOM file.

    :param job: BiomSearchJob object passed from search.py
    :param file_path: String containing file path to uploaded file
    """
    try:
        job.last_run_at = timezone.now()
        otu_table = load_table(file_path)

        if len(otu_table.ids("sample")) <= 10:
            # if it's a rerun, remove any errors but don't add any samples to the DB
            if job.status == BiomSearchJob.RERUN:
                job.error_code = BiomSearchJob.NO_ERRORS
            else:
                # atomic transaction to speed up saving multiple samples
                with transaction.atomic():
                    for sample_name in otu_table.ids(axis="sample"):
                        sample = BiomSample(name=sample_name, job=job)
                        sample.save()

            job.status = BiomSearchJob.QUEUED
            job.save()
            m_n_betadiversity.delay(job)
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
def m_n_betadiversity(job):
    job.status = BiomSearchJob.PROCESSING
    job.save()

    regexp = re.compile("[^A-Za-z0-9]")
    job_dir_path = os.path.split(job.biom_file.path)[0]
    userbiom = job.biom_file.path

    # Changing Animal/Human to Animal_Human for database table processing
    # HACK: any way to do this cleaner?
    criteria = map(
        lambda x: x.replace("/", "_"), map(str, job.criteria.all())
    )
    # Due to database table naming, this is necessary
    if 'All' in criteria:
        criteria[criteria.index('All')] = 'All_eco'

    # TODO: Still hack-y! Find a better way to include the 10k files
    l_data_path = settings.L_MATRIX_DATA_PATH

    try:
        # load submitted biom file/text into otu_table
        print("Getting file {}...".format(userbiom))
        n_otu_table = load_table(userbiom)
        n_otu_matrix = n_otu_table.matrix_data.toarray().T
        # extract sample IDs and OTU IDs
        n_otu_ids = n_otu_table.ids(axis="observation")
        n_sample_ids = list(map(str, n_otu_table.ids(axis="sample")))

        # trying to parse GreenGenes IDs
        try:
            # stringify tuple of observation IDs
            n_otu_ids_formatted = str(tuple(map(int, n_otu_ids)))
            n_otu_ids_formatted100 = str(tuple(map(int, n_otu_ids[:100])))
        except ValueError:
            # stop the job if non integer strings were found
            job.status = BiomSearchJob.STOPPED
            job.error_code = BiomSearchJob.STRICT_GREENGENES_ID
            job.save()
            return

        # preparing SQL query to get 16s copy number of each observation IDs
        # necessary query to check for non-existence of OTUs
        query_str = """
            SELECT 16s_copy_number, otu_id
            FROM OTUS_unified
            WHERE otu_id IN {sample_list_tuple}
            ORDER BY FIELD(otu_id, {sample_list_string})
        """.format(sample_list_tuple=n_otu_ids_formatted,
                   sample_list_string=n_otu_ids_formatted[1:-1])

        # perform query
        print("Querying for 16s copy numbers...")
        conn = MySQLdb.connect(**server_db)
        curs = conn.cursor(DictCursor)
        n = curs.execute(query_str)

        records = curs.fetchall()
        missingInfo =  [rec["otu_id"] for rec in records if rec["16s_copy_number"] is None]
        if missingInfo:
            print "Warning OTUs without copy nr!", missingInfo
        # Warning this replaces missing values simply with 1!!!
        # convert 16s otu copy numbers into doubles for math manipulations
        otu_copy_numbers = np.array(
            [float(rec["16s_copy_number"]) for rec in records] # 1. if rec["16s_copy_number"] is None else
        )
        conn.close()
        print "... successful"
        # if there are observation IDs which are not in DB, exit with message
        # TO BE FIXED!!! Copy missing entries from ServerMicrobiome to EarthMicrobiome
        if len(otu_copy_numbers) != len(n_otu_ids):
            job.status = BiomSearchJob.STOPPED
            job.error_code = BiomSearchJob.OTU_NOT_EXIST
            job.save()

        # otherwise if all observation IDs are in the DB
        else:
            # normalize OTU copy numbers if not already
            if job.is_normalized_otu:
                print("OTUs are pre-normalized...")
            else:
                print("OTUs are not normalized... normalizing")
                n_otu_matrix = n_otu_matrix / otu_copy_numbers

                if job.analysis_type == BiomSearchJob.BRAYCURTIS:
                    bray_curtis(l_data_path, criteria, n_otu_matrix, n_otu_ids, job_dir_path, n_sample_ids, job)
                elif job.analysis_type == BiomSearchJob.GNATUNIFRAC:
                    gnat_unifrac(l_data_path, criteria, n_otu_matrix, n_otu_ids, job_dir_path, n_sample_ids, job)
                else:
                    pass

    except:
        print("Unexpected error:", sys.exc_info())
        traceback.print_tb(sys.exc_info()[2])
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
            user_id=job.user_id, job_id=job.pk
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
