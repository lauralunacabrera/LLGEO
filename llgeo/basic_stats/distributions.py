''' one_line_description

DESCRIPTION:
Insert a paragraph-long description of the module here.

FUNCTIONS:
This module contains the following (main) functions:
    * fun_name : one_line_description
                 (only add user-facing ones)

'''
import numpy as np
import pandas as pd
import scipy as sp
import scipy.stats as stats

# ------------------------------------------------------------------------------
# Main Functions
# ------------------------------------------------------------------------------
def sample_PMF(num_samples, pmf, x = False):
    ''' Sample from a probability mass function 
        num_samples = number of samples
        x = value of random variable (array same size as pmf)
        pmf = probability mass that X = x (array same size as x)
    '''
    if (x) and (len(x) != len(pmf)):
        raise Exception('x and pmf must be same size')

    if np.sum(pmf) != 1:
        raise Exception('sum of pmf must equal 1')

    if not x:
        x = range(len(pmf))

    sim = np.empty(num_samples)
    U = np.random.uniform(size = num_samples)
    cdf = np.append([0], np.cumsum(pmf)) # CDF starting at zero
    
    for x_val, u_from, u_to in zip(x, cdf[:-1], cdf[1:]):
        mask = (U >= u_from) & (U < u_to)
        sim[mask] = x_val

    if num_samples == 1:
        sim = sim[0]

    return sim


def dist_profile(depth, values, dist = 'norm', intv = 1, min_pts = 10, 
                perc = [0.10, 0.25, 0.50, 0.75, 0.90], depth_lims = False):
    ''' Fits distribution to a profile of values in intervals of width intv.
        
    Purpose
    -------
    Given a profile of values (depth vs. values), this separates them into bins
    of width "intv" and returns the bin number. If there are more than "min_pts"
    in the interval, it fist "dist" (norm or lognorm) to the data, returns mean
    and standard deviation (and log versions if lognorm). It also returns 
    *theoretical* percentiles as required by "perc"
        
    Parameters
    ----------
    depth : array
        depth of measured values (or could be another parameter to use as bin
        criteria)
        
    values : array
        measured values to be fitted to distribution (must be the same length
        as depth).

    dist : str (optional)
        distribution to fit. So far, "norm" or "lognorm". Defaults to "norm".

    intv : float (optional)
        width of the intervals. Defaults to 1.

    min_pts : int (optional)
        minimum number of values required within interval in order to fit a dis-
        tribution. Defaults to 1 m. If num points < min_pts, dataframe values
        are set to np.nan

    perc : list of float (optional)
        list of values of where to return the inverse CDF (percentile values 
        from theoretial distribution). 

    depth_lims : tuple of floats (optional)
        (min_depth, max_depth) to consider in the profile. If not specified,
        defaults to the minimum and maximum in "depth" array.
               
    Returns
    -------
    profile : DataFrame
        Contains distribution parameters and inverse CDF over depth profile.
        
    bin_numbers : array
        Array of size equal to depth and values, which indicates the bin number
        of that measurement. If bin_number = 0, then not enough datapoints were
        available to fit a distribution.
    '''

    # Determine bins for data based on depth and intv
    if not depth_lims: depth_lims = (np.min(depth), np.max(depth))
    bins_e = np.arange(depth_lims[0], depth_lims[1] + intv, intv) # bin edges

    # Initialize output dataframe
    profile = pd.DataFrame([], columns = ['bin', 'from', 'to', 'center'])
    profile['from']   = bins_e[:-1]
    profile['to']     = bins_e[1:]
    profile['center'] = ( bins_e[1:] + bins_e[:-1] ) / 2
 
    # Initialize a guess for mean and stdev to be used in distribution fit
    guess_mean = np.mean(values)
    guess_stdv = np.std(values)

    # Initalize storage of added outputs
    bin_numbers = np.empty(len(depth))

    # Initalize columns for outputs (and check dist is a match)
    if dist == 'norm':
        cols = ['mean', 'stdv']
    elif dist == 'lognorm':
        cols = ['mean_x', 'stdv_x', 'mean_lnx', 'stdv_lnx']
    else:
        raise Exception('dist not recognized. Change to "norm" or "lognorm"')

    cols += ['perc_{:d}'.format(int((100*p))) for p in perc]
    results = np.empty((len(profile), len(cols)))

    # Iterate through profile
    bin_count = 1
    for i, row in profile.iterrows():
        
        # Interval mask: determine which values are in this interval
        imask = (depth >= row['from']) & (depth < row['to'])
       
        # If there are not enough points, return NaN row
        if sum(imask) < min_pts:
            results[i, :] = len(cols) * [np.nan]
            
        # Normal distribution fit
        elif dist == 'norm':
            kwargs = {'loc': guess_mean, 'scale': guess_stdv}
            mean_x, stdv_x = stats.norm.fit(values[imask], **kwargs)
            ppf = stats.norm.ppf(perc, loc = mean_x, scale = stdv_x)
            results[i, :] = np.append(np.array([mean_x, stdv_x]), ppf)
                    
        # Lognormal distribution fit
        elif dist == 'lognorm':
            kwargs = {'floc':0, 'scale':np.exp(guess_mean)}
            stdv_lnx, _, scale = stats.lognorm.fit(values[imask], **kwargs)
            ppf = stats.lognorm.ppf(perc, s = stdv_lnx, scale = scale)
            mean_lnx = np.log(scale)
            mean_x,stdv_x = lognorm_to_norm(mean_lnx, stdv_lnx)
            results[i, :] = np.append(np.array([mean_x, stdv_x,
                                                mean_lnx, stdv_lnx]), ppf) 

        # Determine bin number
        if sum(imask) < min_pts:
            bin_numbers[imask] = 0
            profile.loc[i, 'bin'] = 0
        else:
            bin_numbers[imask] = bin_count
            profile.loc[i, 'bin'] = bin_count
            bin_count += 1
    
    # Add results to profile dataframe (final output)
    profile.loc[:, cols] = results
    profile['COV'] = profile['stdv_x'] / profile['mean_x']
    
    return profile, bin_numbers

    
