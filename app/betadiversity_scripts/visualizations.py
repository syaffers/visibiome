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
from collections import defaultdict
from django.conf import settings
from matplotlib import colors as mcolors

class Sample:
    def __init__(self, rank, name, title,
                 ontology_id_1, ontology_term_1,
                 ontology_id_2, ontology_term_2,
                 ontology_id_3, ontology_term_3,
                 sample_size, distance, pvalue, study_source, link,
                 barcharts=None):
        self.Ranking = rank
        self.Name = name
        self.Study = title
        self.pvalue = pvalue

        if not ontology_id_1: ## could be empty string or None
            self.S_EnvO_1 = " "
        else:
            self.S_EnvO_1 = ontology_id_1 + ", " + ontology_term_1

        if not ontology_id_2:
            self.S_EnvO_2 = " "
        else:
            self.S_EnvO_2 = ontology_id_2 + ", " + ontology_term_2

        if not ontology_id_3:
            self.S_EnvO_3 = " "
        else:
            self.S_EnvO_3 = ontology_id_3 + ", " + ontology_term_3

        self.Total_Sample_Size = sample_size
        self.Total_Distance = distance
        self.Study_Source = study_source
        self.Link = link
        if not barcharts is None:
            self.barchart_genus = barcharts[1]
            self.barchart_family = barcharts[2]
            self.barchart_phylum = barcharts[0]

    def is_empty(self):
        return (self.Name == None           and \
                self.Ranking == 1           and \
                self.Study == ""            and \
                self.pvalue == 1            and \
                self.S_EnvO_1 == " "        and \
                self.S_EnvO_2 == " "        and \
                self.S_EnvO_3 == " "        and \
                self.Total_Sample_Size == 0 and \
                self.Total_Distance == 0    and \
                self.Study_Source == "")


def retrieve_source(sample_study, sampleID=None):
    """String replacing subroutine"""
    mgrast_link = "http://metagenomics.anl.gov/linkin.cgi?project=mgp"
    emb_link = "https://qiita.ucsd.edu/study/description/"
    chaffron_paper = "http://www.genome.org/cgi/doi/10.1101/gr.104521.109"
    sra_link = 'https://trace.ncbi.nlm.nih.gov/Traces/sra/?run='

    if sample_study.find('CHA_') != -1:
        return ("Chaffron Data", chaffron_paper)

    elif sample_study.find('QDB_') != -1:
        study_id = sample_study.split("QDB_")[1]
        return ("Earth Microbiome Project/QiimeDB/Qiita", emb_link + study_id)

    elif sample_study.find('MI_MIT_') != -1:
        return ("MI MIT Sequencing", None)

    elif sample_study.find('SRA_') != -1:
        return ("SRA Data", sra_link + sampleID)

    elif sample_study.find('MGRAST_') != -1:
        study_id = sample_study.split("MGRAST_")[1]
        return ("MgRAST Data", mgrast_link + study_id)

    else:
        return ("Unknown", None)


