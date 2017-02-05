from MySQLdb.cursors import DictCursor
from config import server_db
import MySQLdb
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