def lognorm_MME(x):
    ''' Returns the method of moments estimators for lognormal distribution'''
    mean_lnx = - np.log(sum(x**2))/2 +2*np.log(sum(x))-3/2*np.log(len(x))
    var_lnx = np.log(sum(x**2)) - 2*np.log(sum(x))+np.log(len(x))
    stdv_lnx = var_lnx **.5
    return(mean_lnx,stdv_lnx)


def lognorm_MLE(x):
    ''' Returns the maximum likelihood estimators for lognormal distribution'''
    ln_x = np.log(x)
    mean_lnx = np.mean(ln_x)
    squared = (ln_x - mean_lnx) ** 2
    var_lnx = sum(squared)/(len(squared)-0)
    stdv_lnx = var_lnx ** .5
    return(mean_lnx,stdv_lnx)


def py_lognorm_MLE(x):
    ''' Returns the maximum likelihood estimators for lognormal distribution, 
        using the generalized apprach implemented in Scipy
        (allows for location shift)'''
    # If we pass floc=0 in fit, this gives MLE paramters
    shape,loc,scale = stats.lognorm.fit(x,loc=0)   
    mean_x, var_x = stats.lognorm.stats(shape,loc,scale,moments='mv')
    mean_x   = float(mean_x)
    mean_lnx, stdv_lnx = norm_to_lognorm(mean_x, var_x ** 0.5)
    return(mean_lnx,stdv_lnx)


def lognorm_to_norm(mean_lnx,stdv_lnx):
    '''Transforms lognormal estimators back to original units'''
    var_lnx = stdv_lnx**2
    mean_x = np.exp(mean_lnx+0.5*var_lnx)
    var_x = mean_x**2*(np.exp(var_lnx)-1)
    stdv_x = var_x**.5
    return(mean_x,stdv_x)

def norm_to_lognorm(mean_x, stdv_x):
    ''' Transforms estimators to lognormal estimators '''

    var_x   = stdv_x ** 2
    var_lnx = np.log(1+var_x/(mean_x)**2)
    mean_lnx = np.log(mean_x)-0.5*var_lnx
    stdv_lnx = var_lnx**.5
    return mean_lnx, stdv_lnx

def get_all_fits(data):
    '''Gets lognormal fit for data (numpy array) using all methods,
       returns df'''
    # Get parameters using all methods and combine into array
    log_MME   = np.array(lognorm_MME(data))
    log_MLE   = np.array(lognorm_MLE(data))
    log_pyMLE = np.array(py_lognorm_MLE(data))
    MME       = np.array(lognorm_to_norm(log_MME[0],log_MME[1]))
    MLE       = np.array(lognorm_to_norm(log_MLE[0],log_MLE[1]))
    pyMLE     = np.array(lognorm_to_norm(log_pyMLE[0],log_pyMLE[1]))
    fits      = np.stack([MME,log_MME,MLE,log_MLE,pyMLE,log_pyMLE],axis=0)
    fits      = fits.flatten()

    cols = [m+'_'+p for m in ['MME','MLE','pyMLE']
           for p in ['mu','std','mu_lnx','stdv_lnx']] 
    fits_dict = {col: [val] for (col,val) in zip(cols,fits)}
    fits_df = pd.DataFrame.from_dict(fits_dict)
    return(fits_df)

def lognorm_args(mean_lnx, stdv_lnx, logparams = True):
    ''' Returns arguments to pass to scipy's lognorm function the traditional
        way that the lognormal distribution is fit'''

    if not logparams:
        mean_lnx, stdv_lnx = norm_to_lognorm(mean_lnx, stdv_lnx)

    args = {'s': stdv_lnx, 'loc':0, 'scale': np.exp(mean_lnx)}
    return args
