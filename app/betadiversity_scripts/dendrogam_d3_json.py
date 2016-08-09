from MySQLdb.cursors import DictCursor
from config import server_db
import MySQLdb
import json
import numpy as np
import scipy.cluster.hierarchy as sch


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


def add_node(node, parent):
    # First create the new node and append it to its parent's children
    newNode = dict( node_id=node.id, children=[] )
    parent["children"].append( newNode )

    # Recursively add the current node's children
    if node.left: add_node( node.left, newNode )
    if node.right: add_node( node.right, newNode )

def label_tree( n ,id2name,z_dict):
    # If the node is a leaf, then we have its name
    if len(n["children"]) == 0:
        leafNames = [ id2name[n["node_id"]] ]
        n["length"]=z_dict[float(n["node_id"])]*100

    # If not, flatten all the leaves in the node's subtree
    else:
        leafNames = reduce(lambda ls, c: ls + label_tree(c,id2name,z_dict), n["children"], [])
        n["length"]=(z_dict[float(n["node_id"])]-z_dict[float(n["children"][0]['node_id'])])*100


    # Delete the node id since we don't need it anymore and
    # it makes for cleaner JSON
    n["node_id"]

    # Labeling convention: "-"-separated leaf names
    name = "-".join(sorted(map(str, leafNames)))
    if name.find("-")==-1:
    	n["name"] = name
	title,OntologyTerm,sample_size,study_source,ecosystem,ecocolor=meta_data(name)
    else:
	n["name"]=str(name.count("-")+1)
	msampleids=name.replace("-",'\',\'')
	title,OntologyTerm,sample_size,study_source,ecosystem,ecocolor=envo_data(msampleids)
    n["title"]=title
    n["OntologyTerm"]=OntologyTerm
    n["study_source"]=study_source
    n["ecosystem"]=ecosystem
    n["ecocolor"]=ecocolor

    return leafNames

def meta_data(msampleid):
    conn = MySQLdb.connect(**server_db)
    curs = conn.cursor(DictCursor)
    curs.execute("SELECT sample_event_ID,REPLACE(title,'\\'','') title,REPLACE(OntologyTerm,'\\'','') OntologyTerm,OntologyID,sample_size,study,ecosystem,ecocolor FROM `samples_unified` natural join samples_sizes_unified natural join samples_EnvO_annotation_unified natural join envoColors where `sample_event_ID` ='"+msampleid+"'")
    title=""
    OntologyTerm=[]
    ecosystem=[]
    sample_size=0
    sample_event_ID=None
    study_source=""
    ecocolor=[]
    for rec in curs.fetchall():
        #print rec["sample_event_ID"]
	if sample_event_ID==None:
	  sample_event_ID=rec["sample_event_ID"]
	  title=rec["title"]
	  OntologyTerm.append(str(rec["OntologyID"]+","+rec["OntologyTerm"]))
	  sample_size=float(rec["sample_size"])
	  study_source=retrieve_source(rec["study"])
	  ecosystem.append(rec["ecosystem"])
	  ecocolor.append(rec["ecocolor"])
	else:
	  if str(rec["OntologyID"]+","+rec["OntologyTerm"]) not in OntologyTerm:
		OntologyTerm.append(str(rec["OntologyID"]+","+rec["OntologyTerm"]))
	  if rec["ecosystem"] not in ecosystem:
		ecosystem.append(rec["ecosystem"])
	  if rec["ecocolor"] not in ecocolor:
		ecocolor.append(rec["ecocolor"])
    #print len(ecocolor)
    if len(ecocolor)==0:
	ecocolor.append("White")

    while len(ecocolor)!=3:
	#print ecocolor
	ecocolor.append(ecocolor[len(ecocolor)-1])
	#print ecocolor

    conn.close()
    return title,OntologyTerm,sample_size,study_source,ecosystem,ecocolor

def envo_data(msampleids):
    conn = MySQLdb.connect(**server_db)
    curs = conn.cursor(DictCursor)
    curs.execute("SELECT REPLACE(OntologyTerm,'\\'','') OntologyTerm,OntologyID,ecosystem FROM `samples_unified` natural join samples_EnvO_annotation_unified natural join envoColors where `sample_event_ID` in ('"+msampleids+"')")

    title=""
    OntologyTerm=[]
    sample_size=0
    sample_event_ID=None
    study_source=""
    ecosystem=[]
    ecocolor=[]
    maxcnt=0
    for rec in curs.fetchall():
        if str(rec["OntologyID"]+","+rec["OntologyTerm"]) not in OntologyTerm:
	  OntologyTerm.append(str(rec["OntologyID"]+","+rec["OntologyTerm"]))
	if rec["ecosystem"] not in ecosystem:
	  ecosystem.append(rec["ecosystem"])

    conn.close()
    return title,OntologyTerm,sample_size,study_source,ecosystem,ecocolor


def json_for_dendrogam(mnMatrix,mnsampleid):

    SampleIds=mnsampleid
    id2name = dict(zip(range(len(mnsampleid)), mnsampleid))
    MNsample_dict=dict(zip(mnsampleid,range(0,len(mnsampleid))))
    mMatrix=mnMatrix
    Z= sch.linkage(mMatrix,method='average')


    T = sch.to_tree(Z, rd=False )
    z_dict=dict(zip(np.append(Z[:,0],Z[:,1]),np.append(Z[:,2],Z[:,2])))
    z_dict[np.amax(Z[:,0:2])+1]=np.amax(Z[:,2])

    d3Dendro = dict(children=[], name="Root1")

    add_node(T,d3Dendro)

    label_tree( d3Dendro["children"][0],id2name,z_dict)
    #print d3Dendro
    return d3Dendro
