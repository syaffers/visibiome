!     coord_math.f90  -- Implement routines for molecular coordinate math

!      Molecules are described by one-dimensional arrays in the format
!      [x1, y1, z1, ..., xn, yn, zn]

module coord_math_mod

contains

  function det(mat)
    ! Compute the determinant of a 3x3 matrix
    implicit none
    real*8 :: det
    real*8, dimension(3,3) :: mat
    
    det = (mat(1,1) * (mat(2,2) * mat(3,3) - mat(2,3) * mat(3,2)) &
    - mat(1,2) * (mat(2,1) * mat(3,3) - mat(3,1) * mat(2,3)) &
    + mat(1,3) * (mat(2,1) * mat(3,2) - mat(3,1) * mat(2,2)))

  end function det

  subroutine center_of_geometry(mol, cog, natom)
    ! Compute the center of geometry of the molecule
    implicit none
    real*8, dimension(3*natom), intent(in) :: mol
    real*8, dimension(3), intent(out) :: cog
    integer, intent(in) :: natom
!f2py real*8, dimension(3*natom), intent(in) :: mol
!f2py real*8, dimension(3), intent(out) :: cog
!f2py integer optional,depend(mol) :: natom=(len(mol))/3
    
    integer :: idx

    cog = 0.
    do idx=1, natom
       cog = cog + mol(3*(idx-1) + 1:3*idx)
    end do

    cog = cog/natom

  end subroutine center_of_geometry

  subroutine rmsd_rotation(mol1, mol2, rot, natom)
    !     Compute the rotation matrix which rotates molecule1 to molecule2
    !     to optimize the RMSD beween the two structures.
    implicit none
    real*8, dimension(3*natom), intent(in) :: mol1, mol2
    real*8, dimension(3,3),intent(out) :: rot
    integer, intent(in) :: natom
!f2py real*8, dimension(3*natom),check(len(mol1)==len(mol2)), intent(in) :: mol2
!f2py integer optional,depend(mol1) :: natom=(len(mol1))/3


    real*8, dimension(3,3) :: cov, vt, u
    real*8, dimension(201) :: work !Optimal lwork previously calculated by dgesvd

    integer :: lwork

    integer :: idx

    integer :: lwkopt, info

    integer :: three
    integer :: one

    real*8, dimension(3) :: s
    real*8, dimension(1) :: dummy

    real*8 :: d

    lwork = 201
    three = 3
    one = 1

    cov = matmul(reshape(mol1, (/3,natom/)), transpose(reshape(mol2, (/3,natom/))))

    call dgesvd('All of u is returned','All of v is returned', three, three, cov, three, s, u, three, vt, three, work, lwork, info)

    if (info /= 0) then
       return
    end if

    ! calculate the single vt * u determinant and redo the rot calculation on inversions

    ! Compute the determinant of the rotation matrices rather than
    ! cov, since numerical instability may produce inversion even when
    ! det(cov) > 0.
    if (det(u) * det(vt) < 0.) then
       vt(3,:) = -vt(3,:)
    end if

    rot = transpose(matmul(u, vt))

    return 
    
  end subroutine rmsd_rotation

  subroutine translate(mol, translation_vector, translated_mol, natom)
    ! Translate the molecule by the specified translation_vector
    implicit none
    real*8, dimension(3*natom), intent(in) :: mol
    real*8, dimension(3), intent(in) :: translation_vector
    real*8, dimension(3*natom), intent(out) :: translated_mol
    integer, intent(in) :: natom
!f2py real*8, dimension(3*natom), intent(in) :: mol
!f2py real*8, dimension(3), intent(in) :: translation_vector
!f2py real*8, dimension(3*natom), intent(out) :: translated_mol
!f2py integer optional, depend(mol) :: natom=(len(mol))/3

    integer :: idx

    do idx=1,natom
       translated_mol(3*(idx-1)+1:3*idx) = mol(3*(idx-1)+1:3*idx) + translation_vector 
    end do

  end subroutine translate

  subroutine flat_rmsd(mol1, mol2, rmsd_result, natom)
    ! Return the unminimized rmsd between the two molecules
    implicit none
    real*8, dimension(3*natom), intent(in) :: mol1, mol2
    real*8, intent(out) :: rmsd_result
    integer, intent(in) :: natom

    real*8, dimension(3*natom) :: delta

    delta = mol1 - mol2

    rmsd_result = sqrt(dot_product(delta, delta)/natom)

  end subroutine flat_rmsd
    

  function trace(mat, n)
    ! compute the trace of the square matrix mat
    implicit none
    real*8 :: trace

    real*8, dimension(n, n) :: mat
    integer :: n

    integer :: idx
    real*8 :: sum

    sum = 0

    do idx=1,n
       sum = sum + mat(idx, idx)
    end do

    trace = sum
    
  end function trace

  subroutine rmsd(mol1, mol2, rmsd_result, natom)
    ! Compute the rotation optimized 2-norm between the two molecules
    implicit none
    real*8, dimension(3*natom), intent(in) :: mol1, mol2
    real*8, intent(out) :: rmsd_result
    integer, intent(in) :: natom
