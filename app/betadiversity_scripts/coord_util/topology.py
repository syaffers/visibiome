
import re

import numpy as np

def get_atoms_adapter(monomer, arg):
    return monomer.get_atoms(arg)

def get_atomset_adapter(monomer, arg):
    return monomer.get_atomset(arg)


def get_not_atomset_adapter(monomer, arg):
    return monomer.get_not_atomset(arg)

def regex_get_other_atoms_adapter(monomer, arg):
    return monomer.regex_get_other_atoms(arg)

def regex_get_atoms_adapter(monomer, arg):
    return monomer.regex_get_atoms(arg)


def filter_atomset(s):
    s = set(s)
    def filter_condition(atom_name):
        return atom_name in s

    return filter_condition


def filter_not_atomset(s):
    s = set(s)
    def filter_condition(atom_name):
        return atom_name not in s

    return filter_condition


def filter_regex(regex):
    def filter_condition(atom_name):
        return re.match(regex, atom_name)
    return filter_condition

def filter_not_regex(regex):
    def filter_condition(atom_name):
        return not re.match(regex, atom_name)
    return filter_condition


def change_by_atom_ndof(offsets_by_atom, new_ndof):
    """Adapt offsets_by_atom vector to one with the new ndof."""
    old_ndof = offsets_by_atom.shape[1]
    indices = offsets_by_atom[:, 0]/old_ndof

    num_atoms = offsets_by_atom.shape[0]

    dof_delta = np.array(range(new_ndof))
    
    indices_by_atom = np.tile(indices, (1, new_ndof)).transpose()
    dof_by_atom = np.tile(dof_delta, (num_atoms, 1))

    new_offsets_by_atom = (indices_by_atom 
                           + dof_by_atom)

    return new_offsets_by_atom

        
class TopologyError(Exception):
    pass

class Topology(object):

    def __init__(self, name, atom_offsets=None, start=0, shape=None, target_offsets=None, ndof=3):

        self.name = name

        self.ndof = ndof

        # try:
        #     atoms = self.atoms
        # except AttributeError:
        #     pass
        
        # try:
        #     monomers = self.monomers
        # except AttributeError:
        #     pass

        if atom_offsets is None:
            atom_offsets = np.array(range(start, start + ndof * self.num_atoms))
        elif len(atom_offsets) % ndof != 0:
            raise TopologyError("Bad offset length: len(%s) = %s with ndof %s" % (atom_offsets, len(atom_offsets), ndof))

        self.atom_offsets = np.array(atom_offsets)

        if shape is None:
            self.shape = self.atom_offsets.shape
        else:
            self.shape = shape

        if target_offsets is None:
            self.target_offsets = atom_offsets
        else:
            self.target_offsets = target_offsets

        if self.target_offsets.shape != self.atom_offsets.shape:
            raise TopologyError("atom and target offsets do not have the same shape")


    def indent_str(self, level):
        name = self.name
        myindent = '    ' * level
        try:
            mols = self.monomers
            mytype = '<< %s Polymer' % name
            mysubstrs = [mol.indent_str(level+1) for mol in mols]
            subindent = '\n'
            mysubstr = "\n%s\n%s >>" % (subindent.join(mysubstrs), myindent)
        except AttributeError:
            atoms = self.atoms
            mytype = '<< %s Molecule' % name
            mysubstr = ' %s >>' % (', '.join(atoms))
            
        return '%s%s%s' % (myindent, mytype, mysubstr)


    def __str__(self):
        return self.indent_str(0)


    @property
    def offsets_by_atom(self):
        try:
            return self.atom_offsets.reshape(-1, self.ndof)
        except ValueError:
            raise Exception("can't resize %s" % self.atom_offsets)


    @property
    def targets_by_atom(self):
        try:
            return self.target_offsets.reshape(-1, self.ndof)
        except ValueError:
            raise Exception("can't resize %s" % self.target_offsets)


    def get_coords(self, x):
        try:
            return x[self.atom_offsets]
        except TypeError:
            x = np.array(x)
            return x[self.atom_offsets]


    def set_coords(self, x, new_x):
        x[self.atom_offsets] = new_x

    def transfer_coords(self, y, x):
        y[self.target_offsets] = x[self.atom_offsets]
        return y


    def lift_coords(self, x):
        y = np.zeros(self.shape)
        self.transfer_coords(y, x)
        return y

