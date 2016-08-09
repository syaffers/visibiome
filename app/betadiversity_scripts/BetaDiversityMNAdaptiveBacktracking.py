from JSon_metadata import create_json_samples_metadata
from MNBetadiversity import calculate_MNmatrix
from MySQLdb.cursors import DictCursor
from PCOA import pcoa
from biom.parse import parse_biom_table
# from biom.table import DenseTable # not used
from config import server_db
from dendrogam_d3_json import json_for_dendrogam
from heatmap import heatmap_files, get_sorted_representative_id
from select_samples import return_represent_sample, return_rep_original_samples
import MySQLdb
import json
import numpy as np
import sys


# def betadiversity(largedata, userbiom, userdir, user_choice):

largedata = sys.argv[1]
userbiom = sys.argv[2]
userdir = sys.argv[3]
user_choice = sys.argv[4].split(",")

# betadiversity(largedata, userbiom, userdir, user_choice)

st = "Worked"
try:
    # load submitted biom file/text into otutableS
    # legacy code for biom-format 1.x
    # if isinstance(otutableS, DenseTable):
    #     n_sample_otu_matrix = otutableS._data.T
    # else:
    #     n_sample_otu_matrix = np.asarray(
    #         [v for v in otutableS.iterSampleData()]
    #     )
    print("\nParsing input BIOM table... ({})".format(__file__))
    otutableS = parse_biom_table(open(userbiom, "U"))
    n_sample_otu_matrix = np.asarray(
        [v for v in otutableS.iter_data(axis="sample")]
    )

    # get observation IDs and sample IDs from submitted biom file
    # legacy code for biom-format 1.x
    # n_otuid = otutableS.ObservationIds
    # n_sampleid = list(otutableS.SampleIds)
    print("\nGetting observations and samples from BIOM table... ({})".format(__file__))
    n_otu_id = otutableS.ids(axis="observation")
    n_sample_id = list(otutableS.ids(axis="sample"))

    # stringify tuple of observation IDs
    notuids = str(tuple(map(int, n_otu_id)))

    # preparing SQL query to get 16s copy number of each observation IDs
    print("\nMaking query string... ({})".format(__file__))
    query_str = """
    SELECT 16s_copy_number
    FROM OTUS_unified
    WHERE otu_id IN {sample_list_tuple}
    ORDER BY FIELD(otu_id, {sample_list_string})
    """.format(sample_list_tuple=notuids, sample_list_string=notuids[1:-1])

    # perform query
    print("\nPerforming database query... ({})".format(__file__))
    conn = MySQLdb.connect(**server_db)
    curs = conn.cursor(DictCursor)
    curs.execute(query_str)

    # convert 16s otu copy numbers into doubles for math manipulations
    otu_copy_number = np.array(
        [float(rec["16s_copy_number"]) for rec in curs.fetchall()]
    )
    conn.close()

    # if there are observation IDs which are not in DB, exit with message
    # if len(otu_copy_number) != len(n_otuid):
    if len(otu_copy_number) != len(n_otu_id):
        st = "Some OTU not present"

    # otherwise if all observation IDs are in the DB
    else:
        print("\nPerforming M-N Betadiversity Calculation... ({})".format(__file__))
        n_sample_otu_matrix = n_sample_otu_matrix / otu_copy_number

        # retrieve the samples need to compute diversity against using
        # representatives
        mMatrix, Msample = return_represent_sample(largedata, user_choice)

        # if submatrix of 10k matrix and queried sample is returned
        # properly
        if len(mMatrix) != 0 and len(Msample) != 0:
            print("\nFirst run of MN calculation... ({})".format(__file__))
            mnMatrix = calculate_MNmatrix(
                # legacy code
                # mMatrix, Msample, n_sample_otu_matrix, n_otuid
                mMatrix, Msample, n_sample_otu_matrix, n_otu_id
            )
            n_sam=["o"]
            n_sam[0]=str(n_sample_id[0])

            print("\nEnd.")

            #================== END OF MAIN COMPUTATION ==================#

            # 1000 dendogram
            print("\nGenerating 1000 dendrograms... ({})".format(__file__))
            d3Dendro = json_for_dendrogam(mnMatrix, Msample + n_sam)
            json.dump(d3Dendro, open(userdir + "d3dendrogram.json", "w"),
                      sort_keys=True, indent=4)

            # pcoa for 1000 samples
            print("\nGenerating 1000 PCoA... ({})".format(__file__))
            pcoa(mnMatrix, Msample + n_sam, userdir)

            # get top ranking representative OTU IDs
            # legacy code
            # m_repsampleid = get_sortedrepresentativeid(
            m_repsampleid = get_sorted_representative_id(
                mnMatrix, Msample + n_sample_id, 251
            )
            # TODO: Redoing the MN calculation? What's a representative
            # OTU?
            mMatrix, Msample = return_rep_original_samples(
                list(m_repsampleid), largedata, user_choice, 250
            )
            mnMatrix = calculate_MNmatrix(
                mMatrix, Msample, n_sample_otu_matrix, n_otu_id
            )

            # for top 251 dendogram
            print("\nGenerating 250 dendrograms... ({})".format(__file__))
            d3Dendro = json_for_dendrogam(mnMatrix, Msample + n_sample_id)
            json.dump(d3Dendro,
                      open(userdir + "d3dendrogram_sub.json", "w"),
                      sort_keys=True, indent=4)

            # for closest 250 samples
            print("\nGenerating 250 PCoA... ({})".format(__file__))
            pcoa(mnMatrix, Msample + n_sam, userdir + "250_")
            submnMatrix, submn_sample_id = heatmap_files(
                mnMatrix, Msample, n_sample_id, userdir, 21
            )

            # for 21 dendogram
            print("\nGenerating 21 dendrograms... ({})".format(__file__))
            d3Dendro = json_for_dendrogam(submnMatrix, submn_sample_id)
            json.dump(d3Dendro,
                      open(userdir + "d3dendrogram_sub_sub.json", "w"),
                      sort_keys=True, indent=4)

            samplejson = create_json_samples_metadata(
                submnMatrix[0, :], submn_sample_id, submn_sample_id[1:],
                userdir
            )

            json.dump(
                samplejson,
                open(userdir + n_sample_id[0].replace('.','_')+".json", "w"),
                sort_keys=True, indent=4
            )


# except:
#     st="error"

finally:
    fo = open(userdir + "onesampleval.txt","w")
    fo.write(st)
    fo.close()
