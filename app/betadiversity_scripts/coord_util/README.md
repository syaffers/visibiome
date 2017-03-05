
# coord_util

coord_util is a library for reading, manipulating and writing molecule
geometries. coord_util can read and write geometries in several common
formats.  

## Dependencies

coord_util depends on my `tempfile_util` module.

coord_util also depends on `numpy` (tested with 1.6.1).  

coord_util contains a module for storing geometries in a useful
database format, `trajdb`.  In order to make use of this module, coord_util
depends on the presence of `sqlite3` and `h5py`.

Scripts for building all of the above dependencies in the user's home
directory (and thus not requring root permissions) are available in my
`build_scripts` repository.

## Installation

### Download

Clone `coord_util` into your python `site-packages` directory.

```bash
      cd your_python_site-packages
      git clone git://github.com/plediii/coord_util
```

### Configure and Build

This step is optional but recommended; all of the `coord_util`
functions are pure python.  However, some functions have been
implemented more efficiently in Fortran.  To access the more efficient
versions configure and build the moules via:


```bash
	./configure.py
	make
```


### Testing

The `coord_util` package includes several test suites with names in
the form `test_foo.py`.  To execute all of them:

```bash
		./test.bash
```

### Modules

#### coord_math

The coord_math module exposes several geometric functions which
interpret one-dimensional numpy arrays holding contiguous sequence of
atoms.  The arguments to the coord_math functions assume that the
numpy arrays are in the order:

```python
      x = np.array([x1, y1, z1, x2, y2, z2, ..., xn, yn, zn]),
```

where `x1` is the x coordinate of the first atom, `y2` is the y
coordinate of the second atom, and `zn` is the z coordinate of the nth
atom.  The atom index in the following functions is 1-based, so that
the first atom has index 1.

##### get_atom_coords
get_atom_coords returns a 1x3 array containing the coordinates of the ith atom.

```python
		get_atom_coords(np.array([1, 2, 3, 4, 5, 6]), 2) == np.array([4, 5, 6])
```

##### center_of_geometry

center_of_geometry returns a 1x3 array containing the coordinates at
the average of the atom coordinates in the system. 

For instance, the center of geometry of atoms arranged at the corners
of a square is the center of the square:

```python
    center_of_geometry(np.array([0., 0., 0., 
                                 1., 0., 0.,
	                         0., 1., 0.,
	                         1., 1., 0.,]))
	                         == np.array([0.5, 0.5, 0.0])
```

##### rmsd

`rmsd` is a slight misnomer, since rmsd is the *least* root mean
square distance between two geometries.  However, the convention is to
simply refer to this measure as rmsd. The *non* least root mean square
distance between two geometries is simply the l2-norm of the
difference vector, divided by the square root of the number of atoms:

```python
       flat_rmsd(v1, v2) == sqrt(dot(v1-v2, v1-v2)/(len(v1)/3)).
```

The *least* root mean square is the least root mean square between the
two vectors, amongst all possible rotations and translations of the
geometry.  The intuition for using the least rmsd is that, for
example, changes in a water molecule geometry by rotation or
translation are irrelevant to its dynamics.  

Since `rmsd` gives the least root mean square distance, we have, for
example, that

```python
	rmsd(v1, v2) == rmsd(v1, translate(v2, anything))
```

and

```python
	rmsd(v1, v2) == rmsd(v1, rotate(v2, anyangle)).
```


##### align

`align` transforms a geometry to minimize the `flat_rmsd` to another
target geometry.  Explicitly:

```python
       rmsd(v1, v2) == flat_rmsd(v1, align(v1, v2)).
```

Geometries can be aligned considering only subset of the coordinates
using the `subalign` function and the `topology` module described below.

##### translate

`translate` displaces all atoms in a geometry by a uniform vector; for
example, if we translate a geometry via,

```python
	    translate(geom, delta_vector).
```

Then, for any atom in the geometry

```python
    get_atom_coords(geom, idx) - get_atom_coords(translate(geom, delta_vector)), idx) == delta_vector.
```

##### dihedral

`dihedral` calculates the dihedral angle between involving for atoms.  Example:

```python
	   dihedral(geom, idx, jdx, kdx, ldx)
```

##### atom_dist

`atom_dist` calculates the distance between the idxth and jdxth atoms.  Example:

```python
	    atom_dist(geom, idx, jdx).
```

##### rotate_euler

`rotate_euler` rotates the geometry about the origin according to the euler angles.  Example:

```python
	       rotate_euler(geom, alpha, beta, gamma).
```


##### transform

`transform` applies a 3x3 transformation matrix to each atom in the geometry.  Example:

```python
	    transform(geom, euler_rotation_matrix(alpha, beta, gamma)).
```

## topology

