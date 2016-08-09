from biom_table_generator import biom_from_sample
from biom import Table
from biom.parse import parse_biom_table
from nonphylogentic_distance_transform import (
    adaptivebray_curtis, adaptive_bray_curtis, bray_curtis
)
import json
import numpy as np

def calculate_MNmatrix(mMatrix, Msample, n_sample_otu_matrix, n_otu_id):
    """Wrapper function to calculate the adaptive Bray-Curtis distance for
    the input sample and queried samples.
    """
    # generate biom table object based on queried samples
    otutableL = parse_biom_table(json.dumps(biom_from_sample(Msample)))

    m_sample_otu_matrix = np.asarray(
        [v for v in otutableL.iter_data(axis="sample")]
    )

    m_otu_id = otutableL.ids(axis="observation")
    m_sample_id = otutableL.ids(axis="sample")

    # caulculate adaptive Bray-Curtis distances
    nMatrix = adaptivebray_curtis(n_sample_otu_matrix, list(n_otu_id))
    m_nMatrix = adaptive_bray_curtis(m_sample_otu_matrix, list(m_otu_id),
                                     n_sample_otu_matrix, list(n_otu_id))
    mnMatrix = np.vstack(
        (np.hstack((mMatrix, m_nMatrix)),
         np.hstack((np.transpose(m_nMatrix), nMatrix)))
    )

    return mnMatrix
