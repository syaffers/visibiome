from MySQLdb.cursors import DictCursor
from scipy.spatial.distance import squareform
from config import server_db
import MySQLdb
import cogent.cluster.metric_scaling as ms
import itertools
import json
import numpy as np
import os
import pandas as pd
import scipy.cluster.hierarchy as sch


class Sample:
    def __init__(self, rank, name, title,
                 ontology_id_1, ontology_term_1,
                 ontology_id_2, ontology_term_2,
                 ontology_id_3, ontology_term_3,
                 sample_size, distance, pvalue, study_source):
    	self.Ranking = rank
    	self.Name = name
    	self.Study = title
        self.pvalue = pvalue

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


def generate_samples_metadata(top_m_n_distmtx, top_m_n_sample_ids,
                              n_sample_ids, filepath, rankingDF=None):
    ## TODO: do this consistently with pandas DataFrames!
    ## TODO: assert that distmtx is symmetric when ranking=None, should be
    import cPickle
#    with open('/tmp/input.pcl', 'w') as input:
#        cPickle.dump((top_m_n_distmtx,top_m_n_sample_ids, n_sample_ids,filepath,ranking), input)

    m_n_df = pd.DataFrame(top_m_n_distmtx, columns=top_m_n_sample_ids,
                          index=top_m_n_sample_ids) if rankingDF is None else rankingDF
    if not rankingDF is None: ## DEBUG Info, 2b rm'd
        print "received Ranking (from GNAT)"
        print rankingDF.head()
    # connect to microbiome database
    conn = MySQLdb.connect(**server_db)
    all_samples_dict = dict()
    pvalues = np.load('%s/distanceProbability.npy')
    # for each user-submitted sample
    for sample_id_j in n_sample_ids:
        sample_metadata = []
        # rearrange distance matrix for the jth sample and get sample IDs
        ## New: deals with NaN values, individually (from GNAT ranking)
        top_m_j_sample_ids = list(m_n_df.sort(sample_id_j)[sample_id_j].dropna(axis=0).index)
        print "Matches (sorted) for", sample_id_j, list(m_n_df.sort(sample_id_j).index)[:10]
        # get the top m sample IDs without losing order
        top_m_sample_ids = [m_sample_id for m_sample_id in top_m_j_sample_ids
                            if m_sample_id not in n_sample_ids]## we could actually allow other user samples
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
        """.format(m_sample_ids='\',\''.join(top_m_sample_ids))

        #print json_metadata_query
        curs = conn.cursor(DictCursor)
        n = curs.execute(json_metadata_query)
        #print len(top_m_j_sample_ids), len(top_m_sample_ids), n
        authors_list = title = study = ""
        ontology_terms = ["", "", ""]
        ontology_ids = ["", "", ""]
        cnt = distance = rank = sample_size = 0
        sample_event_id = None

        for row in curs.fetchall():
            sample_id_i = row["sample_event_ID"]
            sample_size_i = row["sample_size"]
            study_i = row["study"]
            title_i = row["title"]
            ontology_term = row["OntologyTerm"]
            ontology_id = row["OntologyID"]

            # first run
            if sample_event_id is None:
                sample_event_id = sample_id_i
                title = title_i
                ontology_terms[cnt] = ontology_term
                ontology_ids[cnt] = ontology_id
                sample_size = float(sample_size_i)

                distance = "%.4f" % m_n_df[sample_id_j][sample_id_i]
                pvalue = pvalues[max(int(distance*10000),9999)]


                study = retrieve_source(study_i)

            # when we encounter a new sample from database
            elif sample_event_id != sample_id_i:
                rank = rank + 1

                sample_metadata.append(vars(
                    Sample(rank, sample_event_id, title,
                           ontology_ids[0], ontology_terms[0],
                           ontology_ids[1], ontology_terms[1],
                           ontology_ids[2], ontology_terms[2],
                           sample_size, distance, pvalue, study
                    )
                ))
                # create new sample
                sample_event_id = sample_id_i
                title = title_i
                ontology_terms = ["", "", ""]
                ontology_ids = ["", "", ""]
                cnt = 0
                ontology_terms[cnt] = ontology_term
                ontology_ids[cnt] = ontology_id
                sample_size = float(sample_size_i)
                distance = "%.4f" % m_n_df[sample_id_j][sample_id_i]
                pvalue = pvalues[max(int(distance * 10000), 9999)]

                study = retrieve_source(study_i)

            # if its the same sample
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
                   sample_size, distance, pvalue, study
            )
        ))


        all_samples_dict[sample_id_j] = sample_metadata


    # close connection once everything is done
    conn.close()

    with open(filepath, "w") as json_output_file:
        json.dump(all_samples_dict, json_output_file, sort_keys=True, indent=4)


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


def generate_heatmap_files(m_n_df, filepath, node_count, n_sample_count):
    """Make all heatmap-related files for D3.js drawings: large heatmap and
    small heatmap. Generates CSV files.

    :param m_n_df: Pandas DataFrame of the M + N distance matrix with samples
    on the axes
    :param filepath: User directory path to which the file will be written
    :param rankingcount: Integer number of OTUs to be returned
    :return: Numpy array small distance matrix to be used for dendrogram
    generation
    """
    f_heatmap_all_nodes = open(os.path.join(filepath, "All_heatmap_nodelist.csv"), "w")
    f_heatmap_all_edges = open(os.path.join(filepath, "All_heatmap_edgelist.csv"), "w")
    # f_heatmap_top_nodes = open(os.path.join(filepath, "top_nodelist.csv"), "w")
    # f_heatmap_top_edges = open(os.path.join(filepath, "top_edgelist.csv"), "w")

    n_top_sample_ids = []
    sorted_m_n_sample_ids = []
    for sample_id_j in m_n_df.columns[-n_sample_count:]:
        n_top_sample_ids.append(list(m_n_df.sort(sample_id_j).index))

    i = 0
    while len(sorted_m_n_sample_ids) < (node_count + n_sample_count):
        for j in range(n_sample_count):
            if n_top_sample_ids[j][i] not in sorted_m_n_sample_ids:
                sorted_m_n_sample_ids.append(n_top_sample_ids[j][i])
        i += 1

    sorted_m_n_distmtx = m_n_df.ix[sorted_m_n_sample_ids, sorted_m_n_sample_ids].as_matrix()
    """ NOT NEEDED """

    f_heatmap_all_nodes.write("id" + '\n')
    for sample_id in sorted_m_n_sample_ids:
        f_heatmap_all_nodes.write(str(sample_id) + "\n")
    # f_heatmap_top_nodes.write("id" + '\n')
    # for sample_id in top_sorted_m_n_sample_ids:
    #     f_heatmap_top_nodes.write(str(sample_id) + "\n")
    """ NOT NEEDED """

    m_n_sample_id_pairs = list(
        itertools.combinations(sorted_m_n_sample_ids, 2)
    )
    # top_m_n_sample_id_pairs = list(
    #     itertools.combinations(top_sorted_m_n_sample_ids, 2)
    # )
    """ NOT NEEDED """

    pairwise_distvec = squareform(sorted_m_n_distmtx, 'tovector')
    edge_tuples = zip(m_n_sample_id_pairs, pairwise_distvec)
    # top_pairwise_distvec = squareform(top_sorted_m_n_distmtx, 'tovector')
    # top_edge_tuples = zip(top_m_n_sample_id_pairs, top_pairwise_distvec)
    """ NOT NEEDED """

    f_heatmap_all_edges.write("source,target,weight\n")
    for sample_ids, distance in edge_tuples:
        f_heatmap_all_edges.write("%s,%s,%s\n" %
                                  (sample_ids[0], sample_ids[1], distance))

    # f_heatmap_top_edges.write("source,target,weight\n")
    # for sample_ids, distance in top_edge_tuples:
    #     f_heatmap_top_edges.write("%s,%s,%s\n" %
    #                               (sample_ids[0], sample_ids[1], distance))
    """ NOT NEEDED """

    f_heatmap_all_nodes.close()
    f_heatmap_all_edges.close()
    # f_heatmap_top_nodes.close()
    # f_heatmap_top_edges.close()
    """ NOT NEEDED """


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
    :param filepath: User directory path to which the file will be written
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

    print mnMatrix.shape, filepath
    with open(filepath, "w") as json_output_file:
        print("Writing to file {}...".format(filepath))
        json.dump(dendrogram, json_output_file, sort_keys=True, indent=4)
