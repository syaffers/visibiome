"""File like interface for reading gromacs gro files."""

import os
import numpy as np

import topology as t

STDOPEN=open

class GroError(Exception):
    pass

class GroFile(object):

    resnum_form = '%5d'
    resname_form = '%5s'
    atom_name_form = '%5s'
    atom_num_form = '%5d'
    position_form = '%8.3f'
    velocity_form = '%8.4f'

    @property
    def pre_crd_form(self):
        return ''.join([self.resnum_form, self.resname_form, self.atom_name_form, self.atom_num_form])

    @property
    def pre_crd_len(self):
        return len(self.pre_crd_form % (0, '', '', 0))

    @property
    def crd_len(self):
        return len(self.position_form % 0)

    @property
    def crd_form(self):
        return ''.join([self.position_form] * 3)

    @property
    def vel_form(self):
        return ''.join([self.velocity_form] * 3)

    @property
    def vel_len(self):
        return len(self.velocity_form % 0)


    def __init__(self, name, mode='r',
                 decimals=3,
                 dynamics=False,
                 box=False):

        available_modes = ['r']
        if mode not in available_modes:
            raise GroError("Mode string must be one of %s" % (', '.join("'%s'" % mode for mode in available_modes)))

        if mode=='r':
            self.file = STDOPEN(name, mode)
            self.name = name

        self.position_form='%%%d.%df' % (decimals+5,decimals)
        self.velocity_form='%%%d.%df' % (decimals+5,decimals)

        self.dynamics=dynamics
        self.box=box

    def __enter__(self):
        return self
        
    def __exit__(self, *args):
        self.close()
        return all(arg is None for arg in args)

    def close(self):
        self.file.close()

    def __iter__(self):
        return self

    def next(self):
        self.comment=self.file.next()[:-1] # slice up to the new line
        self.num_atoms=int(self.file.next())

        crds = []
        vels = []
        pre_crd_len = self.pre_crd_len
        crd_len = self.crd_len
        pre_vel_len = pre_crd_len + 3 * crd_len
        vel_len = self.vel_len
        for count in xrange(self.num_atoms):
            line = self.file.next()
            last_pos = pre_crd_len
            for pos in xrange(pre_crd_len + crd_len, pre_crd_len + crd_len * 4, crd_len):
                crds.append(float(line[last_pos:pos]))
                last_pos = pos

            if self.dynamics:
                for pos in xrange(pre_vel_len + vel_len, pre_vel_len + vel_len * 4, vel_len):
                    vels.append(float(line[last_pos:pos]))
                    last_pos = pos

        crds = 10. * np.array(crds) # mulitply by 10 to convert NM to ANG

        if self.dynamics:
            vels = 10. * np.array(vels)

        if not self.box:
            if self.dynamics:
                return crds, vels
            return crds

        box_line = self.file.next()

        box = np.array([float(x) for x in box_line.split()])

        if self.dynamics:
                return crds, vels, box
        else:
            return crds, box


    def read(self):
        return list(self)

open=GroFile
        

def read_residues(gro_file_name):
    """Return a sequence of resname, atom_names for each molecule in the geometry."""

    with open(gro_file_name) as f:
        comment = f.next()
        num_atoms = int(f.next())
        last_resnum = None
        last_resname = None
        
        atom_names = []
        for count in xrange(num_atoms):
            line = f.next()
            resnum = int(line[:5])
            resname = line[5:10]
            atom_name = line[10:15]
            atom_num = int(line[15:20])
            
            if resnum != last_resnum:
                if last_resnum is not None:
                    yield last_resname, atom_names
                    atom_names = []

                last_resnum = resnum
                last_resname = resname
                atom_names.append(atom_name)

        
        yield last_resname, atom_names
            
        

def read_topology(gro_file_name, name=None):
    if name is None:
        name = os.path.splitext(gro_file_name)[0]

    monomers = []
    for resname, atom_names in read_residues(gro_file_name):
        monomers.append(t.Molecule(resname, atom_names))
    
    return t.Polymer(name, monomers)
