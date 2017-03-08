import os

from sql_table import *

class TrajectoryKeys(SQLTable):
    trajectorykey = Integer()
    primary_key(trajectorykey)

class SampleKeys(SQLTable):
    samplekey = Integer()
    primary_key(samplekey)

class TrajectoryPropertyTable(SQLTable):
    """Base class for tables holding properties tied to a TrajectoryKey."""
    trajectorykeys = ForeignTable()
    trajectorykey = trajectorykeys.Integer('trajectorykey')
    primary_key(trajectorykey)

class VectorTables(SQLTable):
    dset_name = Text(unique=True)

class Times(SQLTable):
    samplekeys = ForeignTable()
    samplekey = samplekeys.Integer('samplekey')
    time = Real()
    primary_key(samplekey)

class Trajectories(SQLTable):
    samplekeys = ForeignTable()
    samplekey = samplekeys.Integer('samplekey')
    trajectorykeys = ForeignTable()
    trajectorykey = trajectorykeys.Integer('trajectorykey')
    primary_key(samplekey)


class VectorFileError(DatabaseError):
    pass

def open_vector_file(file_name, create=None):
    if os.path.exists(file_name):
        if create:
            os.remove(file_name)
    else:
        if not create:
            return False

    import h5py

    f = h5py.File(file_name)

    return f


class TrajectoryDatabaseError(DatabaseError):
    pass
        