!f2py real*8, dimension(3*natom),check(len(mol1)==len(mol2)), intent(in) :: mol2
!f2py integer optional,depend(mol1) :: natom=(len(mol1))/3    

    real*8, dimension(3) :: cog
    real*8, dimension(3*natom) :: mol1_cog, mol2_cog

    real*8, dimension(3,3) :: rot

    integer :: idx
    integer :: status

    real*8, dimension(3) :: s
    real*8, dimension(1) :: dummy

    integer :: lwork, three, one

    integer :: lwkopt, info

    real*8, dimension(3,3) :: cov, vt, u
    real*8, dimension(201) :: work !Optimal lwork previously calculated by dgesvd

    real*8 :: d



    lwork = 201
    three = 3
    one = 1


    call center_of_geometry(mol1, cog, natom)
    cog = -cog
    call translate(mol1, cog, mol1_cog, natom)

    call center_of_geometry(mol2, cog, natom)
    cog = -cog
    call translate(mol2, cog, mol2_cog, natom)

    cov = matmul(reshape(mol1_cog, (/3,natom/)), transpose(reshape(mol2_cog, (/3,natom/))))

    if (det(cov) < 0.) then
       d = -1.0
    else
       d = 1.0
    end if

    call dgesvd('All of u is returned','All of v is returned', three, three, cov, three, s, u, three, vt, three, work, lwork, info)

    if (d < 0.) then 
       s(3) = d * s(3)
    end if

    rmsd_result = abs((dot_product(mol1_cog, mol1_cog) + dot_product(mol2_cog, mol2_cog) - 2. * sum(s)) / natom)

    if (rmsd_result < 0.) then
       ! Sometimes this is slightly negative due to numerical instability.
       if (abs(rmsd_result) < 1.0e-7) then
          ! If rmsd_result is *very* negative, there is probably
          ! something wrong.  If this is the case, the sqrt below will
          ! cause our final result to be NaN and this problem will not
          ! likely go unnoticed.
          rmsd_result = abs(rmsd_result)
       end if
    end if

    rmsd_result = sqrt(rmsd_result)

  end subroutine rmsd

  subroutine dihedral(x, i1, i2, i3, i4, natom, dihed)
    !
    ! returns dihedral angle, in degrees, for cartesian coordinates of
    ! (a,b,c,d)
    !
    implicit none

    real*8, dimension(3*natom),intent(in) :: x
    integer,intent(in) :: i1, i2, i3, i4, natom
    real*8, intent(out) :: dihed
!f2py real*8, dimension(3*natom), intent(in) :: x
!f2py integer, intent(in) :: x
!f2py integer optional,depend(x) :: natom=(len(x))/3    
!f2py real*8, intent(out) :: dihed

    real*8 :: xa,ya,za
    real*8 :: xb,yb,zb
    real*8 :: xc,yc,zc
    real*8 :: xd,yd,zd

    real*8 :: xba,yba,zba
    real*8 :: xcb,ycb,zcb
    real*8 :: xdc,ydc,zdc
    real*8 :: xt,yt,zt
    real*8 :: xu,yu,zu
    real*8 :: rt2,ru2,rtru
    real*8 :: cosine,sign

    real*8 :: radian
    parameter (radian=57.29577951308232d0)

    xa = x(3 * (i1 - 1) + 1)
    xb = x(3 * (i2 - 1) + 1)
    xc = x(3 * (i3 - 1) + 1)
    xd = x(3 * (i4 - 1) + 1)
    ya = x(3 * (i1 - 1) + 2)
    yb = x(3 * (i2 - 1) + 2)
    yc = x(3 * (i3 - 1) + 2)
    yd = x(3 * (i4 - 1) + 2)
    za = x(3 * (i1 - 1) + 3)
    zb = x(3 * (i2 - 1) + 3)
    zc = x(3 * (i3 - 1) + 3)
    zd = x(3 * (i4 - 1) + 3)

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
    rtru = sqrt(rt2 * ru2)
    if (rtru .ne. 0.0d0) then
       cosine = (xt*xu + yt*yu + zt*zu) / rtru
       cosine = min(1.0d0,max(-1.00d0,cosine))
       dihed = radian * acos(cosine)
       sign = xba*xu + yba*yu + zba*zu
       if (sign .lt. 0.0d0)  dihed = -dihed
    end if

  end subroutine dihedral

  subroutine atom_dist(mol, idx, jdx, dist, natom)
    implicit none
    real*8, dimension(3 *natom), intent(in) :: mol
    integer, intent(in) :: idx, jdx
    real*8, intent(out) :: dist
    integer, intent(in) :: natom
!f2py real*8, dimension(3*natom), intent(in) :: mol
!f2py integer, intent(in) :: idx, jdx
!f2py real*8, intent(out) :: dist
!f2py integer optional, depend(mol) :: natom=(len(mol))/3

    real*8, dimension(3) :: delta

    delta = mol(3*(idx-1)+1:3*idx) - mol(3*(jdx-1)+1:3*jdx)

    dist = sqrt(dot_product(delta, delta))

  end subroutine atom_dist

end module coord_math_mod



