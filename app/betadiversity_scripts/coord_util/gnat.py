
import os
import random

try:
    import pypbs.pbs_map as ppm
    pypbs_available = True
except ImportError:
    pypbs_available = False

import cPickle as pickle

import trajdb
import coord_math
from sql_table import *

debug = os.getenv('DEBUGGNAT')
if debug:
    debug = debug.strip().upper()
    print 'DEBUGGNAT = ', debug



class Metric(object):
    def __init__(self):
        self.counter = 0

    def dist(self, x, y):
        self.counter += 1
        return coord_math.rmsd(x, y)

    def get_sample(self, db, key):
        return db.get_sample(key)

    def dist_pk(self, db, x, samplekey_y):
        y = self.get_sample(db, samplekey_y)
        return self.dist(x, y)

    def dist_kk(self, db, samplekey_x, samplekey_y):
        x = self.get_sample(db, samplekey_x)
        return self.dist_pk(db, x, samplekey_y)


rmsd_metric=Metric()

class GNATNode(object):

    def __init__(self, db, center, subtrees=None, rmax=0., metric=rmsd_metric):
        self.db = db
        self.center = center
        self.rmax = rmax

        if subtrees is None:
            self.subtrees = []
        else:
            self.subtrees = subtrees
        self.is_leaf = (self.subtrees == []) or (not isinstance(self.subtrees[0], GNATNode))

        self.metric=metric
                

    @property
    def nodes(self):
        yield self
        if self.is_leaf:
            for node in self.subtrees:
                for subnode in node.nodes:
                    yield subnode

    @property
    def all(self):
        yield self.center
        if self.is_leaf:
            for k in self.subtrees:
                yield k
        else:
            for node in self.subtrees:
                for k in node.all:
                    yield k


    @property
    def depth(self):
        if self.is_leaf:
            return 1
        else:
            return 1 + max(node.depth for node in self.subtrees)


    def _query(self, x, r):
        db = self.db

        if self.is_leaf:
            for k in self.subtrees:
                if self.metric.dist_pk(db, x, k) < r:
                    yield k

        else:
            for node in self.subtrees:
                node_r = self.metric.dist_pk(db, x, node.center)

                if node_r < r:
                    yield node.center

                
                if node_r + node.rmax < r:
                    for k in node.all:
                        yield k
                elif node_r - node.rmax < r:
                    for k in node._query(x, r):
                        yield k

    def query(self, x, r):
        db = self.db

        cr = self.metric.dist_pk(db, x, self.center)
        if cr < r:
            yield self.center
        for k in self._query(x, r):
            yield k

    def _neighbor_query(self, x, num, hints):
        assert len(hints) <= num
        if len(hints) == num:
            max_r = hints[-1][0]
        else:
            max_r = 1e100

        db = self.db

        # TODO: factor out hints update, and add node centers before
        # recursion to avoid computing cr twice

        cr = self.metric.dist_pk(db, x, self.center)

        if cr < max_r:
            hints.append((cr, self.center))
            hints.sort(key=lambda h: h[0])
            if len(hints) > num:
                hints.pop()

            if len(hints) == num:
                max_r = hints[-1][0]

        if self.is_leaf:
            for k in self.subtrees:
                r = self.metric.dist_pk(db, x, k)
                if r < max_r:
                    hints.append((r, k))

            hints.sort(key=lambda h: h[0])
            if len(hints) > num:
                hints = hints[:num]
        else:
            for node in self.subtrees:
                nr = self.metric.dist_pk(db, x, node.center)
                if nr - node.rmax < max_r:
                    hints = node._neighbor_query(x, num, hints)

                    if len(hints) == num:
                        max_r = hints[-1][0]

        # hints.sort(key=lambda h: h[0])
        # if len(hints) > num:
        #     hints = hints[:num]

        return hints

    
    def neighbor_query(self, x, num=1):
        neighbors = []

        def new_neighbors_in_order(old_neighbors, key, r):
            for idx, (old_key, old_r) in enumerate(neighbors):
                if old_r > r:
                    return old_neighbors[:idx] + [(key, r)] + old_neighbors[idx:]

            return old_neighbors + [(key, r)]


        traverser = breadth_first(self, x, 1e100)
        # traverser = all(self, x, 1e100)

        try:
            key, r = traverser.next()

            while True:
                neighbors = new_neighbors_in_order(neighbors, key, r)
                if len(neighbors) > num:
                    neighbors = neighbors[:num]
                    rmax = neighbors[-1][1]
                    key, r = traverser.send(neighbors[-1][1])
                else:
                    key, r = traverser.next()
        except StopIteration:
            pass
            

        assert sorted(neighbors, key=lambda n: n[1]) == neighbors
        # assert len(neighbors) == num
        return [n[0] for n in neighbors]

    def __eq__(self, other):
        if self.center != other.center:
            return False

        if abs(self.rmax - other.rmax) > 1e-14:
            return False

        if self.is_leaf != other.is_leaf:
            return False

        if not all(s==o for s, o in zip(self.subtrees, other.subtrees)):
            return False

        return True



    # def check_invariants(self):
    #     subtrees = self.subtrees

    #     if self.is_leaf:
    #         assert all(isinstance(s, int) for s in subtrees)
    #     else:
    #         assert all((isinstance(s, GNATNode) for s in subtrees))

    #     c = self.center
    #     db = self.db
    #     rmax = max(self.metric.dist_kk(db, c, k) for k in self.all)

    #     assert abs(rmax - self.rmax) < 1e-5, 'recorded rmax is not equal to actual rmax: %s != %s (diff = %s)' % (rmax, self.rmax, rmax - self.rmax)

    #     if not self.is_leaf:
    #         for tree in subtrees:
    #             if not tree.is_leaf:
    #                 assert len(tree.subtrees) == len(subtrees), 'subtree has wrong number of splits: %s != %s (%s)' % (len(tree.subtrees), len(subtrees), tree.subtrees)
    #             tree.check_invariants()

