from MySQLdb.cursors import DictCursor
from scipy.spatial.distance import squareform
from config import server_db
from mpld3.plugins import InteractiveLegendPlugin, PointHTMLTooltip
import MySQLdb
import cogent.cluster.metric_scaling as ms
import itertools
import json
import matplotlib.pyplot as plt
import mpld3
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


def generate_samples_metadata(m_n_df, n_sample_ids, filepath, top=20):
    ## TODO: do this consistently with pandas DataFrames!
    ## TODO: assert that distmtx is symmetric when ranking=None, should be
    # import cPickle
    # with open('/tmp/input.pcl', 'w') as input:
    #     cPickle.dump((top_m_n_distmtx,top_m_n_sample_ids, n_sample_ids,filepath,ranking), input)

    # SYAFIQ: I've updated the function to include the m_n_df dataframe
    # in the arguments, Bray-curtis calcs are handling this too. You can clear
    # this comment as needed

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
                            if m_sample_id not in n_sample_ids][:top]
        ## we could actually allow other user samples
        ### SYAFIQ: I agree, in that case, we should include the top 20 + all the
        ### user samples after query but we have to be careful since the loop
        ### below only considers the samples which are in the database
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
                # pvalue = 1


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
                # pvalue = 1

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


def generate_heatmap_files(m_n_distmtx, m_n_sample_ids, userdir, rankingcount):
    """Make all heatmap-related files for D3.js drawings: large heatmap and
    small heatmap. Generates CSV files.

    :param m_n_distmtx: Numpy array matrix of distances
    :param m_n_sample_ids: List of strings containing sample IDs from M and N
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

    sample_dict = dict(enumerate(m_n_sample_ids))
    # sort last row
    idx = np.argsort(m_n_distmtx[-1])
    sorted_m_n_distmtx = m_n_distmtx[:,idx]
    # sort first column
    idx = np.argsort(sorted_m_n_distmtx[:,0])
    sorted_m_n_distmtx = sorted_m_n_distmtx[idx,:]

    sorted_m_n_sample_ids = [str(sample_dict[i]) for i in idx]
    top_sorted_m_n_distmtx = sorted_m_n_distmtx[:rankingcount, :rankingcount]
    top_sorted_m_n_sample_ids = sorted_m_n_sample_ids[:rankingcount]

    f_heatmap_all_nodes.write("id" + '\n')
    for sample_id in sorted_m_n_sample_ids:
        f_heatmap_all_nodes.write(str(sample_id) + "\n")
    f_heatmap_top_nodes.write("id" + '\n')
    for sample_id in top_sorted_m_n_sample_ids:
        f_heatmap_top_nodes.write(str(sample_id) + "\n")

    m_n_sample_id_pairs = list(
        itertools.combinations(sorted_m_n_sample_ids, 2)
    )
    top_m_n_sample_id_pairs = list(
        itertools.combinations(top_sorted_m_n_sample_ids, 2)
    )
    pairwise_distvec = squareform(sorted_m_n_distmtx, 'tovector')
    top_pairwise_distvec = squareform(top_sorted_m_n_distmtx, 'tovector')
    edge_tuples = zip(m_n_sample_id_pairs, pairwise_distvec)
    top_edge_tuples = zip(top_m_n_sample_id_pairs, top_pairwise_distvec)

    f_heatmap_all_edges.write("source,target,weight\n")
    for sample_ids, distance in edge_tuples:
        f_heatmap_all_edges.write("%s,%s,%s\n" %
                                  (sample_ids[0], sample_ids[1], distance))

    f_heatmap_top_edges.write("source,target,weight\n")
    for sample_ids, distance in top_edge_tuples:
        f_heatmap_top_edges.write("%s,%s,%s\n" %
                                  (sample_ids[0], sample_ids[1], distance))

    f_heatmap_all_nodes.close()
    f_heatmap_all_edges.close()
    f_heatmap_top_nodes.close()
    f_heatmap_top_edges.close()

    return top_sorted_m_n_distmtx, top_sorted_m_n_sample_ids


def query_pcoa_metadata(sample_id):
    """Subroutine to query for PCOA metadata"""
    pcoa_metadata_query = """
        SELECT sample_event_ID, REPLACE(title, "'", "") title,
        REPLACE(OntologyTerm, "'", "") OntologyTerm, OntologyID,
        study, ecosystem, ecocolor
        FROM `samples_unified`
        NATURAL JOIN samples_sizes_unified
        NATURAL JOIN samples_EnvO_annotation_unified
        NATURAL JOIN envoColors
        WHERE `sample_event_ID` = '{sample_id}'
    """.format(sample_id=sample_id)

    # connect to the database and form query
    conn = MySQLdb.connect(**server_db)
    curs = conn.cursor(DictCursor)
    curs.execute(pcoa_metadata_query)

    # prepare variables
    title = study_source = ""
    otcnt = oicnt = ecnt = 0
    ontology_terms = ["Unknown", "Unknown", "Unknown"]
    ontology_ids = ["Unknown", "Unknown", "Unknown"]
    ecosystems = ["Unknown", "Unknown", "Unknown"]
    sample_event_id = None
    ecocolor = "black"

    # for each row in the query
    for row in curs.fetchall():
        ontology_term = row["OntologyTerm"].strip()
        ontology_id = row["OntologyID"].strip()
        ecosystem = row["ecosystem"].strip()
        study_source = retrieve_source(row["study"].strip())

        # first run
        if sample_event_id is None:
            sample_event_id = row["sample_event_ID"].strip()
            title = row["title"].strip().replace(',', '')
            ontology_terms[otcnt] = ontology_term.replace(',', '')
            ontology_ids[oicnt] = ontology_id.strip()
            ecosystems[ecnt] = ecosystem.strip()
            ecocolor = row["ecocolor"].strip()
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

    # cleaning ontology IDs
    if ontology_terms[0] is not "Unknown" and ontology_ids[0] is not "Unknown":
        ontology_terms = [ot for ot in ontology_terms if not ot is "Unknown"]
        ontology_ids = [oi for oi in ontology_ids if not oi is "Unknown"]
    else:
        ontology_ids, ontology_terms = [["Unknown"], ["Unknown"]]
        ecosystems = ["Unknown"]

    return (title, ontology_ids, ontology_terms, ecosystems[0], study_source, ecocolor)


def generate_pcoa_file(distmtx, sample_ids, filepath):
    """Make PCoA-related file for D3.js drawings. Generates CSV file.

    :param distmtx: Numpy array matrix of distances
    :param sample_ids: List of strings containing sample IDs
    :param filepath: User directory path to which the file will be written
    """
    with open(filepath, "w") as f_pcoa:
        coords, eigvals = ms.principal_coordinates_analysis(distmtx)
        pcnts = (np.abs(eigvals) / float(sum(np.abs(eigvals)))) * 100
        idxs_descending = pcnts.argsort()[::-1]
        coords = coords[idxs_descending]

        colormap = [
            "#3366cc", "#dc3912", "#ff9900", "#109618", "#990099", "#0099c6", "#dd4477",
            "#66aa00", "#b82e2e", "#316395", "#994499", "#22aa99", "#aaaa11", "#6633cc",
            "#e67300", "#8b0707", "#651067", "#329262", "#5574a6", "#3b3eac"
        ]

        tooltip_html = """
        Sample: {}<br>
        Ecosystem: {}<br>
        Envo ID: {}<br>
        Envo Term: {}<br>
        Study: {} <br>
        Study Source: {}
        """

        """Okay messy indexing coming up! eco_samples_idx holds a list
        of sample indices for each ecosystem that is queried (along with
        color) e.g. {
            ("Biofilm", "grey"): [1,12,...],
            ("Soil", "gold"): [3,16,...]
        }.
        envo_samples_idx holds a list of sample indices for each envo that
        is queried (along witg color) e.g. {
            ENVO:00009003": [1,12,...],
            ENVO:00000073": [3,16,...]
        }.
        tooltip_htmls contains the html formatted string of the metadata
        for each sample. Metdata is a tuple of (title, ontology_ids,
        ontology_terms, ecosystem, study_source, color)
        """
        user_key = ("Unknown", "black")
        eco_samples_idx = dict()
        envo_samples_idx = dict()
        tooltip_htmls = []
        for sample_index, sample_id in enumerate(sample_ids):
            metadata = query_pcoa_metadata(sample_id)
            tooltip_htmls.append(
                tooltip_html.format(
                    sample_id, metadata[3], ", ".join(metadata[1]),
                    ", ".join(metadata[2]), metadata[0], metadata[4]
                )
            )

            color_id = len(envo_samples_idx)
            eco_term = metadata[3]
            eco_color = metadata[5]
            envo_term = metadata[1][0]
            eco_key = (eco_term, eco_color)
            if eco_term is "Unknown":
                envo_key = user_key
            else:
                if envo_term in map(lambda x: x[0], envo_samples_idx):
                    envo_color = filter(lambda x: x[0] == envo_term, envo_samples_idx)[0][1]
                    envo_key = (envo_term, envo_color)
                else:
                    envo_key = (envo_term, colormap[color_id % len(colormap)])

            if eco_key in eco_samples_idx:
                eco_samples_idx[eco_key].append(sample_index)
            else:
                eco_samples_idx[eco_key] = [sample_index]

            if envo_key in envo_samples_idx:
                envo_samples_idx[envo_key].append(sample_index)
            else:
                envo_samples_idx[envo_key] = [sample_index]

        """ PLOTTING """

        plots = {}
        # loop through groupings
        for group in ["ecosystem", "envo"]:
            # loop through each top 3 pairs of principal coordinates
            for pc1, pc2 in itertools.combinations(range(3), 2):
                # start the plot
                fig, ax = plt.subplots()
                fig.set_figwidth(11)

                # plot all the points except for the users samples, they go last
                group_samples_idx = eco_samples_idx
                non_user_group_samples_idx = [e for e in eco_samples_idx.keys()
                                              if not e == user_key]
                if group is "envo":
                    group_samples_idx = envo_samples_idx
                    non_user_group_samples_idx = [e for e in envo_samples_idx.keys()
                                                  if not e == user_key]

                # scatter the ecosystem-labelled points
                # remember that the keys are in the format
                # ("Ecosystem/Envo", "Color")
                for key in non_user_group_samples_idx:
                    ax.scatter(
                        coords.T[group_samples_idx[key], pc1],
                        coords.T[group_samples_idx[key], pc2],
                        marker="o", label=key[0], color=key[1], alpha=1
                    )

                # plot user samples
                ax.scatter(
                    coords.T[group_samples_idx[user_key], pc1],
                    coords.T[group_samples_idx[user_key], pc2],
                    marker="*", s=96, label=user_key[0], color=user_key[1], alpha=1
                )

                # draw PC axis labels
                ax.set_xlabel("PC%d" % (pc1 + 1))
                ax.set_ylabel("PC%d" % (pc2 + 1))
                ax.set_title("PCoA Plot grouped by %s" % (group.capitalize()))

                # adjust the plot abit for the legend for sample legend
                box = ax.get_position()
                ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])

                """INTERACTIVITY"""

                # make interactive legends for sample groupings
                if group is "ecosystem":
                    handles, legend_labels = ax.get_legend_handles_labels()
                    interactive_legend = InteractiveLegendPlugin(
                        zip(handles, ax.collections), legend_labels, alpha_unsel=0.3,
                        alpha_over=1, start_visible=False)

                    mpld3.plugins.connect(fig, interactive_legend)

                # make interactive html labels for non-user samples first, since
                # they are now ordered
                html_labels = np.array(tooltip_htmls)
                for i, key in enumerate(non_user_group_samples_idx):
                    tooltip = PointHTMLTooltip(
                        ax.collections[i],
                        labels=list(html_labels[group_samples_idx[key]])
                    )
                    mpld3.plugins.connect(fig, tooltip)

                # make interactive html labels for user samples
                tooltip = PointHTMLTooltip(
                    ax.collections[-1],
                    labels=list(html_labels[group_samples_idx[user_key]])
                )
                mpld3.plugins.connect(fig, tooltip)

                plot_name = (pc1 + 1, pc2 + 1, group.capitalize())
                plots["PC%d%d%s" % plot_name] = mpld3.fig_to_dict(fig)

        """ FINISH! """
        json.dump(plots, f_pcoa)


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
