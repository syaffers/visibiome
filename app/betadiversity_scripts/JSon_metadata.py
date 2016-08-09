from MySQLdb.cursors import DictCursor
from config import server_db
import MySQLdb
import json

class Sample:
    def __init__(self, rk, name, title, OntologyID1, OntologyTerm1, OntologyID2,
                 OntologyTerm2, OntologyID3, OntologyTerm3, sample_size,
                 distance, stdy_source):
	self.Ranking = rk
	self.Name = name
	self.Study = title

	if OntologyID1 == "":
	  self.S_EnvO_1 = " "
	else:
	  self.S_EnvO_1= OntologyID1 + ", " + OntologyTerm1
	if OntologyID2 == "":
	  self.S_EnvO_2 = " "
	else:
	  self.S_EnvO_2= OntologyID2 + ", " + OntologyTerm2
	if OntologyID3 == "":
	  self.S_EnvO_3 = " "
	else:
	  self.S_EnvO_3= OntologyID3 + ", " + OntologyTerm3

	self.Total_Sample_Size = sample_size
	self.Total_Distance = distance
	self.Study_Source = stdy_source


def retrieve_source(sample_study):
    if sample_study.find('CHA_') != -1:
        return "Chaffron data"
    elif sample_study.find('QDB_') != -1:
        return "Earth Microbiome Project"
    elif sample_study.find('MI_MIT_') != -1:
        return "MI MIT Sequencing"
    elif sample_study.find('SRA_') != -1:
        return "SRA data"
    else:
        return "Unknown"



def create_json_samples_metadata(mnMatrix,mnsampleid,m_sampleid,userdir):
    #print "for ranking: "
    #print mnsampleid
    #print m_sampleid
    MNsample_dict=dict(zip(mnsampleid,range(0,len(mnsampleid))))

    samplejson=dict(sample=[])
    sample_metadata=[]

    msampleids='\',\''.join(m_sampleid)
    conn = MySQLdb.connect(**server_db)
    curs = conn.cursor(DictCursor)
#print notuids
    curs.execute("SELECT DISTINCT sample_event_ID,title,OntologyTerm,OntologyID,sample_size,study FROM `samples_unified` natural join samples_sizes_unified natural join samples_EnvO_annotation_unified natural join envoColors where `sample_event_ID` in ('"+msampleids+"') ORDER BY FIELD( sample_event_ID,'"+msampleids+"')")
    #print msampleids
    title=""
    authors_list=""
    OntologyTerm=["","",""]
    OntologyID=["","",""]
    sample_size=0
    distance=0.0
    cnt=0
    rk=0
    sample_event_ID=None
    study=""
    for rec in curs.fetchall():
	#print rec["sample_event_ID"]
	if sample_event_ID==None:
	  sample_event_ID=rec["sample_event_ID"]
	  title=rec["title"]
	  OntologyTerm[cnt]=rec["OntologyTerm"]
	  OntologyID[cnt]=rec["OntologyID"]
	  sample_size=float(rec["sample_size"])
	  distance="%.4f" %mnMatrix[MNsample_dict[sample_event_ID]]
	  study=retrieve_source(rec["study"])


	elif sample_event_ID!=rec["sample_event_ID"]:
	  rk=rk+1
	  sample_metadata.append(vars(Sample(rk,sample_event_ID,title,OntologyID[0],OntologyTerm[0],OntologyID[1],OntologyTerm[1],OntologyID[2],OntologyTerm[2],sample_size,distance,study)))
	  sample_event_ID=rec["sample_event_ID"]
	  title=rec["title"]
	  OntologyTerm=["","",""]
    	  OntologyID=["","",""]
	  cnt=0
	  OntologyTerm[cnt]=rec["OntologyTerm"]
	  OntologyID[cnt]=rec["OntologyID"]
	  sample_size=float(rec["sample_size"])
	  distance="%.4f" %mnMatrix[MNsample_dict[sample_event_ID]]
	  study=retrieve_source(rec["study"])

	else:
	  OntologyTerm[cnt]=rec["OntologyTerm"]
	  OntologyID[cnt]=rec["OntologyID"]
	cnt=cnt+1

    rk=rk+1
    sample_metadata.append(vars(Sample(rk,sample_event_ID,title,OntologyID[0],OntologyTerm[0],OntologyID[1],OntologyTerm[1],OntologyID[2],OntologyTerm[2],sample_size,distance,study)))

    samplejson['sample']=sample_metadata
    conn.close()
    return samplejson
