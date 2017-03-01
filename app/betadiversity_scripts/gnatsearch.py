import cPickle
import h5py
import dask.array as da
import numpy as np
import glob
import sys, os
import pandas as pd
import scipy.sparse
import MySQLdb
import pdb
from coord_util import gnat
# datastructure  got pickled
from collections import defaultdict
from itertools import izip

from microbiomeUtils import emdusparse, UserSample, SQLSample, rarefy
# from django.conf import settings ## This needs a fix!!! Syafiq
#
# settings.configure()
# from config import server_db

def add_refs(gnatnode, db, metric):
    gnatnode.db = db
    gnatnode.metric = metric
    for subtree in gnatnode.subtrees:
        if not isinstance(subtree, int):
            add_refs(subtree, db, metric)

def load_gnat(name, db, metric):
    with open(name) as f:
        gnatz = cPickle.load(f)
    add_refs(gnatz, db, metric)
    return gnatz

class EMDUnifrac(gnat.Metric): ## see better version in gnatbuild.py!
    def __init__(self, rare=True, l_data_path=None):
        treedataFile = "%s/gg13_97_otus2.pcl" % (l_data_path)
        with open(treedataFile) as f:
            self.Tint, self.lint, self.nodes_in_order, self.nodes_to_index, self.maxlevel, self.indexLevelDict = cPickle.load(f)

        self.rare = rare
        self.counter = 0
        self.computedDistances = {}
        self.topSamples = {}

    def dist(self, sample1, sample2): ## now samples are just a list of tuples
        self.counter += 1

        ## adaptive rarefaction (if rare) + making a sparse vector from samples
        i, j = rarefy(sample1, sample2, self.nodes_to_index, sparse=True, rare=self.rare)
        ## emdusparse = EMD Unifrac with sparse vectors
        d = emdusparse(self.Tint, self.lint, self.indexLevelDict, self.maxlevel, i, j)
        self.computedDistances[(sample1.sampleID, sample2.sampleID)] = d
        # remember top samples for later, for convenience, the entire sample object (ref) is kept
        # Alternatively keep them in MicrobiomeSQLDB (get_sample), but
        # that would keep ALL samples, not just close matches
        if d<0.3:
            ## resorted to dict over list, both have same creation time, but dict is nonredundant
            self.topSamples[sample2.sampleID] = sample2
        return d

class MicrobiomeSQLDB(object):
    def __init__(self, datadir, curs):
        self.curs = curs
        with open('%s/orderedSampleIDs.pcl' % datadir) as f:
            self.sampleIDs = cPickle.load(f)
    def iter_samplekeys(self): ## working with int index, as this is what is saved in the GNAT leaves
        for key in range(len(self.sampleIDs)):
            yield key #ps.seqP
    def get_sample(self, key): ## given an integer key, look up sample ID -> retrieve data from MySQL
        ## make sure curs is global
        sampleID = self.sampleIDs[key]
        self.curs.execute("SELECT otu_id, normalized_count FROM OTUS_samples_unified WHERE sample_event_id = '%s'"%sampleID)
        sample =  SQLSample(sampleID, self.curs.fetchall()) #list of tuples
        return sample
    def size(self):
        return len(self.samples)


class DistanceStats:
    def __init__(self, compDists, userSamples):
        ## massaging the datastructure via a dict of lists to a distance matrix using pandas dataframes
        self.userSamples = userSamples
        self.userSampleIDs = [usample.sampleID for usample in userSamples]
        ddd = defaultdict(list)
        for (s1, s2), d in compDists.items():
            # if s2 in self.userSampleIDs: ## remove this part!!!
            #     print "Warning: missing out", s2, s1
            #     pdb.set_trace()
            ddd[s1].append((s2, d))

        ## data frame: rows are query samples, columns are matched DB samples
        ddf = pd.DataFrame([dict(dists) for dists in ddd.values()], index=ddd.keys())
        self.ddf = ddf.loc[self.userSampleIDs].transpose()  ## reduce to user samples (not sure where other stuff comes from)

    def make_mxn_distmtx(self, top=20):
        ## retaining only those columns (DB samples) for which we have distances for all query samples
        ## working on transposed matrix, retaining only DB samples for which we have dists to all user-samples (queries)
        self.mxn_distmtx = self.ddf.dropna(axis=0, how='any')
        ## reduce further, eg. by taking the 100 best matches per query
        self.msubset = set({})
        for sample in self.userSampleIDs:
            ## sorting columns individually, taking top matches (sample ids)
            self.msubset.update(set(self.mxn_distmtx[sample].sort(inplace=False).axes[0].values[:top]))
        self.rankings = self.ddf.loc[self.msubset]


class GNATquery:
    def __init__(self, gnatz, qsample, threshold=0.4): ## threshold is chosen such that
        #print "Performing GNAT search on %s" % qsample.sampleID
        self.qsample = qsample
        countStart = gnatz.metric.counter
        solutions = set(gnatz.query(qsample, threshold))
        print "Performed %s EMD-Unifrac comparisons" % (gnatz.metric.counter - countStart)
        try:
            self.ranking = sorted([(gnatz.metric.computedDistances[(qsample.sampleID, gnatz.db.sampleIDs[sol])],
                                    gnatz.db.sampleIDs[sol]) for sol in solutions])
        except KeyError as e:
            print "Calculated dists for", qsample.sampleID
            print [(s2,dist) for ((s1,s2), dist) in gnatz.metric.computedDistances.items() if s1==qsample.sampleID]
            raise e
        if len(self.ranking) > 0:
            self.distances, self.sampleIDs = zip(*self.ranking)
        else:
            self.distances, self.sampleIDs = [], []
    def printReport(self, top=10):
        print "Matches for %s" % self.qsample
        for dist, sampleID in self.ranking[:top]:
            print "    %-30s: %.4f" % (sampleID, dist)

