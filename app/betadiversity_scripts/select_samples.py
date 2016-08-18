from MySQLdb.cursors import DictCursor
from config import server_db
from string import strip
import MySQLdb
import cPickle
import numpy as np
import random
import re
import sys

# filter function to extract items in list y if they exist list x
dictfilt = lambda x, y: dict([(i, x[i]) for i in y if i in x])

def prepare_sql(criteria):
    """Prepares SQL query when running return_represent_sample.

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
    return re.sub("\n\s+", " ", strip(sql))


def prepare_sql_original(criteria, rep_sample_ids, sample_count, limit):
    """Prepares SQL query when running return_rep_original_sample.

    :param criteria: List of strings containing user search criteria
    :param rep_sample_ids: List of strings containing representative sample IDs
    :param sample_count: Integer number of samples to take from
    rep_sample_ids
    :param limit: Integer max number of rows to be called from database
    :return: String of SQL query to get rows to get data from DB
    """
    # qs_sample_ids = str(tuple(rep_sample_ids[:sample_count]))
    qs_sample_ids = '\',\''.join(rep_sample_ids[:sample_count])

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
        first_criterion=criteria[0], sample_ids=qs_sample_ids, limit=limit
    )
    # remove unnecessary spaces
    return re.sub("\n\s+", " ", strip(sql))


def return_represent_sample(largedata, user_choice):
    """Get representative samples from the database based on user search
    criteria.

    :param largedata: String filename of 10k file
    :param user_choice: List of strings containing user search criteria
    :return: Tuple of submatrix of representative samples and list of sample IDs
    """
    print("\nLoading 10k files... ({})".format(__file__))
    # load files from binary
    print("\n    from  ({})".format(largedata + "10k_samples.pcl"))
    totsample = cPickle.load(open(largedata + "10k_samples.pcl"))
    # distance matrix
    totMatrix = np.load(largedata + "10k_bray_curtis_adaptive.npy")
    totsample_dict = dict(zip(totsample, range(len(totsample))))
    mMatrix = []
    Msample = []

    # prepare query get data from database which matches the selection
    # criterion of the user
    sql_query = prepare_sql(user_choice)

    # if files are not empty
    if len(totMatrix) != 0 and len(totsample) != 0:
        print("\nQuerying database... ({})".format(__file__))
        # get samples from database
        conn = MySQLdb.connect(**server_db)
        curs = conn.cursor(DictCursor)
        curs.execute(sql_query)

        # get sample ids
        selected_sample = [rec["sample_event_ID"] for rec in curs.fetchall()]
        conn.close()

        # enumerate samples into dictionary
        # selected_sample_dict = {<queried_sample_id>: <queried_index>, ...}
        selected_sample_dict = dict(
            zip(selected_sample, range(len(selected_sample)))
        )

        # filter out database samples to match items loaded from file
        # result -> {<queried_sample_id>: <index_based_on_10k_file>, ...}
        idx_dict = dictfilt(totsample_dict, selected_sample_dict)
        Msample = idx_dict.keys()

        # get submatrix of Bray-Curtis distances for queried samples
        mMatrix = totMatrix[idx_dict.values(),:][:,idx_dict.values()]
        del totMatrix
        del totsample

    return mMatrix, Msample


def return_rep_original_samples(m_repsampleid,
                                largedata, user_choice, sel_count):
    """Get representative samples of original data from the database based on
    user search criteria limited by a selection count.

    :param m_repsampleid: List of representative sample IDs
    :param largedata: String filename of 10k file
    :param user_choice: List of strings containing user search criteria
    :param sel_count: Integer of number of items
    :return: Tuple of submatrix of representative samples and list of sample IDs
    """
    print("\nLoading 10k files... ({})".format(__file__))
    # load files from binary:
    totsample = cPickle.load(open(largedata + "10k_samples.pcl"))
    # distance matrix
    totMatrix = np.load(largedata + "10k_bray_curtis_adaptive.npy")
    totsample_dict = dict(zip(totsample, range(len(totsample))))
    mMatrix = []
    Msample = []
    selected_sample = []

    if len(totMatrix) != 0 and len(totsample) != 0:
        conn = MySQLdb.connect(**server_db)
        # iterative query to get top 250 representatives
        for val in range(1, sel_count + 1):
            # prepare query get data from database which matches the selection
            # criterion of the user
            print("\nQuerying database... ({})".format(__file__))
            sql_query = prepare_sql_original(
                user_choice, m_repsampleid, val, sel_count
            )
            curs = conn.cursor(DictCursor)
            curs.execute(sql_query)
            selected_sample = [
                rec["sample_event_ID"] for rec in curs.fetchall()
            ]

            if len(selected_sample) == sel_count:
                break

        # close connection after for loop
        conn.close()

        # enumerate samples into dictionary
        # selected_sample_dict = {<queried_sample_id>: <queried_index>, ...}
        selected_sample_dict = dict(
            zip(selected_sample, range(0, len(selected_sample)))
        )

        # filter out database samples to match items loaded from file
        # result -> {<queried_sample_id>: <index_based_on_10k_file>, ...}
        idx_dict = dictfilt(totsample_dict, selected_sample_dict)
        Msample = idx_dict.keys()

        # get submatrix of Bray-Curtis distances for queried samples
        mMatrix = totMatrix[idx_dict.values(),:][:,idx_dict.values()]
        del totMatrix
        del totsample

    return mMatrix, Msample
