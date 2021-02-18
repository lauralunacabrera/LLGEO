''' Estimation of correlation structure from observed processes

DESCRIPTION:
This module contains functions related to the estimation of correlation stucture
from geotechnical data.

TODO: - add proper references to dr. fenton's books including formulas

'''

import numpy as np
import pandas as pd
import scipy.optimize as op

# ------------------------------------------------------------------------------
# Functions for Single Process with Equispaced Data
# ------------------------------------------------------------------------------

def corr_fun_equisp(data, mean, std):
    ''' Calculates correlation function given equispaced data, mean, and std.
        
    Purpose
    -------
    This function calculates the correlation coefficient as a function of
    separation (lag) for datapoints provided in "data", assuming a mean
    of "mean" and standard deviation of "std".

    IMPORTANT: THIS FUNCTION ASSUMES EQUISPACED DATA

    Parameters
    ----------
    data : numpy array
        Observations to be used in calculations
        
    mean : float
        mean to use in calculations (usually mean(data))
        
    std : float
        standard deviation to be used in calculations (usually std(data))
    
    Returns
    -------
    lag : numpy array
        Set of lag distances (traditionally labelled tau)
        
    rho : numpy array
        Set of correlation coefficients corresponding to lag (traditionally 
        labelled as rho)
        
    nonavg_rho : numpy array
        Correlation coefficients without dividing by the number of samples (n-j)
    
    '''

    # Determine lag
    n     = len(data)
    lag   = np.arange(0, n)
    
    # Calculate correlation coefficients (see Fenton's notes)
    R     = data.reshape(n, 1) - mean
    M     = R * R.T / std**2
    rho   = np.array([np.sum(np.diag(M, k = j)) / (n-j) for j in range(0, n)])
    
    # For debugging mostly... (or messing around)
    nonavg_rho = np.array([np.sum(np.diag(M, k = j)) for j in range(0, n)])
    
    return(lag, rho, nonavg_rho)


# ------------------------------------------------------------------------------
# Functions for Single Process with Non-Equispaced Data
# ------------------------------------------------------------------------------

def corr_coeffs_1D(x, y):
    ''' Correlation coefficients between observations "y" at 1D coordinate "x" 
        
    Purpose
    -------
    This returns correlation coefficient values for all possible pairs of values
    in "y". It assumes that this is a 1D process where location is indicated by
    the corresponding value in "x".

    This is mostly used as a middle step in getting the correlation function
    for non-equispaced data. If your data is equispaced, it makes more sense
    to use "corr_fun_equispaced" directly.

    If your data is non-equispaced, use this function then feed the results to
    the function "corr_fun_nonequispaced".

    Parameters
    ----------
    x : numpy array
        Location of observation (1D coordinate, typically depth).
        
    y : numpy array
        Measured values to be used in calculating correlation coefficient.
        
    Returns
    -------
    dist : numpy array
        Separation distance between observations for which rho was calculated.
        
    corr : numpy array
        Correlation coefficient between observations.
        
    '''

    # Make sure x and y are the same size
    if len(x) != len(y):
        raise Exception('X and Y must have the same length.')

    # Get basic parameters
    n = len(x)
    miu = np.mean(y)
    std = np.std(y, ddof = 1)

    # Get distance matrix and all possible ij pairs
    dist_matrix = np.abs(x.reshape(n, 1) - x.reshape(1, n))
    ij_pairs = [(i, j) for i in range(n) for j in np.arange(i, n)]

    # Get distance and correlation vectors
    dist, corr = [], []
    for (i, j) in ij_pairs:
        dist += [ dist_matrix [i, j]]
        corr += [ (y[i] - miu) * (y[j] - miu) / (std ** 2) ]

    # Return as np arrays
    dist = np.array(dist)
    corr = np.array(corr)

    return dist, corr