The `topology` module exposes classes and functions for selecting and
manipulating components of geometries, especially residues of
proteins.  The inspiration for the design of this module came from the
pattern used by `jQuery` for selecting and manipulating components of
the DOM.

The need for this module in my own projects arose in the context of
monte-carlo rotamer switching in protein dynamics. Rotamer switching
refers to changing the geometry of a single amino acid side chain in a
protein between different stable formations separated by energetic
frustration.  Monte-Carlo rotamer switching allows for rapid
exploration of a protein's dynamical space without requiring the time
normally required for transitions within the residues.

The usefulness of the `topology` module goes beyond just rotamer
switching.  When coupled with coordinates describing a protein
geometry, it can be used to extract specific atoms, or switch the atom
order in a clear way.

Use of the `topology` module centers around the `Topology` class.
Instances of the topology classes can be read by reading the topology
of a PDB file, or by creating them manually.  


### Creating topology instances

For example, to obtain the topology describing the model in  "protein.pdb":

```python
    import coord_util.pdb as p
    
    top = p.read_topology('protein.pdb')
```


Alternatively, specific topologies can be constructed manually.  For
instance, we can construct a toplogy for a glycine residue, or a water
molecule:

```python
	import topology as t

	gly = t.Molecule('GLY', ['N', 'CA', 'C', 'O'])
	water = t.Molecule('HOH', ['H', 'O', 'H'])
```

Individual molecules can be composed to create polymers.  A glycine dipeptide can be constructed via:

```python
	   digly = t.Polymer('GLYGLY', [gly, gly])
```

Polymers can be composed with water molecules to create a dipeptide solvated in 100 water molecules:

```python
	 system = t.Polymer('solvagted gly', [digly] + [water] * 100)
```

Alternatively, chains can be constructed by creating a monomer set, and using its sequence method.

```python
	ala = t.Molecule('ALA', ['N', 'CA', 'CB', 'C', 'O'])

	  monomers = t.Monomers([gly, ala])

	  gly_ala_gly = t.Polymer('GLYALAGLY', monomers.sequence(['GLY', 'ALA', 'GLY']))
```

The `coord_util` project includes a module `aminoacids` with the standard set of aminoacids:

```python
    from aminoacids import aminoacids

    gly_ala_gly = aminoacids.sequence(['ALA', 'GLY', 'ALA'])
```

	  
### Selecting and extracting substructures

A `Topology` instance, when coupled with the coordinates in the PDB
file, allows us to select specific components.  

Suppose we already have the topology in "protein.pdb", "top" from
above.  The trajectory of geometries in the PDB file can be obtained
via:

```python
	   xs = list(p.read_coords('protein.pdb'))
```

The coordinates of specific components of the geometry can be
extracted by coupling a topology instance with the coordinate
described.  For instance, to extract only the CA atoms in the protein,
we can use the `Topolgy.get_atoms` method to create a subtopology, and
`Topology.get_coords` to extract the coordinates for those atoms from
a numpy array:


```python
      ca_top = top.get_atoms('CA')
      ca_xs = [ca_top.get_coords(x) for x in xs]
```
	   

After the above, assuming the protein consists of N residues with CA
atoms, each of the ca_xs are numpy arrays of length 3N containing
the coordinates of the CA atoms.

Alternatively, we could extract just the backbone of the geometry
using the `Topology.get_atomset` method:

```python
	       backbone_top = top.get_atomset(['CA', 'CB', 'C', 'N', 'O'])
```

Atoms can also be selected with regular expressions (regex).  We could
have selected the backbone atoms using a regex instead:

```python
	       backbone_top = top.regex_get_atoms('^(CA|CB|C|N|O)$')
```

We could also select for specific monomers by name using
`Polymer.get_monomer(resname)`, `Polymer.monomers_slice(idx, jdx)` and
`Polymer.get_monomer_by_index(idx, jdx)`.

### Replacing substructures

Besides extracting substructures from a geometry, replacing those
substructures into a geometry is also useful.  In the case of the
rotamer switching problem, for instance, we want to change the
coordinates of specific side chains in the protein.  This operation is
implemented by the `Topology.set_coords` method.

For instance, suppose we have the subtopology for the first monomer in a Polymer:

```python
    first = top.get_monomer_by_index(0).
```

If `x` is an numpy array of length 3N (corresponding to the N atoms
described by `top`), and `x1` is a numpy array of length 3M
(corresponding to the M atoms of the first residue), we can change the
geometry of the first residue to that of `x1` by

```python
	 first.set_coords(x, x1).
```


### Lifting and reordering atoms

When building a geometry from scratch from its constituent
substructures, a common operation is to build a new array for the
entire geometry, and fill in each of the substructures using
subtopologies For instance, suppose we are beginning to reconstruct a
geometry from its CA atoms.  We can create a numpy array for the
entire geometry, with the CA atoms already filled in using
`Topology.lift_coords` like so:


```python
		       lift_ca = top.lift_coords(top.get_atoms('CA'))
		       
		       full_x = lift_ca.lift_coords(ca_x)
```

Then, assuming `ca_x` is a numpy array of length 3M corresponding to
the M CA atoms, `full_x` will be a numpy array of length 3N
corresponding to the N atoms in the complete geometry, with the CA
coordinates fill in, and the coordinates for the remaining atoms set
to zero.

A related situation is when we have coordinates for a molecule with
atoms in a different order.  Suppose `top2` contains a topology for
the same molecule as `top`, except that the atom names are in a
different order.  Additionally, suppose `x2` contains a geometry for
the atoms in the order of `top2`.  Then we can change order of the
atoms to that of `top` via:

```python
      top_lift_top2 = top.lift_topology(top2, reorder=True)
      x = top_lift_top2.lift_coords(x2)
```

The extra argument to `lift_topology`, `reorder`, is not strictly
necessary, but it dictates that `lift_topology` should raise an
exception if the topology to be lifted does not contain the same
number of atoms.

Topology lifting considers only the names of atoms in molecules, so it
can be used between Polymers with different names as long as the
Molecules in the corresponding positions in the Polymer tree can be
lifted to one another.

### Aligning sub geometries

A common procedure is to align a geometry so that a sub component is
optimally aligned with the same component of another geometry.  This
can be accomplished with the `subalign` function in the `coord_math`
module.  For example, to align protein coordinates `y` to protein
coordinates `x` along their backbone:

```python
	    backbone_top = top.regex_get_atoms('^(CA|CB|C|N|O)$')
	    aligned_y = subalign(backbone_top, x, y)
```	    

## mol_reader/writer

The `coord_util` package includes reader modules for several
coordinate formats. These reader modules provide an `open` function
returning an iterator over the geometries in the file.  

### AMBER Formats

#### mdcrd

The `mdcrd` format requires the number of atoms in the geometry.

```python
    import coord_util.mdcrd as mdcrd

    with mdcrd.open('ala.crd', num_atoms=22) as f:
        for geom in f:
	    print center_of_geometry(geom)
```

#### rst

Example:


```python
	import coord_util.rst as rst

	with rst.open('ala.rst') as f:
	     for geom in f:
	       	 print center_of_geometry(geom)
```


### PDB Format

Example:

```python
    import coord_util.pdb as pdb

    with pdb.open('protein.pdb') as f:
        for geom in f:
	    print center_of_geometry(geom)
```
	    

### Gromacs Format

#### gro

The Gro format specifies coordinates in nanometers, but `coord_util`
converts them to angstroms for consistency with the other formats.

Example:

```python
    import coord_util.gro as gro

    with gro.open('ala.gro') as f:
        for geom in f:
	    print center_of_geometry(geom)
```




## trajdb

`coord_util` includes a module for storing molecular dynamics
trajectories in a convenient database format.  The purpose of `trajdb`
is to associate snapshots molecular dynamics trajectories with a
collection of all relevant real valued physical properties in an
efficient and easily queried pair of files.  A `trajdb` consists of an
`sqlite` and `hdf5` database comprising the trajectories and physical
properties.

This module requires `sqlite3` and `h5py` python modules.


### Opening and creating trajdbs

#### Opening an existing trajdb

An existing trajdb named `mytraj.db` can be opened via:

```python
	import coord_util.trajdb as trajdb

	db = trajdb.open_trajectory_database('mytraj.db', create=False)
```

The optional `create` argument being set to `False` will cause an
exception to be raised if the file does not exist.

#### Creating a new trajdb

A new trajdb named `mytraj.db` for geometries with `ndof` degrees of
freedom (e.g., water molecules have 3*3=6 degrees of freedom) can be
created via:

```python
	import coord_util.trajdb as trajdb

	db = trajdb.open_trajectory_database('mytraj.db', ndof=ndof, create=True)
```

The optional `create` argument being set to `True` will cause `trajdb`
to overwrite any previously existing database.

The `ndof` argument is required when creating a new database.

### Adding and retrieving samples

#### New trajectory insertion

Suppose we have an iterator `traj_iter`, which yields numpy vectors of
molecule geometries representing snapshots from a trajectory with
timestep `dt` (with initial time 0).  This sequence can be inserted
into the `trajdb` stored referenced by `db` via:

```python

  with db.session():
    for x in traj_iter:
      samplekey = db.new_sample(x)
      db.step_time(dt)

  db.close()
```

The samplekey returned by `new_sample` is a unique identifier
representing the geometry in the database.  

