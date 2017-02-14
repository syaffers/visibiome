from MySQLdb.cursors import DictCursor
from biom.parse import parse_biom_table
from config import server_db
from nonphylogentic_distance_transform import (
    n_adaptive_bray_curtis, m_n_adaptive_bray_curtis
)
import MySQLdb
import json
import numpy as np
import time


def biom_from_sample(sample_list, count_type="normalized_count"):
    """Create an OTU table in biom format from SQL database.
    alternative: use table_factory in
    Qiime/biom-format-1.1.1-release/lib/python2.7/site-packages/biom/table.py

    :param sample_list: List of strings of sample IDs
    :return Dict representation of BIOM table
    """
    # preparing database connections
    conn = MySQLdb.connect(**server_db)
    curs = conn.cursor(DictCursor)
    # preparing output BIOM file header
    table = {
        "id": "None","format": "Biological Observation Matrix 1.0.0",
        "format_url": "http://biom-format.org",
        "type": "OTU table",
        "generated_by": "QIIME 1.7.0",
        "matrix_type": "sparse",
        "matrix_element_type": "float"
    }

    # if sample list is empty get samples from database
    if len(sample_list) == 0:
        get_sample_event_ids_query = """
            SELECT DISTINCT `sample_event_ID`
            FROM `samples_EnvO_annotation_unified`
            NATURAL JOIN envoColors
            NATURAL JOIN OTUS_samples_unified
            LIMIT 5
        """
      	curs.execute(get_sample_event_ids_query)
        samples = [rec["sample_event_ID"] for rec in curs.fetchall()]

    # otherwise set samples to sample_list
    else:
        samples = sample_list

    # preparing sample list for database query
    samps = '\',\''.join(samples)
    samplesDict = dict([(sample, idx) for idx, sample in enumerate(samples)])

    # get OTU IDs of each sample item from database
    get_otu_ids_query = """
        SELECT DISTINCT otu_id
        FROM OTUS_samples_unified
        WHERE sample_event_ID IN ('{sample_list_querystring}')
        ORDER BY FIELD(sample_event_id, '{sample_list_querystring}')
    """.format(sample_list_querystring=samps)
    curs.execute(get_otu_ids_query)

    otus = [rec["otu_id"] for rec in curs.fetchall()]
    otusDict = dict([(otu, idx) for idx, otu in enumerate(otus)])

    # get OTU IDs, samples IDs and normalized_count
    count_query = """
        SELECT otu_id, sample_event_ID, {count_type}
        FROM OTUS_samples_unified
        WHERE sample_event_ID IN ('{sample_list_querystring}')
        ORDER BY FIELD(sample_event_id, '{sample_list_querystring}')
        """.format(count_type=count_type, sample_list_querystring=samps)
    curs.execute(count_query)

    # complete BIOM table
    data = []
    for rec in curs.fetchall():
        data.append(
            [otusDict[rec["otu_id"]],
             samplesDict[rec["sample_event_ID"]],
             float(rec[count_type])]
        )

    table['rows'] = [{"id": o, 'metadata': None} for o in otus]
    table['columns'] = [{"id": s, 'metadata': None} for s in samples]
    table['shape'] = [len(otus), len(samples)]
    table['date'] = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
    table['data'] = data
    conn.close()
    return table


def make_m_n_distmtx(m_distmtx, m_sample_ids, n_otu_matrix, n_otu_ids):
    """Wrapper function to calculate the adaptive Bray-Curtis distance for
    the input sample and queried samples.

    :param m_distmtx: numpy array of database queried samples
    :param m_sample_ids: list of database queried sample IDs
    :param n_otu_matrix: numpy array of user provided samples
    :param n_otu_ids: list of user provided sample IDs
    """
    # generate biom table object based on queried samples
    m_otu_table = parse_biom_table(json.dumps(biom_from_sample(m_sample_ids)))

    m_sample_otu_matrix = np.asarray(
        [v for v in m_otu_table.iter_data(axis="sample")]
    )

    m_otu_ids = m_otu_table.ids(axis="observation")

    # calculate adaptive Bray-Curtis distances between all submitted samples
    # if users submits a file with 4 samples, this will return a 4 by 4
    # distance matrix
    n_distmtx = n_adaptive_bray_curtis(n_otu_matrix, list(n_otu_ids))

    # calculate adaptive Bray-Curtis distances for all submitted samples
    # against queried samples
    m_n_distrows = m_n_adaptive_bray_curtis(
        m_sample_otu_matrix, list(m_otu_ids), n_otu_matrix, list(n_otu_ids)
    )

    # stack matrices to make the m + n distance matrix
    m_n_distmtx = np.vstack(
        (np.hstack((m_distmtx, m_n_distrows)),
         np.hstack((m_n_distrows.T, n_distmtx)))
    )

    return m_n_distmtx
