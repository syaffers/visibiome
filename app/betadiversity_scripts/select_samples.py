from MySQLdb.cursors import DictCursor
from config import server_db
from django.conf import settings
import MySQLdb
import cPickle
import numpy as np
import os
import re
import sys

def prepare_sql_representatives(criteria):
    """Prepares SQL query to get representative sample IDs.

    :param criteria: List of strings containing user search criteria
    :return: String of SQL query to get rows to get data from db based on user
             search criteria
    """
    # form initial query string
    sql = """
        SELECT sample_event_ID
        FROM   sample_cluster_representative
        WHERE  {first_criterion} != ''
    """.format(first_criterion=criteria[0])

    # no duplicates query!
    for criterion in criteria[1:]:
       sql += " OR {} != ''".format(criterion)

    # complete query string
    sql += " ORDER BY RAND() LIMIT 1000"
    # remove unnecessary spaces
    return re.sub("\n\s+", " ", sql.strip())


def prepare_sql_actual(criteria, rep_sample_ids, limit):
    """Prepares SQL query to get actual sample IDs.

    :param criteria: List of strings containing user search criteria
    :param rep_sample_ids: List of strings containing representative sample IDs
    :param sample_count: Integer number of samples to take from
    rep_sample_ids
    :param limit: Integer max number of rows to be called from database
    :return: String of SQL query to get rows to get data from DB
    """
    qs_sample_ids = '\',\''.join(rep_sample_ids)
    # form initial query string
    sql = """
        SELECT sample_event_ID
        FROM   Server_samples
        WHERE  {first_criterion}_rep IN ('{sample_ids}')
    """.format(first_criterion=criteria[0], sample_ids=qs_sample_ids)

    # no duplicates query!
    for choice in criteria[1:]:
        sql += " OR {criterion}_rep IN ('{sample_ids}')".format(
            criterion=choice, sample_ids=qs_sample_ids
        )

    # complete query string
    sql += """
        ORDER BY FIELD({first_criterion}_rep, '{sample_ids}')
        LIMIT {limit}
    """.format(
        first_criterion=criteria[0], sample_ids=qs_sample_ids, limit=limit * 2
    )
    # remove unnecessary spaces
    return re.sub("\n\s+", " ", sql.strip())


def query_samples(largedata, user_choice, sel_count, m_repsampleid=None):
    """Get samples of based on user ecosystem query and optional representative
    sample ID list.

    :param largedata: String filename of 10k file
    :param user_choice: List of strings containing user search criteria
    :param sel_count: Integer of number of items
    :param m_repsampleid: (optional) List of representative sample IDs
    :return: Tuple of submatrix of representative samples and list of sample IDs
    """
    print("\nLoading 10k files... ({})".format(__file__))
    # set path for each file
    ten_k_samples_file = os.path.join(largedata, "10k_samples.pcl")
    ten_k_distances_file = os.path.join(largedata,
                                        "10k_bray_curtis_adaptive.npy")
    # load files from binary
    print("\n    from  ({})".format(ten_k_samples_file))
    totsample = cPickle.load(open(ten_k_samples_file))
    # distance matrix
    totMatrix = np.load(ten_k_distances_file)
    totsample_dict = dict(zip(totsample, range(len(totsample))))
    mMatrix = []
    Msample = []
    sql_query = ""

    # if there are representative sample IDs, we need to get the actual samples
    if m_repsampleid:
        sql_query = prepare_sql_actual(user_choice, m_repsampleid, sel_count)
    else:
        sql_query = prepare_sql_representatives(user_choice)

    # if files are not empty
    if len(totMatrix) != 0 and len(totsample) != 0:
        # get samples from database
        print("\nQuerying database (modified)... ({})".format(__file__))
        conn = MySQLdb.connect(**server_db)
        curs = conn.cursor(DictCursor)
        curs.execute(sql_query)

        # get sample ids
        selected_samples = [row["sample_event_ID"] for row in curs.fetchall()]
        conn.close()

        # filter out database samples to match items loaded from file
        # result -> {<queried_sample_id>: <index_based_on_10k_file>, ...}
        filtered_samples = []
        for sample in selected_samples:
            if sample in totsample_dict:
                filtered_samples.append((sample, totsample_dict[sample]))
            if len(filtered_samples) >= sel_count:
                break
        idx_dict = dict(filtered_samples)
        Msample = idx_dict.keys()


        # get submatrix of Bray-Curtis distances for queried samples
        mMatrix = totMatrix[idx_dict.values(),:][:,idx_dict.values()]
        del totMatrix
        del totsample

    return mMatrix, Msample
