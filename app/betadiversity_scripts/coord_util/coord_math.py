"""Python code mirroring rmsd.f90.

The convention here is to emulate the fortran codes, and to be used in
geomtry from the coord_math module.  The arguments named coordinates
are flat 3*n dimensional arrays, and the internal coords variables are
(n,3) dimensional arrays.

"""

import math

import numpy as np

def rmsd_rotation(coordinates1, coordinates2):
    """Compute the rotation matrix to optimally align mol2 to mol1."""
    
    u = coordinates1.reshape((-1, 3))
    v = coordinates2.reshape((-1, 3))

    cov = np.dot(u.transpose(), v)
    [U, S, Vt] = np.linalg.svd(cov)

    if np.linalg.det(U) * np.linalg.det(Vt) < 0:
        # Invert the coordinate assocated with the least singular
        # value.  

        # It's ok to have inversion of 2 coordinates(it's just a 180
        # degree rotation), but not 3 or 1.  Inverting the
        # transformation associated with the least singular value will
        # give the least possible increase in RMSD.
        for idx in xrange(3):
            Vt[2, idx] = -Vt[2, idx]

    # Optimally align v and u.
    return np.dot(Vt.transpose(), U.transpose())



def center_of_geometry(coordinates):
    coords = coordinates.reshape((-1, 3))
    cog = np.array([0.0, 0.0, 0.0])
    num_atom = coords.shape[0]
    for idx in xrange(num_atom):
        cog = cog + coords[idx]

    cog = cog / num_atom

    return cog

def rmsd(coordinates1, coordinates2):
    """Compute the RMSD distance between the two molecules."""

    coordinates1 = np.array(coordinates1)
    coordinates2 = np.array(coordinates2)

    coord1 = translate(coordinates1, -center_of_geometry(coordinates1))
    coord2 = translate(coordinates2, -center_of_geometry(coordinates2))

    u = coord1.reshape((-1, 3))
    v = coord2.reshape((-1, 3))
    cov = np.dot(u.transpose(), v)
    s = np.linalg.svd(cov, compute_uv=0)


    if np.linalg.det(cov) < 0.:
        s[2] = -s[2]

    num_atoms = u.shape[0]
    rmsd = abs(np.dot(coord1, coord1) + np.dot(coord2, coord2) - 2. * np.sum(s))/num_atoms

    if rmsd < 0.:
        if abs(rmsd) < 1e-7:
            rmsd = abs(rmsd)
    return np.sqrt(rmsd)


def translate(coordinates, translation_vector):
    """Translate each atom in  molecule by adding the translation vector."""

    coords = coordinates.reshape((-1, 3)).copy()
    for idx in xrange(len(coords)):
        coords[idx] = coords[idx] + translation_vector

    return coords.reshape((-1, ))

def flat_rmsd(coordinates1, coordinates2):
    """Return unminimized rmsd."""
    num_atoms = len(coordinates1)/3
    delta= coordinates1 - coordinates2
    return np.sqrt(np.dot(delta, delta)/num_atoms)



def dihedral(x, i1, i2, i3, i4):
    radian = 180./math.pi

    xa = x[3 * (i1 - 1)]
    xb = x[3 * (i2 - 1)]
    xc = x[3 * (i3 - 1)]
    xd = x[3 * (i4 - 1)]
    ya = x[3 * (i1 - 1) + 1]
    yb = x[3 * (i2 - 1) + 1]
    yc = x[3 * (i3 - 1) + 1]
    yd = x[3 * (i4 - 1) + 1]
    za = x[3 * (i1 - 1) + 2]
    zb = x[3 * (i2 - 1) + 2]
    zc = x[3 * (i3 - 1) + 2]
    zd = x[3 * (i4 - 1) + 2]
    
    xba = xb - xa
    yba = yb - ya
    zba = zb - za
    xcb = xc - xb
    ycb = yc - yb
    zcb = zc - zb
    xdc = xd - xc
    ydc = yd - yc
    zdc = zd - zc
    xt = yba*zcb - ycb*zba
    yt = xcb*zba - xba*zcb
    zt = xba*ycb - xcb*yba
    xu = ycb*zdc - ydc*zcb
    yu = xdc*zcb - xcb*zdc
    zu = xcb*ydc - xdc*ycb
    rt2 = xt*xt + yt*yt + zt*zt
    ru2 = xu*xu + yu*yu + zu*zu
    rtru = math.sqrt(rt2 * ru2)
    if rtru != 0.0:
       cosine = (xt*xu + yt*yu + zt*zu) / rtru
       cosine = min(1.0,max(-1.00,cosine))
       dihed = radian * math.acos(cosine)
       sign = xba*xu + yba*yu + zba*zu
       if sign < 0.:
           dihed = -dihed
    return dihed

def get_atom_coords(mol, idx):
    """Get the coordinates of the idxth (1-based) atom."""
    return mol[3*(idx-1):3*(idx)]

def atom_dist(mol, idx, jdx):
    """Distance between the idxth and jdxth (1-based) atom in the geometry."""
    return np.linalg.norm(get_atom_coords(mol, idx) - get_atom_coords(mol, jdx))

def euler_rotation_matrix(alpha, beta=0.0, gamma=0.0):
    ca = math.cos(alpha)
    cg = math.cos(gamma)
    cb = math.cos(beta)
    sa = math.sin(alpha)
    sb = math.sin(beta)
    sg = math.sin(gamma)
    rotation_matrix = np.array([[ca * cg - sa * cb * sg, -ca * sg - sa * cb * cg, sb * sa],
                                   [sa * cg + ca * cb * sg, -sa * sg + ca * cb * cg, -sb * ca],
                                   [sb * sg,                sb * cg,                 cb]])

    return rotation_matrix

def transform(mol, transform_matrix):
    """Transform each atom in  molecule by applying the 3x3 transform_matrix."""
    return np.dot(mol.reshape((-1,3)), transform_matrix).reshape((-1,))

def rotate_euler(coords, alpha, beta=0.0, gamma=0.0):
    """Rotate the molecule around the origin according to Euler angles."""
    return transform(coords, euler_rotation_matrix(alpha, beta, gamma))


def rmsd_align_transform(x, y):
    """Return the t1, r, t2 (translation, rotation, translation) for y to minimize the flat_rmsd of y and x.

    The flat_rmsd will be minimized by translating y by t1, rotating
    by r, and translating by t2.

    See the definition of align for use.

    """

    t1 = -center_of_geometry(y)
    t2 = center_of_geometry(x)
    r = rmsd_rotation(translate(x, -t2), translate(y, t1))

    return t1, r, t2


def align(x, y):
    """Return y transformed to minimize flat_rmsd to x."""
    t1, r, t2 = rmsd_align_transform(x, y)
    return translate(transform(translate(y, t1), r), t2)


def subalign(top, x, y):
    """Align y to x according to the subtopology described by top.

    top is expected to be a Topology class from the topology module.

    """
    t1, r, t2 = rmsd_align_transform(top.get_coords(x), top.get_coords(y))
    return translate(transform(translate(y, t1), r), t2)
    


# Overwrite above definitions with a fast fortran implementation
try:
    from _coord_math import *
except ImportError:
    print 'WARNING: unable to import fortran module, so the less efficient python codes are being used instead.'
    pass
