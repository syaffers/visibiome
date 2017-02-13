from MySQLdb.cursors import DictCursor
from scipy.spatial.distance import squareform
from config import server_db
import MySQLdb
import cogent.cluster.metric_scaling as ms
import itertools
import json
import numpy as np
import os
import scipy.cluster.hierarchy as sch


class Sample:
    def __init__(self, rank, name, title,
                 ontology_id_1, ontology_term_1,
                 ontology_id_2, ontology_term_2,
                 ontology_id_3, ontology_term_3,
                 sample_size, distance, study_source):
    	self.Ranking = rank
    	self.Name = name
    	self.Study = title

    	if ontology_id_1 == "":
            self.S_EnvO_1 = " "
    	else:
            self.S_EnvO_1 = ontology_id_1 + ", " + ontology_term_1

    	if ontology_id_2 == "":
            self.S_EnvO_2 = " "
    	else:
            self.S_EnvO_2 = ontology_id_2 + ", " + ontology_term_2

    	if ontology_id_3 == "":
            self.S_EnvO_3 = " "
    	else:
            self.S_EnvO_3 = ontology_id_3 + ", " + ontology_term_3

    	self.Total_Sample_Size = sample_size
    	self.Total_Distance = distance
    	self.Study_Source = study_source


def retrieve_source(sample_study):
    """String replacing subroutine"""
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


def generate_samples_metadata(mnMatrix, mnsampleid, m_sampleid, filepath):
    MNsample_dict = dict(zip(mnsampleid, range(0, len(mnsampleid))))

    sample_json = dict(sample=[])
    sample_metadata = []

    msampleids='\',\''.join(m_sampleid)
    json_metadata_query = """
        SELECT DISTINCT sample_event_ID, title, OntologyTerm, OntologyID,
            sample_size, study
        FROM `samples_unified`
        NATURAL JOIN samples_sizes_unified
        NATURAL JOIN samples_EnvO_annotation_unified
        NATURAL JOIN envoColors
        WHERE `sample_event_ID`
        IN ('{m_sample_ids}')
        ORDER BY FIELD(sample_event_ID, '{m_sample_ids}')
    """.format(m_sample_ids=msampleids)

    conn = MySQLdb.connect(**server_db)
    curs = conn.cursor(DictCursor)
    curs.execute(json_metadata_query)

    authors_list = title = study = ""
    ontology_terms = ["", "", ""]
    ontology_ids = ["", "", ""]
    cnt = distance = rank = sample_size = 0
    sample_event_id = None

    for row in curs.fetchall():
        curr_sample_event_id = row["sample_event_ID"]
        curr_sample_size = row["sample_size"]
        curr_study = row["study"]
        curr_title = row["title"]
        ontology_term = row["OntologyTerm"]
        ontology_id = row["OntologyID"]

        if sample_event_id is None:
            sample_event_id = curr_sample_event_id
            title = curr_title
            ontology_terms[cnt] = ontology_term
            ontology_ids[cnt] = ontology_id
            sample_size = float(curr_sample_size)
            distance = "%.4f" %mnMatrix[MNsample_dict[sample_event_id]]
            study = retrieve_source(curr_study)

        elif sample_event_id != curr_sample_event_id:
            rank = rank + 1
            sample_metadata.append(vars(
                Sample(rank, sample_event_id, title,
                       ontology_ids[0], ontology_terms[0],
                       ontology_ids[1], ontology_terms[1],
                       ontology_ids[2], ontology_terms[2],
                       sample_size, distance, study
                )
            ))
            sample_event_id = curr_sample_event_id
            title = curr_title
            ontology_terms = ["", "", ""]
            ontology_ids = ["", "", ""]
            cnt = 0
            ontology_terms[cnt] = ontology_term
            ontology_ids[cnt] = ontology_id
            sample_size = float(curr_sample_size)
            distance = "%.4f" % mnMatrix[MNsample_dict[sample_event_id]]
            study = retrieve_source(curr_study)

        else:
            ontology_terms[cnt] = ontology_term
            ontology_ids[cnt] = ontology_id

        cnt = cnt + 1

    rank = rank + 1
    sample_metadata.append(vars(
        Sample(rank, sample_event_id, title,
               ontology_ids[0], ontology_terms[0],
               ontology_ids[1], ontology_terms[1],
               ontology_ids[2], ontology_terms[2],
               sample_size, distance, study
        )
    ))

    sample_json['sample'] = sample_metadata
    conn.close()

    with open(filepath, "w") as json_output_file:
        json.dump(sample_json, json_output_file, sort_keys=True,
                  indent=4)