def depth_first(gnat, x, rmax):
    """Coiterate over the samplekeys within the cutoff, depth first.

    Receives updates to rmax as a coroutine.
    """

    
    db= gnat.db
    k = len(gnat.subtrees)

    r = gnat.metric.dist_pk(db, x, gnat.center)
    if r < rmax:
        new_rmax = (yield gnat.center, r)
        if new_rmax is not None:
            rmax = new_rmax

    node_stack = [(gnat, 0)]

    while node_stack != []:
        node, last_position = node_stack.pop()

        if node.is_leaf:
            for key in node.subtrees:
                r = gnat.metric.dist_pk(db, x, key)
                if r < rmax:
                    new_rmax = (yield key, r)
                    if new_rmax is not None:
                        rmax = new_rmax
        else:
            if last_position < k:

                subtree = node.subtrees[last_position]
                node_stack.append((node, last_position+1))

                
                r = gnat.metric.dist_pk(db, x, subtree.center)
                if r < rmax:
                    new_rmax = (yield subtree.center, r)
                    if new_rmax is not None:
                        rmax = new_rmax
                
                if r - subtree.rmax < rmax:
                    node_stack.append((subtree, 0))


def all_traverser(gnat, x, rmax):
    db = gnat.db
    for key in gnat.all:
        r = gnat.metric.dist_pk(db, x, key)
        if r < rmax:
            new_rmax = (yield key, r)
            if new_rmax is not None:
                rmax = new_rmax

def breadth_first(gnat, x, rmax):
    """Coiterate over the samplekeys within the cutoff, breadth first.

    Receives updates to rmax as a coroutine.
    """

    
    db= gnat.db


    def cached_metric(key, r_cache):
        if key in r_cache:
            return r_cache[key]
        r = gnat.metric.dist_pk(db, x, key)
        r_cache[key] = r
        return r


    r = gnat.metric.dist_pk(db, x, gnat.center)
    if r < rmax:
        new_rmax = (yield gnat.center, r)
        if new_rmax is not None:
            rmax = new_rmax


    gnat_depth = gnat.depth

    target_depth = 0

    r_cache = {}

    k = len(gnat.subtrees)

    while target_depth < gnat_depth:

        node_stack = [(gnat, 0, 0)]

        while node_stack != []:
            node, last_position, depth = node_stack.pop()

            if depth == target_depth:
                if node.is_leaf:
                    for key in node.subtrees:
                        r = gnat.metric.dist_pk(db, x, key)
                        if r < rmax:
                            new_rmax = (yield key, r)
                            if new_rmax is not None:
                                rmax = new_rmax
                        
                else:
                    for subtree in node.subtrees:
                        r = cached_metric(subtree.center, r_cache)
                        if r < rmax:
                            new_rmax = (yield subtree.center, r)
                            if new_rmax is not None:
                                rmax = new_rmax

            elif node.is_leaf:
                continue

            elif last_position < k:

                try:
                    subtree = node.subtrees[last_position]
                except IndexError:
                    print last_position
                    raise Exception('index error on %s: %s, %s' % (last_position, node.subtrees, node.center))
                node_stack.append((node, last_position+1, depth))

                r = cached_metric(subtree.center, r_cache)

                if r - subtree.rmax <= rmax:
                    node_stack.append((subtree, 0, depth+1))

        
        target_depth += 1
        

