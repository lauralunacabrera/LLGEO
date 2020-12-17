''' Darendeli Non-linear Properties for Equivalent-Linear Ground Response Analyses

DESCRIPTION:
This module contains functions related to the non-linear dynamic properties of
soils, specifically geared towards use in equivalent-linear ground response 
analyses. The curves specified by Darendeli (2001) are coded here and can
be used for a variety of applications.

FUNCTIONS:
This module contains the following functions:
    * params: calculates parameters for Darendeli curves, based on soil props
    * curves: returns Darendeli curves, based on calcualted params

TODOS:
    * Review documentations cause i switched things around when I added
      darem_params
'''
# ------------------------------------------------------------------------------
# Import Modules
# ------------------------------------------------------------------------------
import numpy as np


# ------------------------------------------------------------------------------
# Main Functions
# ------------------------------------------------------------------------------
def params(PI, OCR, sigp_o, N = 10, load_freq = 1, type = 'mean'):
    ''' Calculates parameters for Darendeli curves, based on soil properties

    Purpose
    -------
    Given the set of soil properties, calculates the parameters needed to obtain
    mean modulus reduction and damping curves according to Darendeli (2011).

    Parameters
    -----------
    PI (%) : float
        Soil Plasticity Index
    OCR (-) : float
        Overconsolidation Ratio
    sigp_o (atm) : float
        In-situ mean effective confining stress (sigma'o)
    N (-) : float, optional
        Number of loading cycles. Not critical, defaults to 10 cycles.
    load_freq (Hz) : float, optional
        Loading frequency. Not critical, defaults to 1 Hz.
    type 

    Returns
    -------
    a (-) : float
        Curvature coefficient (set as constant Phi_5)
    b (-) : float
        Scaling coefficient on material damping curve 
    D_min (dec) : float
        Small strain damping. Ignores effect of high-amplitude cycling on Dmin
        (see Section 6.3 and Pg 144 in Ref_1)
    sstrn_r (dec) : float
        Reference strain, corresponds to the strain amplitude when shear modulus
        reduced to one half of Gmax (key characteristic of the hyperbolic model
        employed in Darendeli's research). See Section 6.2, Pg. 132 in Ref_1.


    Note
    ----
    * This is done separately to explore the dependence of the model parameters
      on the soil properties.

    References
    ----------
    (1) Darendeli, M. B. (2001). Development of a New Family of
        Normalized Modulus Reduction and Material Damping Curves. 393.

        See : Section 7.4.1 Page 172, in Ref(1) 
              Table 8.12, Page 214, in Ref(1)
    '''
    # Phi constants (1-indexed to match equation notations)
    # These are calibrated to all credible data from Darendeli
    if type == 'mean':
        phis = [np.nan, 0.0352, 0.0010, 0.3246, 0.3483, 0.9190, 0.8005, 0.0129, 
                -0.1069, -0.2889, 0.2919, 0.6329, -0.0057]

    # Curvature coefficient (Eq. 7.26b)
    a = phis[5]

    # Scaling coefficient (Eq. 7.28b)
    b = phis[11] + phis[12] * np.log(N)

    # Minimum damping (Eq. 7.28a)
    D_min = (phis[6] + phis[7] * PI * OCR ** phis[8]) * sigp_o ** phis[9] *   \
            (1 + phis[10] * np.log(load_freq))

    # Reference strain (gamma_r in equations) (Eq. 7.26a)
    sstrn_r = (phis[1] + phis[2] * PI * OCR ** phis[3]) * sigp_o ** phis[4]

    return(a, b, D_min, sstrn_r)


def curves(sstrn, a, b, D_min, sstrn_r):
    ''' Mean modulus reduction and damping curves

    Purpose
    -------
    Generate mean modulus reduction and material damping curves for a given set
    of material properties, following Darendeli(2011). Uses the results that
    were calibrated to all the collected data, as recommended by author.
        
    Parameters
    -----------
    sstrn (dec) : array
        Shearing strains of interest (in decimal, not %)
        Any numpy array will work, but should probably be log-spaced!
    a (-) : float
        Curvature coefficient (set as constant Phi_5)
    b (-) : float
        Scaling coefficient on material damping curve 
    D_min (dec) : float
        Small strain damping. Ignores effect of high-amplitude cycling on Dmin
        (see Section 6.3 and Pg 144 in Ref_1)
    sstrn_r (dec) : float
        Reference strain, corresponds to the strain amplitude when shear modulus
        reduced to one half of Gmax (key characteristic of the hyperbolic model
        employed in Darendeli's research). See Section 6.2, Pg. 132 in Ref_1.

    Returns
    -------
    G_red (dec) : array
        MEAN modulus reduction curve for material properties.
        Each value corresponds to shear strain levels given by sstrn
    D_adj (dec) : array
        MEAN damping curve for given properties.
        Each value corresponds to shear strain levels given by sstrn

    Notes
    -----
    * Be careful about providing mean effective confining pressure in atm!

    Refs
    ----
    (1) Darendeli, M. B. (2001). Development of a New Family of
        Normalized Modulus Reduction and Material Damping Curves. 393.
        
        See : Section 7.4.1 Page 172, in Ref(1) 
              Table 8.12, Page 214, in Ref(1)

    '''

    # Normalized modulus reduction curve (Eq. 7.25)
    G_red = 1 / (1 + (sstrn / sstrn_r)**a)

    # Damping constants (Eq. 7.27) ~ one-indexed
    c = [np.nan, -1.1143 * a ** 2 + 1.8618 * a + 0.2523,
                 +0.0805 * a ** 2 - 0.0710 * a - 0.0095, 
                 -0.0005 * a ** 2 + 0.0002 * a + 0.0003 ]

    # Masing damping (Eq. 7.27)
    D_mas_a1 = 1 / np.pi *   \
               (4 * (sstrn - sstrn_r * np.log((sstrn + sstrn_r) / sstrn_r)) /  \
               (sstrn**2 / (sstrn + sstrn_r)) - 2)

    D_mas = c[1] * D_mas_a1 + c[2] * D_mas_a1**2 + c[3] * D_mas_a1**3


    # Adjuted damping (final one!)  (Eq. 7.27)
    # Note that notation is a bit different in Pg. 214 and 174
    D_adjs = b * G_red**0.1 * D_mas + D_min

    return(G_red, D_adjs)

# ------------------------------------------------------------------------------
# Helper Functions - nothing to see here :)
# ------------------------------------------------------------------------------