def get_sorted_representative_id(distmn, mn_sample_id, rankingcount):
    """Get the top ranking representative OTU IDs

    :param distmn: Numpy array matrix of distances
    :param mn_sample_id: List of strings containing sample IDs
    :param rankingcount: Integer number of OTUs to be returned
    :return: List of strings containing top ranking OTU IDs
    """
    sample_dict = dict(enumerate(mn_sample_id))
    idx = np.argsort(distmn[len(distmn)-1])

    samples = [str(sample_dict[i]) for i in idx]
    samples_20 = []
    samples_20 = samples[1:rankingcount]

    return samples_20


def generate_heatmap_files(distmtx, sample_id, sample_id_2, userdir,
                           rankingcount):
    """Make all heatmap-related files for D3.js drawings: large heatmap and
    small heatmap. Generates CSV files.

    :param distmtx: Numpy array matrix of distances
    :param sample_id: List of strings containing first sample IDs
    :param sample_id_2: List of strings containing second sample IDs
    :param userdir: User directory path to which the file will be written
    :param rankingcount: Integer number of OTUs to be returned
    :return: Numpy array small distance matrix to be used for dendrogram
    generation
    """
    f_heatmap_all_nodes = open(os.path.join(userdir,
        "All_heatmap_nodelist.csv"), "w")
    f_heatmap_all_edges = open(os.path.join(userdir,
        "All_heatmap_edgelist.csv"), "w")
    f_heatmap_top_nodes = open(os.path.join(userdir, "top_nodelist.csv"), "w")
    f_heatmap_top_edges = open(os.path.join(userdir, "top_edgelist.csv"), "w")
    samples_mn = sample_id + sample_id_2

    sample_dict = dict(enumerate(samples_mn))
    idx = np.argsort(distmtx[len(distmtx)-1])
    distmtx = distmtx[:,idx]
    idx = np.argsort(distmtx[:,0])
    distmtx = distmtx[idx,:]

    samples = [str(sample_dict[i]) for i in idx]
    samples_10 = []

    samples_10 = samples[:rankingcount]
    samples_list_10 = samples[:rankingcount]
    f_heatmap_all_nodes.write("id"+'\n')
    for items in samples:
        f_heatmap_all_nodes.write(str(items)+ "\n")
    f_heatmap_top_nodes.write("id"+'\n')
    for items in samples_10:
        f_heatmap_top_nodes.write(str(items)+ "\n")

    distmtx_top_10 = distmtx[:rankingcount, :rankingcount]
    samples = list(itertools.combinations(samples, 2))
    samples_10 = list(itertools.combinations(samples_10, 2))
    distmtx_square_all = squareform(distmtx, 'tovector')
    distmtx_square_top_10 = squareform(distmtx_top_10, 'tovector')
    combine = zip(samples, distmtx_square_all)
    combine_top_10 = zip(samples_10, distmtx_square_top_10)

    f_heatmap_all_edges.write("source,target,weight"+'\n')
    for items in combine:
        temp = str(items)
        temp = temp.replace(")", "")
        temp = temp.replace("(", "")
        temp = temp.replace("'", "")
        temp = temp.replace(" ", "")
        f_heatmap_all_edges.write(temp + "\n")

    f_heatmap_top_edges.write("source,target,weight"+'\n')
    for items in combine_top_10:
        temp = str(items)
        temp = temp.replace(")", "")
        temp = temp.replace("(", "")
        temp = temp.replace("'", "")
        temp = temp.replace(" ", "")
        f_heatmap_top_edges.write(temp + "\n")

    f_heatmap_all_nodes.close()
    f_heatmap_all_edges.close()
    f_heatmap_top_nodes.close()
    f_heatmap_top_edges.close()

    return distmtx_top_10, samples_list_10