def split_leaf(node, k, metric_cacher):
    db = node.db
    assert node.is_leaf
    assert len(node.subtrees) > 3*k
    num = len(node.subtrees)
    node.is_leaf = False

    node.subtrees, rest = split_nodes(node.subtrees, k, node.db, node.metric, metric_cacher)
    assert len(node.subtrees) == k
    assert len(node.subtrees) + len(rest) == num

    return rest

class MetricCacher(object):

    def __init__(self, db, metric):
        self.db = db
        self.metric = metric

    def __call__(self, left_keys, right_keys):
        cache = dict(((l, r), self.metric.dist_kk(self.db, l, r))
                     for l in left_keys
                     for r in right_keys)

        symmetric_cache = dict(((r, l), d) for ((l,r), d) in cache.iteritems())

        cache.update(symmetric_cache)
        return cache

class PBSMapMetricCacherWorker(object):

    def __init__(self, dbname, metric):
        self.db = trajdb.open_trajectory_database(dbname, create=False)
        self.metric = metric

    def __call__(self, work):
        left_key, right_key = work
        return (left_key, right_key), self.metric.dist_kk(self.db, left_key, right_key)

    
class PBSMapMetricCacher(object):

    def __init__(self, mapper):
        self.mapper = mapper

    def __call__(self, left_keys, right_keys):
        cache = dict(self.mapper.map(((l, r) 
                                      for l in left_keys
                                      for r in right_keys)))
        symmetric_cache = dict(((r, l), d) for ((l,r), d) in cache.iteritems())

        cache.update(symmetric_cache)
        return cache

def insert_many(node, samplekeys, metric_cacher, k=10, r_cache=None):
    samplekeys = list(samplekeys)

    if len(samplekeys) < 1:
        return
    
    # TODO: instead of partitioning in parallel, compute the r_cache in parallel
    if node.is_leaf:
        samplekeys += node.subtrees

    if not r_cache:
        r_cache = metric_cacher([node.center], samplekeys)

    node.rmax = max(r_cache[(node.center, key)] for key in samplekeys)

    if node.is_leaf:
        node.subtrees = node.subtrees + list(samplekeys)

        if len(node.subtrees) > 3 * k:
            samplekeys = split_leaf(node, k, metric_cacher)
        else:
            return

    assert not node.is_leaf
    
    center_samplekeys = [subnode.center for subnode in node.subtrees]

    r_cache = metric_cacher(center_samplekeys, samplekeys)

    partitions = dict((c, []) for c in center_samplekeys)
    for s in samplekeys:
        c = min(center_samplekeys, key=lambda c: r_cache[(c, s)])
        partitions[c].append(s)
        
    
    for subnode in node.subtrees:
        partition = partitions[subnode.center]
        del partitions[subnode.center] # we don't need this set in memory after this.
        if len(partition) > 0:
            insert_many(subnode, partition, k=k, metric_cacher=metric_cacher, r_cache=r_cache)


def insert(node, samplekey, x, k=10):
    db = node.db
    node.rmax = max(node.rmax, node.metric.dist_pk(db, x, node.center))
    if not node.is_leaf:
        subnode = min( (node for node in node.subtrees),
                       key=lambda n: node.metric.dist_pk(db, x, n.center))
        insert(subnode, samplekey, x, k=k)
    else:
        node.subtrees.append(samplekey)

        if len(node.subtrees) > 3 * k:
            rest = split_leaf(node, k, metric_cacher)
            for key in rest:
                y = db.get_sample(key)
                insert(node, key, y, k=k)    

    if not node.is_leaf:
        assert len(node.subtrees) == k, '%s!=%s' % (len(node.subtrees), k)