def generate_samples_metadata(m_n_df, n_sample_ids, filepath, top=20, barcharts=None):
    ## TODO: do this consistently with pandas DataFrames!
    ## TODO: assert that distmtx is symmetric when ranking=None, should be
    # import cPickle
    # with open('/tmp/input.pcl', 'w') as input:
    #     cPickle.dump((top_m_n_distmtx,top_m_n_sample_ids, n_sample_ids,filepath,ranking), input)

    # connect to microbiome database
    conn = MySQLdb.connect(**server_db)
    all_samples_dict = dict()
    pvalues = np.load(os.path.join(settings.L_MATRIX_DATA_PATH, 'distanceProbability.npy'))

    # for each user-submitted sample
    for sample_id_j in n_sample_ids:
        rankingOfMatchedSamples = []
        # rearrange distance matrix for the jth sample and get sample IDs
        top_m_j_sample_ids = list(m_n_df.sort_values(sample_id_j)[sample_id_j].dropna(axis=0).index)

        # get the top m sample IDs without losing order
        top_m_sample_ids = [m_sample_id for m_sample_id in top_m_j_sample_ids
                            if m_sample_id not in n_sample_ids][:top]
        print "Matches (sorted) for", top_m_sample_ids

        json_metadata_query = """
            SELECT DISTINCT s.sample_event_ID, title, ea.OntologyTerm, ea.OntologyID, sample_size, s.study
            FROM samples_unified s
            LEFT JOIN samples_sizes_unified ss ON s.sample_event_ID = ss.sample_event_ID
            LEFT JOIN samples_EnvO_annotation_unified ea ON s.sample_event_ID = ea.sample_event_ID
            WHERE s.sample_event_ID
            IN ('{m_sample_ids}')
            ORDER BY FIELD(s.sample_event_ID, '{m_sample_ids}')
        """.format(m_sample_ids='\',\''.join(top_m_sample_ids))

        #print json_metadata_query
        curs = conn.cursor(DictCursor) ## creating a cursor inside the loop?
        n = curs.execute(json_metadata_query)
        #print len(top_m_j_sample_ids), len(top_m_sample_ids), n
        authors_list = title = study = ""
        ontology_terms = ["", "", ""]
        ontology_ids = ["", "", ""]
        cnt = distance = rank = sample_size = 0
        sample_event_id = None
        pvalue = 1
        link = None

        annotatedSamples = set({})
        for row in curs.fetchall():
            sample_id_i = row["sample_event_ID"]
            annotatedSamples.add(sample_id_i)
            sample_size_i = row["sample_size"]
            study_i = row["study"] or ''
            title_i = row["title"] or ''
            ontology_term = row["OntologyTerm"] or ''
            ontology_id = row["OntologyID"] or ''

            # first run
            if sample_event_id is None:
                sample_event_id = sample_id_i
                title = title_i
                ontology_terms[cnt] = ontology_term
                ontology_ids[cnt] = ontology_id
                sample_size = float(sample_size_i)
                distance = "%.4f" % m_n_df[sample_id_j][sample_id_i]
                pvalue = pvalues[min(int(m_n_df[sample_id_j][sample_id_i]*10000),9999)]

                study, link = retrieve_source(study_i, sample_event_id)

            # when we encounter a new sample from database
            elif sample_event_id != sample_id_i:
                rank = rank + 1

                rankingOfMatchedSamples.append(vars(
                    Sample(rank, sample_event_id, title,
                           ontology_ids[0], ontology_terms[0],
                           ontology_ids[1], ontology_terms[1],
                           ontology_ids[2], ontology_terms[2],
                           sample_size, distance, pvalue, study, link
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
                pvalue = pvalues[min(int(m_n_df[sample_id_j][sample_id_i] * 10000), 9999)]

                study, link = retrieve_source(study_i, sample_event_id)

            # if its the same sample
            else:
                ontology_terms[cnt] = ontology_term
                ontology_ids[cnt] = ontology_id

            cnt = cnt + 1


        rank = rank + 1

        sample_object = Sample(rank, sample_event_id, title,
               ontology_ids[0], ontology_terms[0],
               ontology_ids[1], ontology_terms[1],
               ontology_ids[2], ontology_terms[2],
               sample_size, distance, pvalue, study, link
        )

        # check if no matches were found, if so then just append a null
        if sample_object.is_empty():
            rankingOfMatchedSamples.append(None)
        else:
            rankingOfMatchedSamples.append(vars(sample_object))

        noInfoSamples = set(top_m_j_sample_ids).difference(annotatedSamples)
        if noInfoSamples:
            #print "Matches for %s" % sample_id_i
            print "!!! No sample info was retrieved for %s" % noInfoSamples
            if len(noInfoSamples) > 10:
                print json_metadata_query

        all_samples_dict[sample_id_j] = {
            "ranking": rankingOfMatchedSamples,
            "barcharts": barcharts[sample_id_j] if barcharts else None
        }


    # close connection once everything is done
    conn.close()
    print filepath
    with open(filepath, "w") as json_output_file:
        json.dump(all_samples_dict, json_output_file, sort_keys=True, separators=(',',':'))

def generate_barcharts(searchresults, filepath, selectedRanks):
    '''Drawing pairwise stacked barcharts of compositions, connecting corresponding fractions by lines.
       Latest version uses mpld3 to be hooked up with d3 javascript library
       Possible TODO: instead of pairwise'''
    import cPickle

    def cutoff_sample_id(sample_id, cutoff=4):
        if len(sample_id) > cutoff:
            return sample_id[:cutoff] + "..."
        return sample_id

    def comparativeBarchart(df, rank, drawLegend=False, figsaveInfo=""):
        tooltip_html = "Sample: %s<br>Clade: %s<br>Abundance: %.2f%%"
        colors = [colorDict[rank][phyl] for phyl in df.columns.values]
        df.columns = [taxa if taxa else '(unassigned)' for taxa in df.columns.values]

        ## Stacked bar chart for convenient visual comparison
        ax = df.plot.bar(width=0.2, stacked=True, legend=drawLegend, color=colors,
                         figsize=(4, 3)) # Syafiq: figures are too big for the page, I need to minify
        ## Beautifying the plot

        ax.set_xticklabels(map(cutoff_sample_id, df.index.values), rotation='horizontal')
        ax.set_ylabel('Relative abundance')
        ax.set_ylim(0, 1)

        box = ax.get_position()
        ax.set_position([box.x0, box.y0 + box.height * 0.10, box.width, box.height * 0.90])

        ## drawing all corresponding lines and mpld3 tooltip labels
        m,n = df.shape ## this way I can directly use Syafiq's code
        xs = []
        ys = []
        for j in range(0, n * m, m):
            for i in range(m):
                p = ax.patches[j + i]
                bw = p.get_width() / 2.
                xs.append(p.get_x() + p.get_width() / 2.)  # constant for each bar
                ys.append(p.get_y() + p.get_height() / 2.)

                if i > 0:
                    xsys = ([xs[j + i - 1] + bw, xs[j + i] - bw],
                            [ys[j + i - 1], ys[j + i]])
                    line = ax.plot(xsys[0], xsys[1],
                                   color=p.get_facecolor(), linewidth=3)[0]
                    #line_label = "OTU%d --- OTU%d" % (j / m, j / m)
                    #line_label = "%s: %.2f%% vs %.2f%%" % (taxon, 100 * patch1.get_height(), 100 * patch2.get_height())
                    #tooltip = mpld3.plugins.LineLabelTooltip(line, label='yo!')
                    #mpld3.plugins.connect(ax.get_figure(), tooltip)
        for i, patch in enumerate(ax.patches):
            clade_name = df.columns.values[int(i / float(m))]
            relative_abundance = 100. * patch.get_height()
            sample_name = df.index.values[i % m]
            tooltip = mpld3.plugins.PointHTMLTooltip(
                patch, labels=[tooltip_html % (sample_name, clade_name, relative_abundance)]
            )

            mpld3.plugins.connect(ax.get_figure(), tooltip)

        fig = ax.get_figure()
        #filetype = 'html' #json ## change back to json!!!

        #filename1 = os.path.join('/tmp/', "%s___%s.%s" % (userSample.sampleID, rank, filetype))
        #print "Trying to save %s" % filename
        svgfile = "%s/bar__%s__%s.svg" % (os.path.splitext(filepath)[0], figsaveInfo, rank)
        print "Saving bar diagram in %s" % svgfile
        plt.savefig(svgfile)
        figdict =  mpld3.fig_to_dict(fig) ## encountered issues with save_html
        if not figdict:
            print "Warning: no figure generated:",
            filename = os.path.join(filepath, "%s___%s.%s" % (userSample.sampleID, rank, 'svg'))
            plt.savefig(filename)
            print df.head()
        #with open(filename, 'w') as w:
        #    print >> w, html
        #with open(filename, 'w') as w:
        #    print >> w, html

        #mpld3.save_html(fig, filename)
        #saveFct = getattr(mpld3, 'save_%s' % filetype)
        #saveFct(fig, filename)
        #fig.savefig(filename) ## could also just save the svg/png (without all mpld3 wizzardry)
        return figdict

    def groupby(rank, sample):
        df = sample.composition.groupby(rank).sum()


        df.columns = [sample.sampleID]
        print df.head()
        return df
    ## creating color dicts for consistent coloring
    conn = MySQLdb.connect(**server_db)
    curs = conn.cursor()
    colors = np.array(mcolors.cnames.values())
    colorDict = {}
    for rank in selectedRanks: ## TODO: create remaining colordicts
        np.random.shuffle(colors)
        curs.execute('SELECT DISTINCT `%s` FROM OTUS_unified' %rank)
        clades = curs.fetchall()
        colorDict[rank] = dict([(clades[i][0], colors[i%len(colors)]) for i in range(len(clades))])
    conn.close()
    barcharts = defaultdict(dict)


    for result in searchresults:
        userSample = result.qsample
        if result.ranking:
            matchSamples = list(zip(*result.ranking)[1][:5])
            #print "### Top 5 for %s"%(userSample.sampleID), [(s.sampleID, d) for d,s in gnatresult.ranking][:10]
            for rank in selectedRanks:
                taxaGroupedTables = [groupby(rank, sample) for sample in [userSample] + matchSamples]
                #print taxaGroupedTables
                combinedAbundances = pd.concat(taxaGroupedTables, axis=1, join='outer').fillna(0.00001)
                combinedAbundances.sort_values(userSample.sampleID, inplace=True, ascending=False)
                barcharts[userSample.sampleID][rank] = comparativeBarchart(combinedAbundances.T, rank, figsaveInfo=userSample.sampleID)
        else:
            print "Warning: no ranking found for query sample", userSample.sampleID
    return barcharts



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
        study_source, link = retrieve_source(row["study"].strip(), row["sample_event_ID"])

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


def generate_pcoa_file(distmtx, m_n_sample_ids, n_sample_ids, filepath):
    """Make PCoA-related file for D3.js drawings. Generates CSV file.

    :param distmtx: Numpy array matrix of distances
    :param m_n_sample_ids: List of strings containing m and n sample IDs
    :param n_sample_ids: List of strings containing user (or n) sample IDs
    :param filepath: User directory path to which the file will be written
    """
    coords, eigvals = ms.principal_coordinates_analysis(distmtx)
    pcnts = (np.abs(eigvals) / float(sum(np.abs(eigvals)))) * 100
    idxs_descending = pcnts.argsort()[::-1]
    coords = coords[idxs_descending]

    # from google10c
    #print "Distance Matrix distmtx"
    #print distmtx, coords
    print 'm_n_sample_ids' + str(len(m_n_sample_ids)), m_n_sample_ids
    print "n_sample_ids" + str(len(n_sample_ids)), n_sample_ids
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

    """Okay messy indexing coming up! eco_samples_idx holds a list of sample
    indices for each ecosystem that is queried (along with color) e.g. {
        ("Biofilm", "grey"): [1,12,...],
        ("Soil", "gold"): [3,16,...]
    }.
    envo_samples_idx holds a list of sample indices for each envo that is
    queried (along with color) e.g. {
        ("ENVO:00009003", "blue"): [1,12,...],
        ("ENVO:00000073", "red"): [3,16,...]
    }.
    tooltip_htmls contains the html formatted string of the metadata for each
    sample. Metdata is a tuple of (title, ontology_ids, ontology_terms,
    ecosystem, study_source, color)
    """
    m_sample_ids = [sample_id for sample_id in m_n_sample_ids
                    if not sample_id in n_sample_ids]
    user_key = ("User Samples", "red")
    eco_samples_idx = {user_key: []}
    envo_samples_idx = {user_key: []}
    tooltip_htmls = [""] * len(m_n_sample_ids)

    # all other samples excluding user samples
    for sample_id in m_sample_ids:
        metadata = query_pcoa_metadata(sample_id)
        tooltip_htmls[m_n_sample_ids.index(sample_id)] = tooltip_html.format(
            sample_id, metadata[3], ", ".join(metadata[1]),
            ", ".join(metadata[2]), metadata[0], metadata[4]
        )

        color_id = len(envo_samples_idx)
        eco_term = metadata[3]
        eco_color = metadata[5]
        envo_term = metadata[1][0]
        eco_key = (eco_term, eco_color)
        # if the envo has already been encountered before, don't add a new sample
        if envo_term in map(lambda x: x[0], envo_samples_idx):
            envo_color = filter(lambda x: x[0] == envo_term, envo_samples_idx)[0][1]
            envo_key = (envo_term, envo_color)
        else:
            envo_key = (envo_term, colormap[color_id % len(colormap)])

        if eco_key in eco_samples_idx:
            eco_samples_idx[eco_key].append(m_n_sample_ids.index(sample_id))
        else:
            eco_samples_idx[eco_key] = [m_n_sample_ids.index(sample_id)]

        if envo_key in envo_samples_idx:
            envo_samples_idx[envo_key].append(m_n_sample_ids.index(sample_id))
        else:
            envo_samples_idx[envo_key] = [m_n_sample_ids.index(sample_id)]

    # add user samples to eco_samples_idx, envo_samples_idx and html_tooltips
    for sample_id_j in n_sample_ids:
        envo_samples_idx[user_key].append(m_n_sample_ids.index(sample_id_j))
        eco_samples_idx[user_key].append(m_n_sample_ids.index(sample_id_j))
        tooltip_htmls[m_n_sample_ids.index(sample_id_j)] = tooltip_html.format(
            sample_id_j, user_key[0], user_key[0], user_key[0], "", ""
        )

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
            svgfile = "%s_PC%s%s_%s.svg" %((os.path.splitext(filepath)[0],) + plot_name)
            print "Saving PCoA in %s" % svgfile
            plt.savefig(svgfile)

    """ FINISH! """
    with open(filepath, "w") as f_pcoa:
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
            study_source, link = retrieve_source(row["study"], row["sample_event_ID"])
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
        json.dump(dendrogram, json_output_file, sort_keys=True, separators=(',',':'))
