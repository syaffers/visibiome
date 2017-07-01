import pdb
import numpy as np
from scipy.spatial.distance import squareform, euclidean, pdist
import pandas as pd
import dask.array as da
from gnatsearch import EMDUnifrac, MicrobiomeSQLDB, SearchEngine
import MySQLdb
import h5py

class Results: ## Mocking up GnatResults, bad hack
    def __init__(self, qsample, sols, traversedNodes, curs):
        self.qsample = qsample
        self.traversedNodes = traversedNodes
        if not hasattr(qsample, 'composition'):
            self.qsample.computeComposition(curs)
            #print "Warning, query without composition information", qsampleID
        self.ranking = []
        for (d, matchSample) in sols:
            if not hasattr(matchSample, 'composition'):
                #pdb.set_trace()
                matchSample.computeComposition(curs)
                #print "Warning, solution without composition information", qsampleID
            self.ranking.append((d,matchSample))
        self.ranking.sort()
    def __repr__(self):
        return 'AESA Result (%s)'%self.ranking

class AESA(SearchEngine):
    ## See Zezula book on NN, notation inspired from there as well
    def __init__(self, n_otu_matrix, n_otu_ids, n_sample_ids, l_data_path, criteria, conn=None):
        super(AESA, self).__init__(n_otu_matrix, n_otu_ids, n_sample_ids, l_data_path, criteria, conn=conn)

        precalcDM = '24K_EMDunifrac_copynrCorrected_DM.h5'
        f = h5py.File('%s/%s' % (l_data_path, precalcDM))
        d = f['distance matrix']
        self.dm = da.from_array(d, chunks=(1000, 1000))

    def search(self, threshold=0.3, rare=True): ## wrapper
        self.metric = EMDUnifrac(rare=rare, l_data_path=self.l_data_path)
        self.db = MicrobiomeSQLDB(self.l_data_path, self.curs)
        self.results = []
        self.rankings = pd.concat([self.search1(sample, threshold) for sample in self.userSamples], axis=1)
        #pdb.set_trace()
        ## ideally rewrite visualizations (generate_barcharts so to deprecate GNATresults, just should use rankings)
        #print self.metric.computedDistances.keys()
    def search1(self, q, r): # query here: sample
        pi = np.random.randint(len(self.dm))
        p1 = self.db.get_sample(pi)
        solutionDict = {}
        solutions = []
        remain = [(0, i) for i in range(len(self.dm))] ## TODO: intersect with search domain

        while remain:
            #print len(remain)
            dqp = self.metric.dist(q, p1)
            if dqp < r:
                solutionDict[p1.sampleID] = dqp
                solutions.append((dqp, p1))
            newRemain = []
            relevantDistanceIDs = zip(*remain)[1]
            relevantDistances = self.dm[pi, relevantDistanceIDs].compute() ## only lookup once, to make use of dask
            for o, dist_pi_o in zip(relevantDistanceIDs, relevantDistances):
                if o == pi: continue
                dqpoMin = dqp - dist_pi_o
                dqpoMax = dqp + dist_pi_o
                if abs(dqpoMin) < r: ## close enough to further look at
                    if dqpoMax < r:  ## close enough to be a solution
                        #solutions.add((o, (max(0,dqpoMin), dqpoMax)))
                        osample = self.db.get_sample(o)
                        #assert osample.sampleID == self.db.sampleIDs[o], "double checking"
                        dqo = self.metric.dist(q, osample)
                        solutionDict[self.db.sampleIDs[o]] = dqo
                        solutions.append((dqo, osample))
                    else: ## at least further look
                        newRemain.append((abs(dqpoMin),o))
            remain = newRemain

            if remain:
                pi = max(remain)[1]
                p1 = self.db.get_sample(pi)
        print '[AESA] Found %s solutions for sample %s' % (len(solutions), q.sampleID)
        self.results.append(Results(q, solutions, self.metric.traversedNodes, self.curs))
        return pd.Series(solutionDict).to_frame(q.sampleID)  #, self.counter

if __name__ == '__main__':
    from collections import Counter
    l_data_path = '/home/qiime/visibiome/app/static/data'
    df = pd.read_csv('/media/sf_SharedFolderQiimeVM/membranes.csv', sep='\t', index_col='#OTU_ID')
    df = df.T
    server_db = dict(db='EarthMicroBiome', host='localhost', user='root', passwd='qiime')
    conn = MySQLdb.connect(**server_db)
    curs = conn.cursor()

    data = []
    ranges = [.1, .2, .3, .4]
    for rnge in ranges:
        aesa = AESA(df.values, map(str, df.columns.values), list(df.index.values), l_data_path, ['All_eco'], conn)
        #aesa.init2(l_data_path)
        aesa.search(rnge)
        data.append(Counter(zip(*aesa.metric.traversedNodes.keys())[0]).values())
    plt.boxplot(data)
    plt.ylabel('# EMDUnifrac comparisons')
    plt.xlabel('Range')
    plt.show()
    #result = aesa.make_m_n_distmtx()
    conn.close()


if __name__ == '__main__0':
    np.random.seed(0)

    data = np.array([[1.01, 5, 6, 0.9, 3.9, 4.7, 0.2, 1, 4.1, 5.1]]).T

    DM = squareform(pdist(data))
    aesa = AESA(None, DM, None)

    rem = aesa.search(7, 0.12)

if __name__ == '__main__1':
    np.random.seed(0)

    data = np.array([[1.1, 5, 6, 0.9, 3.9, 4.7, 0.2, 1, 4.1, 5.1]]).T

    DM = squareform(pdist(data))
    aesa = AESA(data, DM, euclidean)

    rem = aesa.search([5.7], 0.4)

if __name__ == "__main__2":
    ## Some serious business
    datadir = "/research/gutsybugs/manwar-data/Projects/EcoPhyl/BetaDiversity/PairwiseUnifracCluster/Data"
    basename = "24K_EMDunifrac_copynrCorrected"
    D = np.load("%s/%s_DM.npy"%(datadir,basename)) ## distance matrix
    samples = np.load("%s/%s_clusters100F.pcl"%(datadir,basename)) ## sample names in acc. with D
    aesa = AESA(None, D, None)
    selected = np.random.randint(len(samples), size=100)
    for qrange in [0.05, 0.1, 0.2, 0.3, 0.4]:
        comps = np.array([aesa.search(i, qrange)[-1] for i in selected])
        print "Range: %.2f Comparisons: %4d (%.1f%%) STD: %.1f" % (qrange, comps.mean(), 100. * comps.mean() / len(samples), comps.std())
