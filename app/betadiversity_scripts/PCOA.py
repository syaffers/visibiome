import cogent.cluster.metric_scaling as ms
import numpy
import sys
import os.path
import cPickle
import MySQLdb
from MySQLdb.cursors import DictCursor
from dendrogam_d3_json import retrieve_source
from config import server_db


def meta_data(msampleid):
    conn = MySQLdb.connect(**server_db)
    curs = conn.cursor(DictCursor)
    curs.execute("SELECT sample_event_ID,REPLACE(title,'\\'','') title,REPLACE(OntologyTerm,'\\'','') OntologyTerm,OntologyID,sample_size,study,ecosystem FROM `samples_unified` natural join samples_sizes_unified natural join samples_EnvO_annotation_unified natural join envoColors where `sample_event_ID` ='"+msampleid+"'")
    title=""
    OntologyTerm=["Unknown","Unknown","Unknown"]
    otcnt=0
    OntologyID=["Unknown","Unknown","Unknown"]
    oicnt=0
    ecosystem=["Unknown","Unknown","Unknown"]
    ecnt=0
    sample_size=0
    sample_event_ID=None
    study_source=""
    for rec in curs.fetchall():
        #print rec["sample_event_ID"]
	if sample_event_ID==None:
	  sample_event_ID=rec["sample_event_ID"].strip()
	  title=rec["title"].strip().replace(',','')
          #print title
	  OntologyTerm[otcnt]=rec["OntologyTerm"].strip().replace(',','')
	  OntologyID[oicnt]=rec["OntologyID"].strip()
	  sample_size=float(rec["sample_size"])
	  study_source=retrieve_source(rec["study"])
	  ecosystem[ecnt]=rec["ecosystem"].strip()
	  otcnt=otcnt+1
	  oicnt=oicnt+1
	  ecnt=ecnt+1
	else:
	  if rec["OntologyID"] not in OntologyID:
		OntologyID[oicnt]=rec["OntologyID"].strip()
		oicnt=oicnt+1
	  if rec["OntologyTerm"] not in OntologyTerm:
		OntologyTerm[otcnt]=rec["OntologyTerm"].strip()
		otcnt=otcnt+1
	  if rec["ecosystem"] not in ecosystem:
		ecosystem[ecnt]=rec["ecosystem"].strip()
		ecnt=ecnt+1


    conn.close()
    return title,OntologyID[0],OntologyTerm[0],OntologyID[1],OntologyTerm[1],OntologyID[2],OntologyTerm[2],sample_size,study_source,ecosystem[0],ecosystem[1],ecosystem[2]


def pcoa(distmtx,samples,userdir):
    f1=open(userdir+"pcoa_1000.csv","w")

    coords, eigvals = ms.principal_coordinates_analysis(distmtx)
    pcnts = (numpy.abs(eigvals) / sum(numpy.abs(eigvals))) * 100
    idxs_descending = pcnts.argsort()[::-1]
    coords = coords[idxs_descending]
    eigvals = eigvals[idxs_descending]
    pcnts = pcnts[idxs_descending]
    f1.write("Sample Name,PC1,PC2,PC3,Title,OntologyID1,OntologyTerm1,OntologyID2,OntologyTerm2,OntologyID3,OntologyTerm3,Sample Size,Study Source,Ecosystem1,Ecosystem2,Ecosystem3\n")
    for i in zip(samples,coords.T[:,0],coords.T[:,1],coords.T[:,2]):
	res=str(i+meta_data(i[0])).replace("u\'","").replace("\'","").replace("(","").replace(")","")
	f1.write(res+ "\n")
    #print coords.T
    f1.close()
