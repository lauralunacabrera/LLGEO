''' Toro 1996 method for randomizing shear wave velocity 

DESCRIPTION:
Toro Method is a first order auto-regressive model used to randomize shear wave
velocity. Note that the functions here are QUITE simplified, because the
interlayer correlation coefficient is assumed constant with depth. Maybe one day 
I'll code everything in, but I just don't have the need for it right now.

The workflow is as follows:

1. We start with a dataframe "all_data" which contains data for shear wave
   velocity profiles. Must have columns ['name', 'depth', 'vs']
2. The data is paired into adjecent layers in the dataframe "paired_data". A 
   maximum threshold is established for two layers to be considered "adjecent"
   (see function: get_paired_data).
3. Interlayer correlation coefficients are calculated for the paired data,
   in the dataframe "IL_corr_coeffs". Here, depth bins may be specified so that
   paired data with a range of "mid_depth" are considered. A minimum number of 
   points (min_pts) may be specified as a requirement to calculate corr coeffs.
   (see function: get_IL_corr_coeffs).
'''

import numpy as np
import pandas as pd

# ------------------------------------------------------------------------------
# Main Functions
# ------------------------------------------------------------------------------
def get_Toro_standrd_corr(site_class):
    # TODO
    pass


def gen_toro_realization(u_lnvs, corr_coeffs, sigma_lnvs):
    ''' TODO - document
    u_lnvs = array of length  n with mean for each layer
    corr_coeff = array of length (n-1) with interlayer correlations
    sigma_lnvs = float with standard deviation
    '''

    Z = np.empty_like(u_lnvs)
    Z[0] = np.random.normal(0, 1)

    for i, rho in enumerate(corr_coeffs):
        epsilon = np.random.normal(0, 1)
        Z[i + 1] = rho * Z[i] + epsilon * (1 - rho**2) ** 0.5
    
    Vs = np.exp(u_lnvs + Z * sigma_lnvs)
    return Z, Vs


def get_IL_corr(all_data:pd.DataFrame , dbin_edges:np.array,
                dintv_max:float = 1, min_pts:float = 10) -> pd.DataFrame:
    ''' Calculates interlayer correlation coefficients for paired data
        
    Purpose
    -------
    Given adjecent Vs measurements and a corresponding mid_depth, this
    calculates the interlayer correlation coefficient in depth bins. 
        
    Parameters
    ----------
    all_data : pandas dataframe
        Dataframe with shear wave velocity profiles to be processed. 
        Must at least have the columns: ['name', 'depth', 'vs']
        where 'name' is used to separate sdata from different tests 
        
    dbin_edges : numpy array
        Depth intervals to be used in the depth bins (edges).
        
    dintv_max : float (defaults to 1)
        Maximum distance between two adjecent layers that is allowed in order
        to considered the measurements a "pair".
            
    min_pts : float (defaults to 10)
        Minimum number of points required to report a correlation coefficient.

    Returns
    -------
    paired_data    : pandas dataframe
        Dataframe with shear wave velocity profiles to be processed. 
        Must at least have the columns: ['name', 'depth', 'vs']
        where 'name' is used to separate data from different tests 
        
    IL_corr_coeffs : pandas dataframe
        Dataframe with reuslts of correlation coefficient and number of points
        for each depth bin. 

    Notes
    -----
    * This is a simplification of Toro's correlation coefficients, since it is
       assumed that the thickness of the layers is constant. This is a fair
       assumption for SCPTs, but may not be the case for other types of tests.

    '''

    # First, get paired data
    paired_data = get_paired_data(all_data, dintv_max)

    # Initalize output dataframe
    out_cols = ['mid_depth', 'IL_corr_coeff', 'num_pts']
    IL_corr_coeffs = pd.DataFrame({}, columns = out_cols)

    # Iterate through the depth bins
    for d_from, d_to in zip(dbin_edges[:-1], dbin_edges[1:]):

        # Get the middle depth of this bin and establish a mask
        mid_depth = (d_from + d_to) / 2
        mask = (paired_data['mid_depth'] >= d_from) & \
               (paired_data['mid_depth'] <  d_to)

        # Get the number of datapoints and paired data
        n = np.sum(mask)
        prev_vs = paired_data.loc[mask, 'prev_vs'].values
        next_vs = paired_data.loc[mask, 'next_vs'].values

        # If there are less than min_pts data points, don't report correlations
        if n < min_pts:
            rho = np.nan

        # Othewise, calculate it (checked by hand and it look good :)
        else: 
            rho = np.corrcoef(np.stack([prev_vs, next_vs], axis = 0))[0,1]

        # Append outputs to correlation coefficient dataframe
        outputs = {'mid_depth': mid_depth, 'IL_corr_coeff':rho, 'num_pts':n}
        IL_corr_coeffs = IL_corr_coeffs.append(outputs, ignore_index = True)

    return paired_data, IL_corr_coeffs