def split_nodes(points, k, db, metric, metric_cacher):

    assert len(points) == len(set(points))

    num = len(points)

    assert num >= 3*k, """Not enough samples for k split points: %s < %s""" % (num, k)

    random.shuffle(points)

    points, rest = points[:3*k], points[3*k:]

    # choose k points, each maximizing the minimum distance to previously chosen points

    r_cache = metric_cacher(points, points)

    selected = [points.pop()]

    #r_cache = {}
    for count in xrange(k-1):
        p = max(points, key=lambda p: min(r_cache[(p, s)] for s in selected) )
        points.remove(p)
        selected.append(p)


    nodes = [GNATNode(db, s, metric=metric) for s in selected]

    assert len(nodes) == k
    
    return nodes, points + rest


default_gnat_name='rmsd_gnat'


def build_gnat(db, k=10, metric=rmsd_metric,
               use_pbs_map=False):

    pickle.dumps(metric) # make sure we can pickle the metric

    # print 'Loading samplekeys'
    samplekeys = list(db.iter_samplekeys())

    # print 'Shuffling'
    random.shuffle(samplekeys)

    parent_key = samplekeys.pop()

    parent_node = GNATNode(db, parent_key, metric=metric)

    # print 'Inserting...'

    if pypbs_available and use_pbs_map:
        with ppm.PBSMap(PBSMapMetricCacherWorker, startup_args=(db.dbname, metric), num_clients=10) as mapper:
            insert_many(parent_node, samplekeys, k=k, metric_cacher=PBSMapMetricCacher(mapper))
    else:
        insert_many(parent_node, samplekeys, k=k, metric_cacher=MetricCacher(db, metric))

    # print 'Checking...'
    # parent_node.check_invariants()

    return parent_node


OPENTREE=0
POINT=1
CLOSETREE=2

def gnat_table_rows(node, super_key=None):
    """Serialize the GNAT."""
    parentkey = node.center
    yield OPENTREE, parentkey, super_key, float(node.rmax)

    if node.is_leaf:
        for k in node.subtrees:
            yield POINT, k, parentkey, None

    else:
        for t in node.subtrees:
            for row in gnat_table_rows(t, parentkey):
                yield row

    yield CLOSETREE, None, parentkey, None
    


def save_gnat(parent_node, name=default_gnat_name):
    db = parent_node.db

    table_name = name + '_nodes'
    print 'Saving ', table_name

    class GNATNodes(SQLTable):
        samplekeys = ForeignTable()
        tree_type = Integer()
        samplekey = samplekeys.Integer('samplekey')
        parent = samplekeys.Integer('samplekey')
        rmax = Real()


    gnatnodes = GNATNodes(name=table_name, samplekeys=db.samplekeys)

    db.new_table(gnatnodes, overwrite=True)

    db.insert(gnatnodes, gnat_table_rows(parent_node))

    db.set_var(name + '_metric', pickle.dumps(parent_node.metric))


def load_sub_trees(db, centerkey, gnat_table_rows, metric):

    subtrees = []

    for tree_type, key, parentkey, rmax in gnat_table_rows:
        assert parentkey == centerkey, 'expecting a child of %s, got a child of %s' %  (centerkey, parentkey)
        if tree_type == CLOSETREE:
            return subtrees
        if tree_type == OPENTREE:
            sub_subtrees = load_sub_trees(db, key, gnat_table_rows, metric)
            subtrees.append(GNATNode(db, key, sub_subtrees, rmax, metric))
        elif tree_type==POINT:
            subtrees.append(key)
        else:
            raise Exception("Unknown tree_type %s" % tree_type)

    raise Exception("Tree %d was not closed." % parentkey)
            
            
def load_gnat_from_rows(db, table_rows, metric):
    tree_type, key, parentkey, rmax = table_rows.next()

    subtrees = load_sub_trees(db, key, table_rows, metric)

    return GNATNode(db, key, subtrees, rmax, metric=metric)

            

def load_gnat(db, name=default_gnat_name, metric=None):

    table_name = name + '_nodes'
    gnatnodes = db.get_table(table_name)

    if metric is None:
        metric_pickle = db.get_var(name + '_metric')
        if metric_pickle:
            metric = pickle.loads(str(metric_pickle))
        else:
            metric = rmsd_metric
            db.set_var(name + "_metric", pickle.dumps(metric))

    gnat_table_rows = db.select(gnatnodes.columns)

    return load_gnat_from_rows(db, gnat_table_rows, metric)
        
