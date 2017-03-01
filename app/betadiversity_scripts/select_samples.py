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


""" NO LONGER NEEDED """
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
""" NO LONGER NEEDED """


def query_samples(l_data_path, criteria, query_count, m_rep_sample_ids=None):
    """Get samples of based on user ecosystem query and optional representative
    sample IDs list.

    :param l_data_path: String filename of 10k file
    :param criteria: List of strings containing user search criteria
    :param query_count: Integer of number of items to return from query
    :param m_rep_sample_ids: (optional) List of representative sample IDs
    :return: Tuple of submatrix of representative samples and list of sample
    IDs
    """
    print("\nLoading 10k files... ({})".format(__file__))
    # set path for each file
    l_sample_ids_file = os.path.join(l_data_path, "10k_samples.pcl")
    l_distmtx_file = os.path.join(l_data_path, "10k_bray_curtis_adaptive.npy")
    # load files from binary
    print("\n    from  ({})".format(l_sample_ids_file))
    l_sample_ids = cPickle.load(open(l_sample_ids_file))

    # load distance matrix from file
    l_distmtx = np.load(l_distmtx_file)
    l_sample_ids_dict = dict(zip(l_sample_ids, range(len(l_sample_ids))))
    m_distmtx = []
    m_sample_ids = []
    sql_query = ""

    # if there are representative sample IDs, we need to get the actual samples
    if m_rep_sample_ids:
        """ NO LONGER NEEDED """
        sql_query = prepare_sql_actual(criteria, m_rep_sample_ids, query_count)
    else:
        sql_query = prepare_sql_representatives(criteria)

    # if files are not empty
    if len(l_distmtx) != 0 and len(l_sample_ids) != 0:
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
        for sample_id in selected_samples:
            if sample_id in l_sample_ids_dict:
                filtered_samples.append(
                    (sample_id, l_sample_ids_dict[sample_id])
                )
            if len(filtered_samples) >= query_count:
                break
        idx_dict = dict(filtered_samples)
        m_sample_ids = idx_dict.keys()


        # get submatrix of Bray-Curtis distances for queried samples
        m_distmtx = l_distmtx[idx_dict.values(),:][:,idx_dict.values()]
        del l_distmtx
        del l_sample_ids

    return m_distmtx, m_sample_ids