# ------------------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------------------

def get_paired_data(all_data:pd.DataFrame, dintv_max:float = 1) -> pd.DataFrame:
    ''' Creates pairs of adjecent Vs layers for the provided data
        
    Purpose
    -------
    Utility function that pairs data in the dataframe "all_data", which is
    assumed to contain shear wave velocity profiles for many SCPTs or similar
    tests. 

    If two adjecent measurements are farther than "dintv_max" apart, then
    the pair will not be added to the paired data.
        
    Parameters
    ----------
    all_data : pandas dataframe
        Dataframe with shear wave velocity profiles to be processed. 
        Must at least have the columns: ['name', 'depth', 'vs']
        where 'name' is used to separate data from different tests 
        
    dintv_max : float (optional)
        Maximum distance between two adjecent layers that is allowed in order
        to considered the measurements a "pair". Defaults to 1.
        
    Returns
    -------
    paired_data : pandas dataframe
        Dataframe with paired data, with columns:
            'mid_depth': corresponding to the average depth of adjecent layers
            'prev_vs'  : shear wave velocity in shallower layer
            'next_vs'  : shear wave velocity in deeper layer
        
    Notes
    -----
    * Not the most efficient!! Because it iterates through each row in all_data.
      Couldn't figure out a way to do without a loop, and still check that the
      d_intv requirements are met and that we're not comibining different 
      soundings. Might be worth to try again.
    '''

    # Check that the necessary columns exist in df_data
    for req_col in ['name', 'depth', 'vs']: 
        if req_col not in list(all_data):
            raise Exception('df_data is missing column: ' + req_col)
    
    # First, generate depth interval column for all SCPTS (or similar)
    for _, one_cpt_data in all_data.groupby('name'):
        depth = one_cpt_data['depth'].values
        dintv = np.concatenate([[np.nan], depth[1:] - depth[:-1] ], axis = 0)
        all_data.loc[one_cpt_data.index, 'dintv'] = dintv
   
    # Initialize output dataframe
    paired_data = pd.DataFrame({}, columns=['mid_depth', 'prev_vs', 'next_vs'])

    # Iterate through each row in the dataset
    for row_idx, row in all_data.iterrows():

        # If the interval is too long or invalid, skip this pair
        invalid_row = np.isnan(row['dintv']) | (row['dintv'] > dintv_max)
        if invalid_row: continue

        # Otherwise, get paired data
        prev_d = all_data.loc[row_idx - 1, 'depth']
        next_d = all_data.loc[row_idx,     'depth']
        new_row = {'mid_depth' : (prev_d + next_d) / 2,
                   'prev_vs'   : all_data.loc[row_idx - 1, 'vs'],
                   'next_vs'   : all_data.loc[row_idx,     'vs']}

        # Add to output dataframe
        paired_data = paired_data.append(new_row, ignore_index = True)
    
    return paired_data