class SearchEngine:
    def __init__(self, n_otu_matrix, n_otu_ids, n_sample_ids, l_data_path, criteria):
        self.n_otu_matrix = n_otu_matrix
        self.n_otu_ids = n_otu_ids
        self.n_sample_ids = n_sample_ids
        self.l_data_path = l_data_path
        self.criteria = criteria
        self.userSamples = [UserSample(n_sample_id, sample, self.n_otu_ids) for
                            (n_sample_id, sample) in zip(self.n_sample_ids, self.n_otu_matrix)]
        self.conn = MySQLdb.connect(user='root', host='localhost', passwd='qiime', db='EarthMicroBiome')  ## **server_db!!!
        self.curs = conn.cursor()
        print "Search engine/DB initialized..."

    def make_m_n_distmtx(self): ## master, calling self.methods
        ## Expects gnatsearch to be done!
        ## get mxn_distmtx and also m', i.e the usable subset of m
        ds = DistanceStats(self.gnatz.metric.computedDistances, self.userSamples)
        compositions = [sample.composition(self.curs) for sample in self.gnat.metric.topSamples.values() + self.userSamples]
        ds.make_mxn_distmtx()
        self.make_nxn_distmtx()
        print "Made N x N matrix:"
        ids = [s.sampleID for s in self.userSamples]
        print pd.DataFrame(data=self.nxn_distmtx, index=ids, columns=ids)
        ## extract m' x m' from (precalc) m x m (complete DM of DB)
        precalcDM = '24K_EMDunifrac_copynrCorrected_DM.h5'
        f = h5py.File('%s/%s' % (self.l_data_path, precalcDM))
        d = f['distance matrix']
        mxm_distmtx = da.from_array(d, chunks=(1000,1000))

        sampleIDs_to_index = dict(zip(self.db.sampleIDs, range(len(self.db.sampleIDs))))
        ## in the future, this should simply be a right join of pandas dfs on their indices
        msubset, msubsetSampleIDs = zip(*sorted([(sampleIDs_to_index[sampleID], sampleID) for sampleID in ds.msubset]))
        msubset = np.array(msubset)
        m_distmtx = mxm_distmtx[msubset][:,msubset].compute()
        mxn_distmtx = ds.mxn_distmtx.loc[list(msubsetSampleIDs)].values ## arrange mxn matrix accordingly
        ## compose all parts of the distance matrix
        # stack matrices to make the m + n distance matrix
        m_n_distmtx = np.vstack(
            (np.hstack((m_distmtx, mxn_distmtx)),
             np.hstack((mxn_distmtx.T, self.nxn_distmtx)))
        )
        return m_n_distmtx, list(msubsetSampleIDs) + self.n_sample_ids, ds.rankings, compositions


    def make_nxn_distmtx(self):
        dm = np.zeros((len(self.userSamples), len(self.userSamples)))
        for i in range(len(self.userSamples)):
            for j in range(i+1, len(self.userSamples)):
                dm[i,j] = self.metric.dist(self.userSamples[i], self.userSamples[j])
        self.nxn_distmtx = dm + dm.T

    def gnatsearch(self): ## TODO gnatsearch against indiviual environments or at least filter results accordingly
        self.db = MicrobiomeSQLDB(self.l_data_path, self.curs)
        self.metric = EMDUnifrac(rare=True, l_data_path=self.l_data_path)
        self.gnatz = load_gnat('%s/gnat24Kemdu50b_noRef.pcl' % self.l_data_path, self.db, self.metric)
        self.GNATresults = [GNATquery(self.gnatz, qsample) for qsample in self.userSamples[:10]]

    def shortReport(self): ## possible after gnatsearch only!!!
        for gr in self.GNATresults:
            gr.printReport(5)
    def close(self):
        self.conn.close()



if __name__ == "__main__":
    def createDict(samplefile):
        abus = np.load(samplefile)
        with open('%s_otus.pcl'%samplefile[:-7]) as f:
            otus = cPickle.load(f)
        return dict(zip(otus, abus))

    l_data_path = '/home/qiime/visibiome/app/static/data'
    sampledatadir = '/home/qiime/visibiome/app/static/testdata'
    sampleFiles = glob.glob('%s/*_sc.npy' % sampledatadir)[:1]

    index = ["User_%s" % os.path.basename(sf)[:-7] for sf in sampleFiles]
    df = pd.DataFrame([createDict(samplefile) for samplefile in sampleFiles], index=index)

    engine = SearchEngine(df.values, list(df.columns.values), index, l_data_path, ['All'])
    engine.gnatsearch()
    for s, r in zip(engine.userSamples, engine.GNATresults):
        print s.sampleID, r.ranking
    dm, sids = engine.make_m_n_distmtx()

    #DistanceStats(gnatz.db.computedDistances, index)
    # n_otu_matrix, n_otu_ids, n_sample_ids = df.values, list(df.columns.values), index
    # userSamples = [UserSample(n_sample_id, sample, n_otu_ids) for (n_sample_id, sample) in
    #                zip(n_sample_ids, n_otu_matrix)]
    # metric.dist(userSamples[0], userSamples[0])

