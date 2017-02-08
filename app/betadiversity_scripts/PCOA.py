import cogent.cluster.metric_scaling as ms
import sys
import os.path
import cPickle
import MySQLdb
from MySQLdb.cursors import DictCursor
from dendrogam_d3_json import retrieve_source
from config import server_db
from numpy import abs


def meta_data(msampleid):
    # connect to the database and form query
    conn = MySQLdb.connect(**server_db)
    curs = conn.cursor(DictCursor)
    curs.execute("SELECT sample_event_ID,REPLACE(title,'\\'','') title,REPLACE(OntologyTerm,'\\'','') OntologyTerm,OntologyID,sample_size,study,ecosystem FROM `samples_unified` natural join samples_sizes_unified natural join samples_EnvO_annotation_unified natural join envoColors where `sample_event_ID` ='"+msampleid+"'")

    # prepare variables
    title = ""
    otcnt = oicnt = ecnt = sample_size = 0
    OntologyTerm = ["Unknown", "Unknown", "Unknown"]
    OntologyID = ["Unknown", "Unknown", "Unknown"]
    ecosystem = ["Unknown", "Unknown", "Unknown"]
    sample_event_ID = None
    study_source = ""

    # for each row in the query
    for rec in curs.fetchall():
        # first run
        if sample_event_ID is None:
            sample_event_ID = rec["sample_event_ID"].strip()
            title = rec["title"].strip().replace(',','')
            OntologyTerm[otcnt] = rec["OntologyTerm"].strip().replace(',','')
            OntologyID[oicnt] = rec["OntologyID"].strip()
            sample_size = float(rec["sample_size"])
            study_source = retrieve_source(rec["study"])
            ecosystem[ecnt] = rec["ecosystem"].strip()
            otcnt = otcnt + 1
            oicnt = oicnt + 1
            ecnt = ecnt + 1
        # all other runs
        else:
	    if rec["OntologyID"] not in OntologyID and oicnt < 3:
                OntologyID[oicnt] = rec["OntologyID"].strip()
                oicnt = oicnt + 1
            if rec["OntologyTerm"] not in OntologyTerm and otcnt < 3:
	        OntologyTerm[otcnt] = rec["OntologyTerm"].strip()
                otcnt = otcnt + 1
            if rec["ecosystem"] not in ecosystem and ecnt < 3:
                ecosystem[ecnt] = rec["ecosystem"].strip()
                ecnt = ecnt + 1

    conn.close()
    return title,OntologyID[0],OntologyTerm[0],OntologyID[1],OntologyTerm[1],OntologyID[2],OntologyTerm[2],sample_size,study_source,ecosystem[0],ecosystem[1],ecosystem[2]


def pcoa(distmtx, samples, userdir):
    """Make PCoA-related file for D3.js drawings. Generates CSV file.

    :param distmtx: Numpy array matrix of distances
    :param samples: List of strings containing sample IDs
    :param userdir: User directory path to which the file will be written
    """
    with open(userdir + "pcoa_1000.csv", "w") as f_pcoa:
        coords, eigvals = ms.principal_coordinates_analysis(distmtx)
        pcnts = (abs(eigvals) / sum(abs(eigvals))) * 100
        idxs_descending = pcnts.argsort()[::-1]
        coords = coords[idxs_descending]
        # eigvals = eigvals[idxs_descending]
        # pcnts = pcnts[idxs_descending]

        header = "Sample Name,PC1,PC2,PC3,Title,OntologyID1,OntologyTerm1,"
        header += "OntologyID2,OntologyTerm2,OntologyID3,OntologyTerm3,"
        header += "Sample Size,Study Source,Ecosystem1,Ecosystem2,Ecosystem3\n"

        f_pcoa.write(header)
        for i in zip(samples, coords.T[:,0], coords.T[:,1], coords.T[:,2]):
            res = str(i + meta_data(i[0])).replace("u\'","").replace("\'","")\
                      .replace("(","").replace(")","")
            f_pcoa.write(res + "\n")
