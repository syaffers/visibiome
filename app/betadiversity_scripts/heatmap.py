import numpy as np
import itertools
from scipy.spatial.distance import squareform


def get_sorted_representative_id(Distmn, mnSample_id, rankingcount):
    """Get the top ranking representative OTU IDs

    :param Distmn: Numpy array matrix of distances
    :param mnSample_id: List of strings containing sample IDs
    :param rankingcount: Integer number of OTUs to be returned
    :return: List of strings containing top ranking OTU IDs
    """
    Sample_dict = dict(enumerate(mnSample_id))
    idx = np.argsort(Distmn[len(Distmn)-1])

    Samples = [str(Sample_dict[i]) for i in idx]
    Samples_20 = []
    Samples_20 = Samples[1:rankingcount]

    return Samples_20


def heatmap_files(Distmn, Sample_id, Sample_id2, userdir, rankingcount):
    """Make all heatmap-related files for D3.js drawings: large heatmap and
    small heatmap. Generates CSV files.

    :param Distmn: Numpy array matrix of distances
    :param Sample_id: List of strings containing first sample IDs
    :param Sample_id2: List of strings containing second sample IDs
    :param userdir: User directory path to which the file will be written
    :param rankingcount: Integer number of OTUs to be returned
    :return: Numpy array small distance matrix to be used for dendrogram
    generation
    """
    f_heatmap_all_nodes = open(userdir + "All_heatmap_nodelist.csv", "w")
    f_heatmap_all_edges = open(userdir + "All_heatmap_edgelist.csv", "w")
    f_heatmap_top_nodes = open(userdir + "top_nodelist.csv", "w")
    f_heatmap_top_edges = open(userdir + "top_edgelist.csv", "w")
    Samples_nm = Sample_id + Sample_id2

    Sample_dict = dict(enumerate(Samples_nm))
    idx = np.argsort(Distmn[len(Distmn)-1])
    Distmn = Distmn[:,idx]
    idx = np.argsort(Distmn[:,0])
    Distmn = Distmn[idx,:]

    Samples = [str(Sample_dict[i]) for i in idx]
    Samples_10 = []

    Samples_10 = Samples[:rankingcount]
    Sampleslist_10 = Samples[:rankingcount]
    f_heatmap_all_nodes.write("id"+'\n')
    for items in Samples:
        f_heatmap_all_nodes.write(str(items)+ "\n")
    f_heatmap_top_nodes.write("id"+'\n')
    for items in Samples_10:
        f_heatmap_top_nodes.write(str(items)+ "\n")

    Distmn_top10 = Distmn[:rankingcount, :rankingcount]
    Samples = list(itertools.combinations(Samples, 2))
    Samples_10 = list(itertools.combinations(Samples_10, 2))
    DM_squareAll = squareform(Distmn, 'tovector')
    DM_square_top10 = squareform(Distmn_top10, 'tovector')
    Combine = zip(Samples, DM_squareAll)
    Combine_top10 = zip(Samples_10, DM_square_top10)

    f_heatmap_all_edges.write("source,target,weight"+'\n')
    for items in Combine:
        temp = str(items)
        temp = temp.replace(")", "")
        temp = temp.replace("(", "")
        temp = temp.replace("'", "")
        temp = temp.replace(" ", "")
        f_heatmap_all_edges.write(temp + "\n")

    f_heatmap_top_edges.write("source,target,weight"+'\n')
    for items in Combine_top10:
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

    return Distmn_top10, Sampleslist_10