class Molecule(Topology):

    def __init__(self, name, atoms, atom_offsets=None, start=0, shape=None, target_offsets=None, ndof=3):
        self.name = name
        self.atoms = atoms
        Topology.__init__(self, name, atom_offsets=atom_offsets, start=start, shape=shape, target_offsets=target_offsets,
                          ndof=ndof)

    def copy(self):
        return Molecule(self.name, self.atoms[:],
                        atom_offsets=self.atom_offsets.copy(),
                        shape=self.shape,
                        target_offsets=self.target_offsets.copy(),
                        ndof=self.ndof)


    @property
    def num_atoms(self):
        return len(self.atoms)

    @property
    def atom_names(self):
        return self.atoms


    def __len__(self):
        return len(self.atoms)

    def _get(self, filter_condition):
        """Generic function to return a sub topology."""
        idx = -1
        atoms_in_query = []
        offset_indices = []
        for idx, atom_name in enumerate(self.atoms):
            if filter_condition(atom_name):
                offset_indices.append(idx)
                atoms_in_query.append(atom_name)

        atom_offsets = self.offsets_by_atom[offset_indices].reshape((-1,))
        target_offsets = self.targets_by_atom[offset_indices].reshape((-1,))

        return Molecule(self.name, 
                        atoms=atoms_in_query, 
                        atom_offsets=atom_offsets, 
                        shape=self.shape, 
                        target_offsets=target_offsets,
                        ndof=self.ndof)
        

    def get_atoms(self, query):
        return self._get(filter_atomset([query]))

    def get_atomset(self, query):
        return self._get(filter_atomset(query))

    def get_not_atomset(self, query):
        return self._get(filter_not_atomset(query))


    def regex_get_atoms(self, query):
        return self._get(filter_regex(query))

    def regex_get_other_atoms(self, query):
        return self._get(filter_not_regex(query))

    def lift_topology(self, other_topology, namemap=None,
                      reorder=False):

        if self.ndof != other_topology.ndof:
            raise TopologyError("Can not raise a topology with %s dof to %s dof." % (other_topology.ndof, self.ndof))

        if namemap:
            other_atom_names = [namemap(atom_name) for atom_name in other_topology.atoms]
        else:
            other_atom_names = other_topology.atoms

        if len(set(self.atoms)) != len(self.atoms):
            raise TopologyError("Can not reorder atoms in a molecule with redundant atom names.")

        if ((reorder and (set(self.atoms) != set(other_atom_names)))
            or len(set(other_atom_names) - set(self.atoms)) > 0):
            first = '\n'.join(set(self.atoms) - set(other_atom_names))
            second = '\n'.join(set(other_atom_names) - set(self.atoms))
            raise TopologyError("Can not reorder topology %s to %s because the set of atom names do not match.\nIn first but not second: %s\nsecond but not first: %s" % (self.name, other_topology.name, first, second))
        
        offsets_by_atom = self.offsets_by_atom
        other_offsets_by_atom = other_topology.offsets_by_atom

        atom_offsets = []
        target_offsets = []

        for jdx, atom_name in enumerate(other_atom_names):
            idx = self.atoms.index(atom_name)
            
            atom_offsets.extend(list(other_offsets_by_atom[jdx]))
            target_offsets.extend(list(offsets_by_atom[idx]))

        atom_offsets = np.array(atom_offsets)
        target_offsets = np.array(target_offsets)

        return Molecule(self.name, 
                        other_atom_names, 
                        atom_offsets=atom_offsets, 
                        shape=self.shape, 
                        target_offsets=target_offsets)

    def change_ndof(self, new_ndof):
        new_offsets_by_atom = change_by_atom_ndof(self.offsets_by_atom, new_ndof)
        new_targets_by_atom = change_by_atom_ndof(self.targets_by_atom, new_ndof)


        assert len(self.shape) == 1, str(self.shape)

        new_shape = (self.shape[0]/self.ndof * new_ndof, )

        return Molecule(self.name, 
                        atoms=self.atoms, 
                        atom_offsets=new_offsets_by_atom.reshape((-1,)), 
                        shape=new_shape, 
                        target_offsets=new_targets_by_atom.reshape((-1,)),
                        ndof=new_ndof)

        


    def get_contiguous_topology(self, start=0):
        return self.__class__(atoms=self.atoms, start=start, ndof=self.ndof, name=self.name)
        

def monomers_offset_vector(monomers):
    atom_offsets = []
    for monomer in monomers:
        atom_offsets.extend(list(monomer.atom_offsets))

    return np.array(atom_offsets)


def monomers_target_vector(monomers):
    target_offsets = []
    for monomer in monomers:
        target_offsets.extend(list(monomer.target_offsets))

    return np.array(target_offsets)
        

