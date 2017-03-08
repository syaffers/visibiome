"""Read and write AMBER rst files."""

import numpy as np

from floatx import floatx

STDOPEN=open

class RSTError(Exception):
    pass

class RSTFile(object):

    crd_per_line=6
    crd_fmt='%12.6f'

    def __init__(self, name, mode='r',
                 comment=None,
                 dynamics=False,
                 box=False):

        if comment is None:
            comment = "Created by " + __file__
        available_modes = ['r', 'w']
        if mode not in available_modes:
            raise RSTError("Mode string must be one of %s" % (', '.join("'%s'" % mode for mode in available_modes)))

        if mode=='w':
            self.file = STDOPEN(name, mode)
            self.file.write(comment + '\n')
            self.comment = comment
        elif mode=='r':
            self.file = STDOPEN(name, mode)
            self.comment = self.file.next()[:-1] # slices off the terminating newline
        else:
            raise RSTError("unrecognized mode '%s'" % mode)

        self.name = name
        self.dynamics = dynamics
        self.box=box

        self._written = False

    def __enter__(self):
        return self
        
    def __exit__(self, *args):
        self.close()
        return all(arg is None for arg in args)

    @property
    def crd_len(self):
        return len(self.crd_fmt % 1.0)

    def close(self):
        self.file.close()

    def __iter__(self):
        return self

    def next(self):
        f = self.file
        self.num_atoms = int(f.next())

        crd_per_line = self.crd_per_line        
        crd_len = self.crd_len

        crds = []



        num_crds_left = 3 * self.num_atoms
        while num_crds_left > 0:
            line = f.next()
            num_on_line = min(num_crds_left, crd_per_line)

            last_idx = 0
            for next_idx in xrange(crd_len, crd_len * (num_on_line+1), crd_len):
                crds.append(floatx(line[last_idx:next_idx]))
                last_idx = next_idx
                
            num_crds_left -= num_on_line

        if not self.dynamics and not self.box:
            return np.array(crds)

        if self.dynamics:
            num_crds_left = self.num_crds
            vel_crds = []
            while num_crds_left > 0:
                line = f.next()
                num_on_line = min(num_crds_left, crd_per_line)

                last_idx = 0
                for next_idx in xrange(crd_len, crd_len * (num_on_line+1), crd_len):
                    vel_crds.append(floatx(line[last_idx:next_idx]))
                    last_idx = next_idx

                num_crds_left -= num_on_line

            if not self.box:
                return np.array(crds), np.array(vel_crds)


        line = f.next()
        num_on_line = len(line)/crd_len

        box_crds = []
        last_idx = 0
        for next_idx in xrange(crd_len, crd_len * (num_on_line+1), crd_len):
            box_crds.append(floatx(line[last_idx:next_idx]))
            last_idx = next_idx


        if self.dynamics:
            return np.array(crds), np.array(vel_crds), np.array(box_crds)

        return np.array(crds), np.array(box_crds)
        

    def read(self):
        return self.next()

    def write(self, x):
        if self._written:
            raise RSTError("Attempt to write more than one geometry to RST file.")

        f = self.file

        f.write('%5d\n' % (len(x)//3))

        if self.box:
            x, box = x
        else:
            box=None

        fmt = self.crd_fmt
        crd_per_line = self.crd_per_line


        crd_count = 0
        for crd in x:
            f.write(fmt % crd)
            crd_count += 1
            if crd_count == crd_per_line:
                f.write('\n')
                crd_count = 0

        if crd_count != 0:
            f.write('\n')
            
        if box:
            for crd in box:
                f.write(fmt % crd)
                crd_count += 1

            f.write('\n')
            
        
open=RSTFile

def write_rst(filename, coord, comment=None, dynamics=False, box=False):
    """Write a geometry to an RST file."""
    with RSTFile(filename, 'w', comment=comment, dynamics=dynamics, box=box) as f:
        f.write(coord)

def read_rst(filename, dynamics=False, box=False):
    """Return the geometry in an rst file."""
    with RSTFile(filename, 'r', dynamics=dynamics, box=box) as f:
        return f.read()

        