def corr_fun_nonequisp(sep_dist, corr_coeff, intv, min_pts):
    ''' Determines the correlation function for non-equisapced correlation coeff
        
    Purpose
    -------
    This takes in pairs of separation distance vs. correlation coefficient calc-
    culated from data that is not necessarily equispaced (see corr_coeffs_1D)
    and returns the estimated correlation function in separation distance
    intervals ("intv") wherever there are more than "min_pts" available.
            
    Parameters
    ----------
    sep_dist : numpy array
        Separation distance between the calculated correlation coefficients.
        
    corr_coeff : numpy array
        Calculated correlation coefficient at a given sep_dist
        
    intv : float
        Separation distance interval to use in estimating the correlation func-
        tion. Note that this will target n * intv as the centers: 
            For example if intv=1 is given, then estimates will be returned for:
                (0 to 0.5), (0.5 to 1.5), (1.5 to 2.5), etc...
            That is:
                (0 to 1/2*intv), (1/2*intv to 3/2*intv), (3/2*intv to 5/2*intv) 
                up to (x/x*intv to (x/x + 1/2) * intv)

    min_pts : int
        The minimum number of points required to return an estimate of the
        correlation function. If there are less than min_pts at a given
        separation distance, a NaN row is returned.   

    Returns
    -------
    corr_fun : dataframe
        Contains the results of the estimated correlation function. 
        Has columns: [dist_from, dist_to, dist_mid, num_pts, mean, stdv]
    '''

    # Make sure that inputs are numpy arrays, otherwise this fails
    # (Added because it is a common erorr to pass list or pd series)
    if type(sep_dist) is not np.ndarray:
        mssg = 'Error in corr_fun_nonequisp... sep_dist must be np array!\n'
        mssg += '   Instead, it is: ' + str(type(sep_dist))
        raise Exception(mssg)
    if type(corr_coeff) is not np.ndarray:
        mssg = 'Error in corr_fun_nonequisp... corr_coeff must be np array!\n'
        mssg += '   Instead, it is: ' + str(type(corr_coeff))
        raise Exception(mssg)

    # Initalize output
    corr_fun = []

    # Get separation distance bins in which to calculate correlation func.
    centers = np.arange(0, np.max(sep_dist) + intv, intv) # Target loc of bins
    edges = ( centers[:-1] + centers[1:] ) / 2 # Edges of bins in between center
    edges = np.append([0], edges) # Add zero at the beginning
    edges = np.append(edges, [ edges[-1] + intv/2 ]) # Add half interval at end

    # Iterate through each separtion distance "bin"
    for d_from, d_to in zip(edges[:-1], edges[1:]):

        # Determine center of interval
        d_center = np.average([d_from, d_to])

        # Determine which values are within this distance "bin"
        mask = (sep_dist >= d_from) & (sep_dist < d_to)
        binned_coeff = corr_coeff[mask]

        # Determine number of datapoints within this "bin"
        n = np.sum(mask)

        # If there are less points that required, return NaNs
        if n <= min_pts:
            corr_fun += [ [d_from, d_to, d_center, n, np.nan, np.nan] ]

        # Otherwise, return correlation function parameters
        else:
            mean = np.average(binned_coeff) # Talk to Fenton
            stdv = np.std(binned_coeff, ddof = 1)
            corr_fun += [ [d_from, d_to, d_center, n, mean, stdv] ]

    # Turn result into a pandas dataframe to make columns more clear
    cols = ['dist_from', 'dist_to', 'dist_mid', 'num_pts', 'corr_fun', 'stdv']
    corr_fun = pd.DataFrame(corr_fun, columns = cols)
    
    return corr_fun


# ------------------------------------------------------------------------------
# Functions for Many Processes
# ------------------------------------------------------------------------------