class Polymer(Topology):

    def __init__(self, name, monomers, fixed_monomers=False, atom_offsets=None, start=0, shape=None, target_offsets=None, ndof=3):
        # If the offsets of the monomers are predetermined,
        # fixed_monomers should be True, otherwise we will adjust them
        # to be contiguous.
        self.name = name 
        
        if fixed_monomers:
            concrete_monomers = monomers
        else:
            start = 0
            concrete_monomers = []

            for monomer in monomers:

                monomer = monomer.get_contiguous_topology(start)
                concrete_monomers.append(monomer)
                start = monomer.atom_offsets[-1] + 1

        self.monomers = concrete_monomers
        if atom_offsets is None:
            atom_offsets = monomers_offset_vector(self.monomers)

        if target_offsets is None:
            target_offsets = monomers_target_vector(self.monomers)

        if shape is None:
            shape = atom_offsets.shape

        for monomer in self.monomers:
            monomer.shape = shape

        Topology.__init__(self, name, atom_offsets=atom_offsets, start=start, shape=shape, target_offsets=target_offsets,
                          ndof=ndof)


    def flatten(self):
        """Flatten a Polymer of Polymers into a single chain."""
        if not isinstance(self.monomers[0], Polymer):
            raise Exception("Only polymers of polymers can be flattened.")

        new_monomers = []
        for monomer in self.monomers:
            new_monomers.extend(monomer.monomers)

        return Polymer(self.name, new_monomers, fixed_monomers=True, ndof=self.ndof)


    def monomers_slice(self, i, j):
        the_slice = self.monomers.__getslice__(i, j)
        if len(the_slice) == 0:
            raise Exception("Empty monomers slice range %d %d for %d monomers" % (i, j, len(self.monomers)))
        return Polymer(self.name, the_slice, fixed_monomers=True, ndof=self.ndof)

    def get_monomer_by_index(self, idx):
        return self.monomers[idx]


    @property
    def sequence(self):
        return [monomer.name for monomer in self.monomers]

    @property
    def atoms(self):
        atom_names = []
        for monomer in self.monomers:
            atom_names.extend(monomer.atom_names)
        return atom_names
    
    @property
    def num_monomers(self):
        return len(self.monomers)

    @property
    def num_atoms(self):
        return sum(monomer.num_atoms for monomer in self.monomers)

    def __len__(self):
        return sum(len(monomer) for monomer in self.monomers)

    def get_monomer(self, query):
        concrete_monomers = [monomer for monomer in self.monomers if monomer.name == query]
        return Polymer(self.name, concrete_monomers, fixed_monomers=True, ndof=self.ndof)

    def _get(self, get_submonomer, query):
        """Generic function to return a sub topologies of the comprised molecules."""
        concrete_monomers = []
        for monomer in self.monomers:
            sub_monomer = get_submonomer(monomer, query)
            concrete_monomers.append(sub_monomer)

        return Polymer(self.name, concrete_monomers, fixed_monomers=True, ndof=self.ndof)
        

    def get_atoms(self, query):
        return self._get(get_atoms_adapter, query)

    def get_atomset(self, query):
        return self._get(get_atomset_adapter, query)

    def get_not_atomset(self, query):
        return self._get(get_not_atomset_adapter, query)


    def regex_get_atoms(self, query):
        return self._get(regex_get_atoms_adapter, query)

    def regex_get_other_atoms(self, query):
        return self._get(regex_get_other_atoms_adapter, query)

    def lift_topology(self, other_topology, namemap=None,
                      reorder=False):

        if self.ndof != other_topology.ndof:
            raise TopologyError("Can not raise a topology with %s dof to %s dof." % (other_topology.ndof, self.ndof))
        


        if self.num_monomers != other_topology.num_monomers:
            raise TopologyError("Topologies have incompatible numbers of monomers: %d != %d" % (self.num_monomers, other_topology.num_monomers))

        concrete_monomers = []

        for monomer, other_monomer in zip(self.monomers, other_topology.monomers):
            concrete_monomers.append(monomer.lift_topology(other_monomer, namemap=namemap,
                                                           reorder=reorder))

        return Polymer(self.name, concrete_monomers, fixed_monomers=True, shape=self.shape, ndof=self.ndof)


    def change_ndof(self, new_ndof):

        concrete_monomers = []

        for monomer in self.monomers:
            concrete_monomers.append(monomer.change_ndof(new_ndof))


        assert len(self.shape) == 1, str(self.shape)

        new_shape = (self.shape[0]/self.ndof * new_ndof, )

        return Polymer(self.name, concrete_monomers, shape=new_shape, ndof=new_ndof)

    def get_contiguous_topology(self, start=0):
        concrete_monomers = []

        for monomer in self.monomers:
            concrete_monomer = monomer.get_contiguous_topology(start)
            concrete_monomers.append(concrete_monomer)

            if concrete_monomer.num_atoms > 0:
                start = concrete_monomer.atom_offsets[-1] + 1
            
        return Polymer(self.name, concrete_monomers, fixed_monomers=True, ndof=self.ndof)


def namedict(d):
    """reorder namemap using the dict."""

    def namemap(atom_name):
        try:
            return d[atom_name]
        except KeyError:
            return atom_name

    return namemap


class Monomers(object):
    """Store a dictionary of monomers for transformation into a sequence."""
    
    def __init__(self, monomers):
        self.monomer_dict = dict((monomer.name, monomer) for monomer in monomers)

    def sequence(self, resseq):
        monomer_dict = self.monomer_dict
        return [monomer_dict[resname].copy() for resname in resseq]
    