The `session` ensures that the SQL database is only modified if all of
the samles are successfully inserted.  The `close` function ensures
that the samples are written to the `hdf5` database.

#### Multiple trajectory insertion

It is possible to denote that samples in the `trajdb` come from
multiple independent trajectories by using the `new_trajectory` and
`switch_trajectory` functions.  Suppose `traj_iters` is an iterator of
trajectory iterators.  Then the following will insert multiple
trajectories each with initial time 0 and time step `dt`.


```python
  with db.session():
    for traj_iter in traj_iters:
      trajkey = db.new_trajectory()
      for x in traj_iter:
        samplekey = db.new_sample(x)
        db.step_time(dt)

  db.close()
```

The `trajkey` returned from `new_trajectory` is a unique identifier
representing the trajectory in the database.

Alternatively, a previous inserted trajectory can be "resumed" by
calling `db.switch_trajectory` with an existing `trajkey`.

#### Sample retrieval

Geometries inserted into a `trajdb` can be retrieved as long as the
hdf5 database is present, and the samplekey of the desired geometry is
known.  The geometry associated with a given samplekey can be
retrieved via `get_sample` such as:


```python
  x = db.get_sample(samplekey)
```

Then `x` will be a numpy array holding the geometry of the
`samplekey`th geometry.  All the samplekeys for the database can be
retrieved by the `select` function (described in more detail below):

```python
  for samplekey in db.select([db.samplekeys.samplekey]):
    x = db.get_sample(samplekey)
    print 'Sample %s is %s % (samplekey, x)
```

To simply iterate over the trajectories (in samplekey order), use the
`db.iter_coordinates` function.  The previous example is equivalent to
the following:

```python
  for samplekey, x in db.iter_coordinates():
    print 'Sample %s is %s % (samplekey, x)
```

### Adding physical properties 

In the most common case, molecule samples are described through a
smaller set (i.e., smaller than the number of degrees of freedom) of
real valued functions of the complete geometry.  Examples of such
functions are dihedral angles, bond lengths, or rmsd from a specific
geometry. 

The `trajdb` module provides functions to associate real valued
properties to the samplekeys describing the geometries in the
database, and to query the database for based on these properties.

The physical properties for a trajdb can be queried without the
presence of the (often much larger) full geometries (in the hdf5
database).

#### Adding new physical properties

Suppose we want to describe molecules by the dihedral involving atoms
1, 2, 3 and 4; named psi.  This attribute can be done in the following
way:

```python
  def psis():

    for samplekey, x in db.iter_coordinates():
      yield samplekey, dihedral(x, 1, 2, 3, 4)


  db.add_sample_table('psi')  
  # the above adds the attribute psi to `db`

  db.insert(db.psi, psis())
```
  
### Retrieving physical properties

By default, time and trajectory keys are associated with each sample.
We can select these values, along with any additional properties in
the following way:

```python

   for row in db.select([db.trajectories.trajectorykey, db.times.time, db.psis.value]):
     print 'Trajectory %d at time %f had psi=%f' % row
````


### Selecting properties by range

To restrict the samples selected, the `select` function includes a where keyword:

```python

   for row in db.select([db.trajectories.trajectorykey, db.times.time], 
                        where=((db.psis.value>0.)&(db.psis.value<3.14/2))):
     print 'Trajectory %d at time %f had psi between 0 and pi/2' % row
```

## GNAT

The `coord_util` module includes efficient functions for searching for
nearest neighbors in a set of numpy arrays.  The code is the Geometric
Near-neighbor Access Tree (GNAT), and closely follows the strategy
outlined by Brin (infolab.standford.edu/~sergey/near.html). 

'Nearest' in this context refers to any metric, but the `gnat` code
defaults to `rmsd`.

This GNAT library is designed to work with a trajdb, but can easily be
freed from this constraint (see test_gnat.py).

### Building

Assuming `db` is a `tradb`, we can build a GNAT indexing the
structures via 

```python
  import coord_util.gnat as g

  gnat = g.build_gnat(db)
```

### Searching

Given a sample `x`, the samplekeys of all neighbors closer than `r`
according to the metric can be obtained using the `query` function.


```python
  for samplekey in gnat.query(x, r):
    print 'Sample %d is closer than %f' % (samplekey, r)
```

The nearest neighbor can be identified by the `neighbor_query` function:

```python
  print 'The nearest neighbor is sample %d' % (g.neighbor_query(x)[0])
```

### Saving/Loading

A GNAT would not be very useful if we had to recreate the structure
everytime we wanted to do queries.  The GNAT can be saved to the
`trajdb` by using the `gnat` module's `save_gnat` function.

```python
  g.save_gnat(gnat)
```

The GNAT stored in the `trajdb` can be restored via the `load_gnat`
function.

```python
  restored_gnat = g.load_gnat(db)
```

