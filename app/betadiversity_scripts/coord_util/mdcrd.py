"""File like interface for reading Amber mdcrd files."""

import numpy as np

from floatx import floatx

STDOPEN=open

class MDCrdError(Exception):
    pass

class MDCrdFile(object):

    crd_per_line=10
    crd_fmt='%8.3f'

    def __init__(self, name, mode='r', num_atoms=None, 
                 comment=None,
                 box=False):

        if comment is None:
            comment = "Created by " + __file__
        available_modes = ['r', 'w', 'a']
        if mode not in available_modes:
            raise MDCrdError("Mode string must be one of %s" % (', '.join("'%s'" % mode for mode in available_modes)))

        if mode=='w':
            self.file = STDOPEN(name, mode)
            self.file.write(comment + '\n')
            self.comment = comment
        elif mode=='a':
            f = STDOPEN(name)
            self.comment = f.next()[:-1] # strip off the trailing newline
            f.close()
            self.file = STDOPEN(name, mode)
        elif mode=='r':
            if num_atoms is None:
                raise MDCrdError("num_atoms option must be provided to open mdcrd files for reading.")

            self.num_crds = num_atoms * 3
            self.file = STDOPEN(name, mode)
            self.comment = self.file.next()[:-1] # strip off the trailing newline
        else:
            raise MDCrdError("unrecognized mode '%s'" % mode)

        self.name = name
        self.box=box

    def __enter__(self):
        return self
        
    def __exit__(self, *args):
        self.close()
        return all(arg is None for arg in args)

    @property
    def num_atoms(self):
        return 3 * self.num_crds

    @property
    def crd_len(self):
        return len(self.crd_fmt % 1.0)

    def close(self):
        self.file.close()

    def __iter__(self):
        return self

    def next(self):
        num_crds_left = self.num_crds
        crd_per_line = self.crd_per_line        
        crd_len = self.crd_len

        crds = []

        f = self.file

        while num_crds_left > 0:
            line = f.next()
            num_on_line = min(num_crds_left, crd_per_line)

            last_idx = 0
            for next_idx in xrange(crd_len, crd_len * (num_on_line+1), crd_len):
                crds.append(floatx(line[last_idx:next_idx]))
                last_idx = next_idx
                
            num_crds_left -= num_on_line

        if not self.box:
            return np.array(crds)

        line = f.next()
        num_on_line = len(line)/crd_len

        box_crds = []
        last_idx = 0
        for next_idx in xrange(crd_len, crd_len * (num_on_line+1), crd_len):
            box_crds.append(floatx(line[last_idx:next_idx]))
            last_idx = next_idx

        return np.array(crds), np.array(box_crds)


    def read(self):
        return list(self)
        

    def write(self, x):
        if self.box:
            x, box = x
        else:
            box=None

        fmt = self.crd_fmt
        crd_per_line = self.crd_per_line

        f = self.file
        crd_count = 0
        for crd in x:
            f.write(fmt % crd)
            crd_count += 1
            if crd_count == crd_per_line:
                f.write('\n')
                crd_count=0

        if crd_count != 0:
            f.write('\n')
            
        if box:
            for crd in box:
                f.write(fmt % crd)
                crd_count += 1

            f.write('\n')
            
open=MDCrdFile        

def write_mdcrds(filename, coords, comment=None, box=False):
    """Write the list of molecules to an mdcrd file."""

    with MDCrdFile(filename, 'w', comment=comment, box=box) as f:
        for coord in coords:
            f.write(coord)

def mdcrds_in_file(filename, num_atoms, box=False):
    """Return an iterator of the coords in the mdcrd file."""
    with MDCrdFile(filename, 'r', box=box, num_atoms=num_atoms) as f:
        for coord in f:
            yield coord
                