def query_pcoa_metadata(msampleid):
    """Subroutine to query for PCOA metadata"""
    pcoa_metadata_query = """
        SELECT sample_event_ID, REPLACE(title, "'", "") title,
        REPLACE(OntologyTerm, "'", "") OntologyTerm, OntologyID, sample_size,
        study, ecosystem
        FROM `samples_unified`
        NATURAL JOIN samples_sizes_unified
        NATURAL JOIN samples_EnvO_annotation_unified
        NATURAL JOIN envoColors
        WHERE `sample_event_ID` = '{m_sample_id}'
    """.format(m_sample_id=msampleid)

    # connect to the database and form query
    conn = MySQLdb.connect(**server_db)
    curs = conn.cursor(DictCursor)
    curs.execute(pcoa_metadata_query)

    # prepare variables
    title = study_source = ""
    otcnt = oicnt = ecnt = sample_size = 0
    ontology_terms = ["Unknown", "Unknown", "Unknown"]
    ontology_ids = ["Unknown", "Unknown", "Unknown"]
    ecosystems = ["Unknown", "Unknown", "Unknown"]
    sample_event_id = None

    # for each row in the query
    for row in curs.fetchall():
        ontology_term = row["OntologyTerm"].strip()
        ontology_id = row["OntologyID"].strip()
        ecosystem = row["ecosystem"].strip()

        # first run
        if sample_event_id is None:
            sample_event_id = row["sample_event_ID"].strip()
            title = row["title"].strip().replace(',', '')
            sample_size = float(row["sample_size"])
            ontology_terms[otcnt] = ontology_term.replace(',', '')
            ontology_ids[oicnt] = ontology_id.strip()
            ecosystems[ecnt] = ecosystem.strip()
            otcnt = otcnt + 1
            oicnt = oicnt + 1
            ecnt = ecnt + 1

        # all other runs
        else:
            if ontology_id not in ontology_ids and oicnt < 3:
                ontology_ids[oicnt] = ontology_id
                oicnt = oicnt + 1
            if ontology_term not in ontology_terms and otcnt < 3:
                ontology_terms[otcnt] = ontology_term
                otcnt = otcnt + 1
            if ecosystem not in ecosystems and ecnt < 3:
                ecosystems[ecnt] = ecosystem
                ecnt = ecnt + 1

    conn.close()
    return (title,
       ontology_ids[0], ontology_terms[0],
       ontology_ids[1], ontology_terms[1],
       ontology_ids[2], ontology_terms[2],
       sample_size, study_source,
       ecosystems[0], ecosystems[1], ecosystems[2]
    )


def generate_pcoa_file(distmtx, samples, filepath):
    """Make PCoA-related file for D3.js drawings. Generates CSV file.

    :param distmtx: Numpy array matrix of distances
    :param samples: List of strings containing sample IDs
    :param userdir: User directory path to which the file will be written
    """
    with open(filepath, "w") as f_pcoa:
        coords, eigvals = ms.principal_coordinates_analysis(distmtx)
        pcnts = (np.abs(eigvals) / float(sum(np.abs(eigvals)))) * 100
        idxs_descending = pcnts.argsort()[::-1]
        coords = coords[idxs_descending]
        # eigvals = eigvals[idxs_descending]
        # pcnts = pcnts[idxs_descending]

        header = "Sample Name,PC1,PC2,PC3,Title,OntologyID1,OntologyTerm1,"
        header += "OntologyID2,OntologyTerm2,OntologyID3,OntologyTerm3,"
        header += "Sample Size,Study Source,Ecosystem1,Ecosystem2,Ecosystem3\n"

        f_pcoa.write(header)
        for i in zip(samples, coords.T[:,0], coords.T[:,1], coords.T[:,2]):
            res = str(i + query_pcoa_metadata(i[0])).replace("u\'","")\
                      .replace("\'","").replace("(","").replace(")","")
            f_pcoa.write(res + "\n")


def add_dendrogram_node(node, parent):
    """Subroutine for dendrogram generation"""
    # First create the new node and append it to its parent's children
    new_node = dict(node_id=node.id, children=[])
    parent["children"].append(new_node)

    # Recursively add the current node's children
    if node.left:
        add_dendrogram_node(node.left, new_node)
    if node.right:
        add_dendrogram_node(node.right, new_node)


def label_dendrogram_tree(n, id2name, z_dict):
    """Subroutine for dendrogram generation"""
    # If the node is a leaf, then we have its name
    if len(n["children"]) == 0:
        leaf_names = [id2name[n["node_id"]]]
        n["length"] = z_dict[float(n["node_id"])] * 100

    # If not, flatten all the leaves in the node's subtree
    else:
        leaf_names = reduce(
            lambda ls, c: ls + label_dendrogram_tree(c, id2name, z_dict),
            n["children"], []
        )
        n["length"] = (z_dict[float(n["node_id"])] \
            - z_dict[float(n["children"][0]['node_id'])]) * 100


    # Delete the node id since we don't need it anymore and
    # it makes for cleaner JSON
    n["node_id"]

    # Labeling convention: "-"-separated leaf names
    name = "-".join(sorted(map(str, leaf_names)))

    if name.find("-") == -1:
        n["name"] = name
        title, ontology_terms, sample_size, study_source, ecosystems, \
            ecocolors = query_dendrogram_metadata(name)

    else:
        n["name"] = str(name.count("-") + 1)
        msampleids = name.replace("-",'\',\'')
        title, ontology_terms, sample_size, study_source, ecosystems, \
            ecocolors = query_dendrogram_envo(msampleids)

    n["title"] = title
    n["OntologyTerm"] = ontology_terms
    n["study_source"] = study_source
    n["ecosystem"] = ecosystems
    n["ecocolor"] = ecocolors

    return leaf_names