def many_corr_fun_nonequisp(df, xcol, ycol, icol, fun_opts = {}):
    ''' Estim. of correl. coeffs. and funct. for *many* nonequispaced processes
        
    Purpose
    -------
    This is a *wrapper* function that takes in many observed processes with non-
    equispaced data and returns estimates of the correlation coefficients and
    correlation function.

    THIS IS DESIGNED ONLY FOR A 1D PROCESSES WITH 1 COORDINATE (typ. depth)
    
    It returns a dataframe of correlation coefficients, a df of "local" corre-
    lation function (separate correlation function per observed process), and a
    "global" correlation function that combines all the correlation coefficients
    regardless of which "process" they initially came from. (Careful with this!!
    The underlying assumption is that all observed processes have the same
    correlation structure. The applicability of that assumption is left up to
    the user.)

    Parameters
    ----------
    df : dataframe
        Contains observed processes to be used in estimating correlation coeffs
        and function. Must at a minimum contain columns:
            [xcol, ycol, id_col]
        
    xcol : str
        Name of the column in df that corresponds to the location of the ob-
        servation (typicall depth).

    ycol : str
        Name of the column in df that corresponds to the measured values of the
        process

    icol : str
        Name of the column in df that corresponds to the name (or identifier) of
        the test (for example: cpt_name where values are SCPT19-01, etc..)

    func_opts : dict (optional)
        Contains keyword arguments to be passed to "corr_fun_nonequisp", which
        estimates the correlation funciton from correlation coefficients.
        It defaults to: {'intv' : 1, 'min_pts' : 10}
        
    Returns
    -------
    corr_coeffs : dataframe
        Calcualted correlation coefficient calcualted separately for each
        observed process and then concatenated together. Columns are:
            [icol, sep_dist, corr_coeff] 
        
    local_funs : dataframe
        Estimated correlation function calculated separately for each observed
        process and then concatenated together.

    global_fun : dataframe
        Estimated correlation function calculated based on corr_coeffs, but 
        assuming these are all part of the same random process with the same
        correlation structure. CAREFUL: the applicability of this assumption
        is left up to the user. 
        
    Notes
    -----
    * This isn't the traditional way of doing this, but... ¯|_(ツ)_|¯
    '''
    
    # Initalize outputs
    corr_coeffs = []
    local_funs = []

    # Update to user-defined options for correlation function
    opts = {'intv' : 1, 'min_pts' : 10}
    opts.update(fun_opts)

    # Iterate through grouped dataframes
    for id, data in df.groupby(icol):

        # Get correlation coefficients
        kwargs = {'x' : data[xcol].values.astype(float),
                  'y' : data[ycol].values.astype(float) }       
        dist_array, coeff_array = corr_coeffs_1D(**kwargs)

        # Summarize correlation coefficient results in dataframe
        coeff = pd.DataFrame({icol : [id] * len(coeff_array),
                              'sep_dist' : dist_array,
                              'corr_coeff' : coeff_array, })

        # Get the correlation function
        fun = corr_fun_nonequisp(dist_array, coeff_array, **opts)
        fun[icol]  = [id] * len(fun)

        # Append to outputs
        corr_coeffs += [ coeff ]
        local_funs += [ fun ]

    # Concatenate results into output dataframes
    corr_coeffs = pd.concat(corr_coeffs, axis = 0, ignore_index = True)
    local_funs  = pd.concat(local_funs,  axis = 0, ignore_index = True)

    # Estimate a "global" correlation function
    glob_fun = corr_fun_nonequisp(corr_coeffs['sep_dist'].values, 
                                  corr_coeffs['corr_coeff'].values, **opts)
                
    return corr_coeffs, local_funs, glob_fun


# ------------------------------------------------------------------------------
# Theoretical Correlation Functions
# ------------------------------------------------------------------------------

def markov_fun(tau, rho,  theta_guess):
    ''' One-line description of the function
        
    Purpose
    -------
    Paragraph-long description of function purpose
    State assumptions and limitations. Examples are great.
        
    Parameters
    ----------
    param_name : param_data_type (optional?)
        Description of the parameter.
        Include assumptions, defaults, and limitations!
        
    param_name : param_data_type (optional?)
        Description of the parameter.
        Include assumptions, defaults, and limitations!
        
    Returns
    -------
    output_name : output_data_type
        Description of the parameter.
        Include assumptions, defaults, and limitations!
        
    output_name : output_data_type
        Description of the parameter.
        Include assumptions, defaults, and limitations!
        
    Notes
    -----
    * Anything the user should know?
        
    Refs
    ----
    * Include *VERY DETAILED* bibliography. 
      State publications, urls, pages, equations, etc.
      YOU'RE. AN. ENGINEER. NOT. A. CODER.
    '''

    # Get line of mest fit
    res = lambda theta: rho - np.exp(-2 * tau / theta)
    markov_fit = op.least_squares(res, theta_guess)
    theta = markov_fit.x[0]
    markov = rho - markov_fit.fun

    return(theta, markov)