class TrajectoryDatabase(DatabaseMixin):
    """MD coordinate trajectory database.    """

    def create_tables(self, *args, **kwargs):
        super(TrajectoryDatabase, self).create_tables(*args, **kwargs)

        self.new_table(TrajectoryKeys())
        self.new_table(SampleKeys())
        self.new_table(Times(samplekeys=self.samplekeys))
        self.new_table(Trajectories(samplekeys=self.samplekeys, 
                                    trajectorykeys=self.trajectorykeys))

        
    def create_vector_tables(self, *args, **kwargs):
        self.new_table(VectorTables())

        self.new_vector_table('coordinates', self.ndof)



    @property
    def ndof(self):
        return self.__ndof

    def __init__(self, dbname, *args, **kwargs):

        if 'create' in kwargs:
            create = kwargs['create']
        else:
            create = None

        if os.path.isdir(dbname) or (not os.path.exists(dbname) and os.path.splitext(dbname)[-1] == ''):
            if create:
                if not os.path.exists(dbname):
                    os.mkdir(dbname)
            dbname = os.path.join(dbname, os.path.basename(dbname) + '.db')

        
        super(TrajectoryDatabase, self).__init__(dbname, *args, **kwargs)

        if 'ndof' in kwargs:
            ndof = kwargs['ndof']
            assert isinstance(ndof, int)

            self.ensure_var('ndof', str(ndof))
            self.__ndof = ndof

        else:
            ndof = self.get_var('ndof')
            if ndof is None:
                raise TrajectoryDatabaseError('ndof is not present in Vars or __init__ kwargs.')
            self.__ndof = int(ndof)


        
        vector_file = self.open_vector_file(create=create)

        if vector_file:
            self.has_vector_file = True
        else:
            self.has_vector_file = False

        if create:
            self.create_vector_tables(*args, **kwargs)
        
        if vector_file:
            for vtable_name, in self.select([self.vectortables.dset_name]):
                vtable_name = vtable_name.lower()
                if not hasattr(self, vtable_name):
                    ndof = int(self.get_var(vtable_name + '_ndof'))
                    setattr(self, vtable_name, self.get_vector_table(vtable_name, ndof))


        try:
            self.first_key = self.keys().next()
        except StopIteration:
            self.first_key = -1


    def close(self):
        if self.vector_file is not None:

            self.check_vector_table('coordinates', self.ndof)

            self.vector_file.close()

        DatabaseMixin.close(self)

    __vector_file = None

    @property
    def vector_file(self):
        if self.__vector_file:
            return self.__vector_file

        return self.open_vector_file()

    def open_vector_file(self, create=False):
        dbname_woext = os.path.splitext(self.dbname)[0]
        dbname_whdf5 = dbname_woext + '.hdf5'
        self.vector_file_name = dbname_whdf5

        self.__vector_file = open_vector_file(self.vector_file_name, create=create)

        return self.__vector_file


    def vector_table_shape(self, ndof):
        if self.last_samplekey:
            num_samples = self.last_samplekey+1
        else:
            num_samples = 1

        return (num_samples, ndof)
        
    
    def check_vector_table(self, vector_table_name, ndof):

        expected_shape = self.vector_table_shape(ndof)

        vector_file = self.vector_file

        dset = vector_file[vector_table_name]

        return dset.shape == expected_shape
        

    def new_vector_table(self, vector_table_name, ndof, overwrite=False):
        if self.has_vector_table(vector_table_name, ndof):
            if overwrite:
                del self.vector_file[vector_table_name]
            else:
                raise VectorFileError("vector table '%s' already exists." % vector_table_name)

        expected_shape = self.vector_table_shape(ndof)


        vector_file = self.vector_file

        vector_file.create_dataset(vector_table_name, expected_shape, maxshape=(None, ndof))


        dset = vector_file[vector_table_name]

        assert self.check_vector_table(vector_table_name, ndof)

        self.insert(self.vectortables, [(vector_table_name, )])
        self.set_var(vector_table_name.lower() + '_ndof', str(ndof))
        

        if hasattr(self, vector_table_name):
            delattr(self, vector_table_name)

        setattr(self, vector_table_name, dset)

        return dset

    def has_vector_table(self, vector_table_name, ndof):
        vector_file = self.vector_file
        if not vector_file:
            return False

        # if self.last_samplekey:
        #     num_samples = self.last_samplekey+1
        # else:
        #     num_samples = 1
        # expected_shape = (num_samples, ndof)

        try:
            dset = vector_file[vector_table_name]
        except KeyError:
            return False

        return dset

    def get_vector_table(self, vector_table_name, ndof):
        dset = self.has_vector_table(vector_table_name, ndof)

        if not dset:
            raise VectorFileError("Vector table '%s' is not present." % vector_table_name)
        
        return dset

    @property
    def vector_table_names(self):
        return list(self.select([self.vectortables.dset_name]))

    def get_vector_table_ndof(self, vector_table_name):
        vector_file = self.vector_file
        return vector_file[vector_table_name].shape[1]

    def add_sample_table(self, table_name, property_name='value', overwrite=False):
        class SampleTable(SQLTable):
            samplekeys = ForeignTable()
            samplekey = samplekeys.Integer('samplekey')
            property = Real()
            primary_key(samplekey)


        table = SampleTable(name=table_name, property_name=property_name, samplekeys=self.samplekeys)

        if not overwrite:
            old_table = self.has_table(table_name)
            if old_table:
                if not set(column.qualified_name for column in old_table.columns) == set(column.qualified_name for column in old_table.columns):
                    raise TableError('Old table exists and does not have the column set [%s]' % property_name)
                return old_table

        table = self.new_table(table, overwrite=overwrite)
        return table


    def get_sample_property_column(self, name):
        table = self.get_table(name)
        if len(table.columns) != 2:
            raise TableError('Not a sample property table: %s' % table)

        return table.columns[-1]


    __current_trajectorykey = None
    __current_samplekey = None
    __current_time = None

    __last_samplekey = None
    @property
    def last_samplekey(self):
        if self.__last_samplekey is not None:
            return self.__last_samplekey

        self.__last_samplekey = self.select_max(self.samplekeys.samplekey)
        return self.__last_samplekey

    def keys(self):
        for key, in self.select(self.samplekeys.columns):
            yield key

    @property
    def num_samples(self):
        return self.last_samplekey - self.first_key + 1

    @property
    def current_samplekey(self):
        if self.__current_samplekey is not None:
            return self.__current_samplekey
        self.__current_samplekey = self.select_max(self.samplekeys.samplekey)
        return self.__current_samplekey

    def new_sample(self, coords):
        assert len(coords) == self.ndof, '%s != %s'% (len(coords), self.ndof)

        
        
        key = self.current_samplekey

        if key is None:
            key = -1
            self.first_key = 0
            
        self.insert(self.samplekeys, [(key+1,)])
        key = self.__current_samplekey = key+1            


        coordinates = self.coordinates

        coordinates.resize((1+self.__current_samplekey, self.ndof))
        coordinates[self.__current_samplekey] = coords

        current_trajectorykey = self.current_trajectorykey
        current_time = self.current_time

        self.insert(self.trajectories, [(self.__current_samplekey, current_trajectorykey)])
        self.insert(self.times, [(self.__current_samplekey, current_time)])
        return key

    def get_sample(self, samplekey):
        coordinates = self.coordinates
        return coordinates[samplekey]


    __last_trajectorykey = None
    @property
    def last_trajectorykey(self):
        if self.__last_trajectorykey is not None:
            return self.__last_trajectorykey

        self.__last_trajectorykey = self.select_max(self.trajectorykeys.trajectorykey)
        return self.__last_trajectorykey


    @property
    def current_trajectorykey(self):
        if self.__current_trajectorykey is not None:
            return self.__current_trajectorykey

        # default to the trajectorykey of the current sample
        current_samplekey = self.current_samplekey

        trajectorykey = None
        try:
            trajectorykey, = self.select([self.trajectories.trajectorykey], where=(self.samplekeys.samplekey==current_samplekey)).next()
        except StopIteration:
            trajectorykey = None

        if trajectorykey is None:
            self.__current_trajectorykey = -1
            trajectorykey = self.new_trajectory()

        self.__current_trajectorykey = trajectorykey
        return self.__current_trajectorykey

        
        self.__current_trajectorykey = self.select_max(self.trajectorykeys.trajectorykey)
        return self.__current_trajectorykey

    def new_trajectory(self, reset_time=0.):
        self.__last_trajectorykey = self.__current_trajectorykey = self.__current_trajectorykey + 1
        self.insert(self.trajectorykeys, [(self.__current_trajectorykey,)])
        self.__current_time = reset_time
        return self.__last_trajectorykey

    def switch_trajectory(self, other_trajectorykey):
        assert 0 <= other_trajectorykey <= self.last_trajectorykey
        self.__current_trajectorykey = other_trajectorykey


    @property
    def current_time(self):
        if self.__current_time is not None:
            return self.__current_time

        # default to the time of the current samplekey
        current_samplekey = self.current_samplekey

        time = 0.
        for row in self.select([self.times.time], where=(self.samplekeys.samplekey==current_samplekey)):
            # this should only occur once...
            time = row[0]
            break
        self.__current_time = time 
        return self.__current_time

    def set_time(self, time):
        self.__current_time = time

    def step_time(self, step):
        self.__current_time += step

    def iter_vectors(self, vector_table_name, ndof, missing=None, where=None):

        vectors = self.get_vector_table(vector_table_name, ndof)

        if missing:
            assert isinstance(missing, SQLTable)
            assert missing.samplekey.is_primary_key()

            samplekey_constraint=self.samplekeys.samplekey.not_in(select([missing.samplekey]))

            if where:
                where = where & samplekey_constraint
            else:
                where = samplekey_constraint

        for row in self.select([self.samplekeys.samplekey], where=where):
            samplekey = row[0]
            yield samplekey, vectors[samplekey]


    def iter_coordinates(self, missing=None, where=None):
        for row in self.iter_vectors('coordinates', self.ndof, missing=missing, where=where):
            yield row


    def iter_samplekeys(self):
        for key, in self.select([self.samplekeys.samplekey]):
            yield key


open_trajectory_database=TrajectoryDatabase

    