def query_dendrogram_metadata(m_sample_id):
    """Subroutine for dendrogram generation"""
    dendrogram_metadata_query = """
        SELECT sample_event_ID, REPLACE(title, "'", "") title,
        REPLACE(OntologyTerm, "'", "") OntologyTerm, OntologyID, sample_size,
        study, ecosystem, ecocolor
        FROM `samples_unified`
        NATURAL JOIN samples_sizes_unified
        NATURAL JOIN samples_EnvO_annotation_unified
        NATURAL JOIN envoColors
        WHERE `sample_event_ID` = '{m_sample_id}'
    """.format(m_sample_id=m_sample_id)

    # connect to database and perform query
    conn = MySQLdb.connect(**server_db)
    curs = conn.cursor(DictCursor)
    curs.execute(dendrogram_metadata_query)

    # prepare variables
    sample_event_id = None
    sample_size = 0
    title = study_source = ""
    ontology_terms = []
    ecosystems = []
    ecocolors = []

    for row in curs.fetchall():
        ontology_term = str(row["OntologyID"] + "," + row["OntologyTerm"])
        ecosystem = row["ecosystem"]
        ecocolor = row["ecocolor"]

        if sample_event_id == None:
            sample_event_id = row["sample_event_ID"]
            title = row["title"]
            sample_size = float(row["sample_size"])
            study_source = retrieve_source(row["study"])
            ontology_terms.append(ontology_term)
            ecosystems.append(ecosystem)
            ecocolors.append(ecocolor)

        else:
            if ontology_term not in ontology_terms:
                ontology_terms.append(ontology_term)
            if ecosystem not in ecosystems:
                ecosystems.append(ecosystem)
            if ecocolor not in ecocolors:
                ecocolors.append(ecocolor)


    if len(ecocolors) == 0:
        ecocolors.append("White")
    while len(ecocolors) < 3:
        ecocolors.append(ecocolors[len(ecocolors) - 1])

    conn.close()
    return (title, ontology_terms, sample_size, study_source, ecosystems,
            ecocolors)


def query_dendrogram_envo(m_sample_ids):
    """Subroutine for dendrogram generation"""
    dendrogram_envo_query = """
        SELECT REPLACE(OntologyTerm, "'", "") OntologyTerm, OntologyID,
        ecosystem
        FROM `samples_unified`
        NATURAL JOIN samples_EnvO_annotation_unified
        NATURAL JOIN envoColors
        WHERE `sample_event_ID` in ('{m_sample_ids}')
    """.format(m_sample_ids=m_sample_ids)

    # connect to database and perform query
    conn = MySQLdb.connect(**server_db)
    curs = conn.cursor(DictCursor)
    curs.execute(dendrogram_envo_query)

    # prepare variables
    title = study_source = ""
    sample_size = maxcnt = 0
    sample_event_ID = None
    ontology_terms = []
    ecosystems = []
    ecocolors = []

    for row in curs.fetchall():
        ontology_term = str(row["OntologyID"] + "," + row["OntologyTerm"])
        ecosystem = row["ecosystem"]
        if ontology_term not in ontology_terms:
            ontology_terms.append(ontology_term)
        if ecosystem not in ecosystems:
            ecosystems.append(ecosystem)

    conn.close()
    return (title, ontology_terms, sample_size, study_source, ecosystems,
            ecocolors)


def generate_dendrogram_file(mnMatrix, mnsampleid, filepath):
    """Make dendrogram-related file for d3 drawings. Generates JSON file.

    :param mnMatrix: Numpy array matrix of distances
    :param mnsampleid: List of strings containing sample IDs
    :param userdir: User directory path to which the file will be written
    """
    id2name = dict(zip(range(len(mnsampleid)), mnsampleid))
    MNsample_dict = dict(zip(mnsampleid, range(0, len(mnsampleid))))
    mMatrix = mnMatrix
    Z = sch.linkage(mMatrix, method='average')

    T = sch.to_tree(Z, rd=False)
    z_dict = dict(zip(np.append(Z[:,0], Z[:,1]), np.append(Z[:,2], Z[:,2])))
    z_dict[np.amax(Z[:, 0:2]) + 1] = np.amax(Z[:, 2])

    dendrogram = dict(children=[], name="Root1")
    add_dendrogram_node(T, dendrogram)
    label_dendrogram_tree(dendrogram["children"][0], id2name, z_dict)

    with open(filepath, "w") as json_output_file:
        print("Writing to file {}...".format(filepath))
        json.dump(dendrogram, json_output_file, sort_keys=True, indent=4)
