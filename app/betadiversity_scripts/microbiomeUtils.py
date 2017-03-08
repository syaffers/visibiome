"""

toolkit of functions and classes  that was previously used to calculate all pairwise Unifrac distances for 24615 samples, that have been saved in two separate files per sample:
one for occurring OTU names, one for abundances ## could altenatively just have been a biom tabel with one row

Latest addition to sample class: is able to perform pair-wise adaptive rarefaction, in conjunction with the little
wrapper function 'rarefy'

Latest addition: emdusparse:
optimized version of EMDUnifrac, using sparse vectors and just propagating non-zero
loads in a strictly level-based  bootom-up approach
Much faster!

adapted from EMDUnifrac (biorxiv/github, also python) see:


"""
#from EMDUnifrac import EMDUnifrac_weighted_plain, parse_tree_file
import numpy as np
from collections import Counter
import cPickle
import scipy.sparse
from collections import defaultdict
from itertools import izip
import pandas as pd

def emdusparse(Tint, lint, indexLevelDict, maxlevel, i,j, reportNodes=False):
    ## Adapted from EMDUnifrac
    ## Consider using networkx graph for Tint, lint, indexLevelDict, nodes_to_index etc, much less hassle
    ## initializing dicts for all levels (maybe some unused), so to do stricly level-based bottom up!
    ## Difficulty was with uneven depths
    ## was considering priority queues, but they might spoil the complexity
    eps = 1e-08
    diff = i-j
    ## creating list of dictionaries
    levels = [(level, defaultdict(float)) for level in range(maxlevel+1)]
    ## Preparing the stage, inserting the initial differences into the acc. level-dict
    for index, val in izip(diff.indices, diff.data):
        level = indexLevelDict[index]
        levels[level][1][index] = val
    Z = 0
    visitedNodes = set([])
    while levels:
        currentLevel, currentLevelDict = levels.pop()
        if currentLevel == 0: break ## reached root
        for node, value in currentLevelDict.items():
            visitedNodes.add(node)
            parent = Tint[node]
            if abs(value) > eps: # go on if there is really more "earth" to propagate to the ancestry
                parentLevel = currentLevel-1
                levels[parentLevel][1][parent] += value
                Z += lint[node] * abs(value)
    if reportNodes:
        return Z, len(visitedNodes)
    else:
        return Z

class Sample:
    """ Sample objects, precalculated from sql database
        contain: 1. list of otus, 2. sequence counts, 3. sum of 2."""
    def __init__(self, sampleID='Sabkha', datadir=None, key=None):
        self.sampleID = sampleID
        self.key=key
        with open("%s/%s_otus.pcl" %(datadir, sampleID)) as f:
            self.otus = cPickle.load(f)
        self.seqCounts = np.load("%s/%s_sc.npy" %(datadir, sampleID))
        self.size = len(self.seqCounts)
        self.seqP = self.seqCounts/float(self.seqCounts.sum())
        #self.calcP()
        #self.compactPdict = dict(zip(self.otus,self.seqP))
    def subsample(self, size):
        return Counter(np.random.choice(self.otus, size, replace=True, p=self.seqP))
    def adaptRarefy(self, minSize, nodes_to_index, sparse=False, rare=True):
        """Calculates relative abundance of rarefied abundance"""
        if not sparse:
            l = np.zeros(len(nodes_to_index))
            for otu, count in self.subsample(minSize).items():
                l[nodes_to_index[otu]] = count/float(minSize)
            return l
        else:
            if rare:
                otus, seqP = zip(*self.subsample(minSize).items())
                seqP = np.array(seqP)
                seqP = seqP / float(seqP.sum())
            else:
                ## only produces sparse vector from sample info without rarefaction
                otus, seqP = self.otus, self.seqP
            indices = [nodes_to_index[otu] for otu in otus]
            return scipy.sparse.csc_matrix((seqP, (indices, np.zeros(len(indices), dtype=int))), shape=(len(nodes_to_index),1))
    def calcP(self, nodes_to_index):
        ## Legacy code, not used, as it is not adaptively rarefying...
        indices = [nodes_to_index[otu] for otu in self.otus]
        self.p = scipy.sparse.csc_matrix((self.seqP, (indices, np.zeros(self.size))), shape=(len(nodes_to_index),1))
        return self.p

    def computeComposition(self, curs):
        '''creates nice dataframe with otu_id as index:
         1. reads lineage info from SQL db -> dataframe df
         2. otus/seqCounts -> dataframe df0
         3. joins them
         Convenient barchart construction: df.groupby(['phylum']).sum()
         Only needed for query matches that are top ranked!
        '''
        ## this requires EArthMicroBiome!!
        columns = 'otu_id phylum family genus'.split()
        lineageQuery = "SELECT %s FROM OTUS_unified WHERE otu_id IN (%s)"
        query = lineageQuery % (','.join(columns), ','.join(["'%s'"%otu for otu in self.otus]))

        curs.execute(query)
        records = list(curs.fetchall())
        df = pd.DataFrame(records, columns=columns)
        df.set_index('otu_id', inplace=True)
        df0 = pd.DataFrame(zip(self.otus, self.seqP), columns=['otu_id', 'rel_abundance'])
        df0.set_index('otu_id', inplace=True)
        self.composition = pd.concat([df, df0], axis=1, join='inner')


class UserSample(Sample):
    '''receiving a possibly sparse abundance vector and in pos. accordance, otu names (otus)'''
    def __init__(self, sampleID, vector, otus):
        self.sampleID = sampleID
        self.key = None
        seqCounts, self.otus = zip(*[(abund, otu) for abund,otu in zip(vector, otus) if not np.isnan(abund) and abund > 0])
        self.seqCounts  = np.array(seqCounts)
        self.size = len(self.seqCounts)
        self.seqP = self.seqCounts / float(self.seqCounts.sum())

class SQLSample(Sample):
    '''Extract sample info from DB, just given id and open cursor'''
    def __init__(self, sampleID, curs):
        curs.execute("SELECT otu_id, normalized_count FROM OTUS_samples_unified WHERE sample_event_id = '%s'" % sampleID)
        vectorOtus = curs.fetchall()
        self.sampleID = sampleID
        self.key = None
        self.otus, seqCounts = zip(*vectorOtus)
        self.seqCounts  = np.array(seqCounts)
        self.size = len(self.seqCounts)
        self.seqP = self.seqCounts / float(self.seqCounts.sum())

def rarefy(sample1, sample2, nodes_to_index, sparse=False, rare=True):
    '''Pairwise adaptive rarefaction, if rare is false, just make sparse vectors'''
    minSize = min(sample1.size, sample2.size)
    s1r = sample1.adaptRarefy(minSize, nodes_to_index, sparse=sparse, rare=rare)
    s2r = sample2.adaptRarefy(minSize, nodes_to_index, sparse=sparse, rare=rare)
    return s1r, s2r

