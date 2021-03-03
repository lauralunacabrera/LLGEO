''' Generate 1D and 2D random fields using Local Average Subdivision

DESCRIPTION:
This module contains functions to generate 1D and 2D random fields using the 
Local Average Subdivision Method. The functions here don't do much: the actual
LAS method was coded in Fortran 77 and compiled into a dynamic library. Then,
an interface to python was created using numpy's F2PY module. The result of this
process is an extension module (simLAS.cpython ... .so) that is called here.

MAIN FUNCTIONS:
This module contains the following functions:
    * simLAS1D: generates 1D realizations of a random field using LAS
    * simLAS2D: generates 2D realizations of a random field using LAS
    * plot_rf : given a random field array and axes handles, returns a plot

TODO - simLAS2d: automate finding K1, K2,  m, OR just request these directly
'''

# ------------------------------------------------------------------------------
# Import Modules
# ------------------------------------------------------------------------------
# import sys
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from F77_to_py import simLAS as LAS # pylint: disable=import-error
import numpy as np

# ------------------------------------------------------------------------------
# Main functions
# ------------------------------------------------------------------------------

def sim1d(n, xl, zm, zv, thx, fncnam, pa, pb, nsims, kseed):
    ''' Generates 1D realizations of a random field using LAS.
    
    Purpose
    -------
    Generates nsims of a random field using Local Average Subdivision method, 
    according to the provided parameters. This function assumes a normally 
    distributed random process. The wrapped subroutine is sim1d.f, which calls
    onto the Fortran 77 library GAF77.so (must be dynamically compiled).
    
    Only programmed for non-conditional 1D random fields!

    Parameters
    ----------
    n : int (integer)
        Number of cells to discretize the field. Note that the field resolution
        given by n must be such that N = k1*2**m where k1 is a positive integer
        in the range [1, 16] and m is an integer in the range [0, 16]. Thus, the
        largest value of n is 1,048,576 although it must also be less than MXN.
        An error message will be issued if n doesn't satisfy the above equation.
        
    xl : float (real*4)
        Physical dimensions of the random process. Careful with units!

    zm : float (real*8)
        Mean of the random process, which is assumed to be normally distributed.

    zv : float (real*8)
        Point variance of the random process. NOT STANDARD DEVIATION!!
         
    thx : float (real*8)
        Scale of fluctuation of the random process (correlation length).

    fncnam : str (char*6)
        Name of the variance function. Must be one of:
        (*** I generally use dlavx1)

            'dlace1' -> 1D Damped oscillatory noise process
            'dlafr1' -> 1D Fractional Gaussian noise model.
                        Requires (H, delta) where H is thx and
                        delta is the cell dimension.
            'dlavx1' -> 1D Exponentially decaying (Markov) model.
                        Requires scale of fluctuaction. ***
            'dlsmp1' -> 1D Simple polynomial decaying covariance.
            'dlspx1' -> 1D Gaussian decaying correlation model.
                        requires scale of fluctuation.

    pa : float (real*8)
       Typically the point variance of the random process. The 
       first additional parameter for the covariance function.
 
    pb : float (real*8)
       Typically not used, unless covariance function requires two
       parameters (it's the second additional parameter).

    nsims : int (integer)
        Number of realizations to return.

    kseed : int (integer)
       Integer seed to be used to initialize the pseudo-random 
       number generator. If kseed = 0, then a random seed will be used.

    Returns
    -------
    Zs : list of numpy arrays
        List with nsims elements, where each element corresponds to a random
        field realization. Each realization is a 1D numpy array of length n.
        
    Notes
    -----

    References
    ----------
    (1) Fenton & Griffiths (2008). Risk assessment in geotechnical engineering.
        John Wiley & Sons, Inc.
            See: All of chapter 3
    '''
    # Create random field realizations using sim1d (see F77_to_PY folder)
    Zs = [LAS.sim1d(n, xl, zm, zv, thx, fncnam, pa, pb, kseed, 7, i+1)
           for i in range(nsims)]

    # Only return the first n elements (all else is workspace)
    Zs = [z[:n] for z in Zs]

    return Zs


def sim2d(n1, n2, xl, yl, zm, zv, thx, thy, fnc, pa, pb, nsims, outf, seed):
    ''' Generates 2D realizations of a random field using LAS.
    
    Purpose
    -------
    Generates nsims of a random field using Local Average Subdivision method, 
    according to the provided parameters. This function assumes a normally 
    distributed random process. The wrapped subroutine is sim2d.f, which calls
    onto the Fortran 77 library GAF77.so (must be dynamically compiled).

    Only programmed for non-conditional 2D random fields!
    
    Parameters
    ----------
    n1 and n2 : int (integer)
        Number of cells to discretize the field in x and y dirs, respectively.
        Both N1 and N2 must be such that N1 = k1*2**m and N2 = k2*2**m,
        where m is common to both and k1 and k2 are integers satisfying the exp.
        k1 x k2 <= MXK. Generally, k1 and k2 are chosen to be as large as 
        possible while still satisfying the above requirement. Note that N1 and
        N2 cannot be chosen arbitrarily - it is usually best to choose m first
        then k1 and k2 as to satisfy or exceed problem requirements. 
        
    xl and yl: float (real*4)
        Physical dimensions of the random process. Careful with units!

    zm : float (real*8)
        Mean of the random process, which is assumed to be normally distributed.

    zv : float (real*8)
        Point variance of the random process. NOT STANDARD DEVIATION!!
         
    thx and thy: float (real*8)
        Scales of fluctuation of the random process (correlation length).

    fnc : str (char*6)
        Name of the variance function. Must be one of:
        (*** I generally use dlavx2)

            'dlavx2' -> 2D Exponentially decaying (Markov) model.
                        Requires scale of fluctuaction. ***
            'dlspx5' -> 2D Gaussian decaying correlation model.
                        Requires scale of fluctuation.

    pa : float (real*8)
       Typically the point variance of the random process. The 
       first additional parameter for the covariance function.
 
    pb : float (real*8)
       Typically not used, unless covariance function requires two
       parameters. The second additional parameter for the covariance function.

    nsims : int (integer)
        Number of realizations to return.

    outf : str (char*12)
        Name of file onto which debugging info will be printed (12 char max).

    seed : int (integer)
       Integer seed to be used to initialize the pseudo-random 
       number generator. If kseed = 0, then a random seed will be used.

    iout (input)
       Unit number onto which progress, error, and warning messages are logged.


    Returns
    -------
    Zs : list of numpy arrays
        List with nsims elements, where each element corresponds to a random
        field realization. Each realization is a 2D numpy array of size n1xn2.
        Z(1,1) is the lower left cell, Z(2,1) is the next cell in the X direct.,
        Z(1,2) is the next cell in the Y direction (upwards).
        
    References
    ----------
    (1) Fenton & Griffiths (2008). Risk assessment in geotechnical engineering.
        John Wiley & Sons, Inc.
            See: All of chapter 3
    '''
    # Create random field realizations using sim1d (see F77_to_PY folder)
    Zs = [LAS.sim2d(n1, n2, xl, yl, zm, zv, thx, thy, fnc, pa, pb, seed, outf,
                    i+1) for i in range(nsims)]

    # Only return the first n elements (all else is workspace)
    Zs = [z[0:n1*n2].reshape(n1, n2, order = 'F') for z in Zs]

    return(Zs)


def plot_rf(ax, z):
    ''' given a random field array and axes handles, returns a plot '''

    ax.imshow(z.T, origin = 'lower')

    return(ax)
