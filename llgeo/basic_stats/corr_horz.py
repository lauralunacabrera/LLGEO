''' one_line_description

DESCRIPTION:
Insert a paragraph-long description of the module here.

'''

import numpy as np
import pandas as pd


# ------------------------------------------------------------------------------
# Main Functions
# ------------------------------------------------------------------------------

def estimate_horz_corr(data, col_dict, bins_depth, bins_dist, bins_angl, min_pts):

    # Reanme data columns
    data.rename(col_dict, axis = 1, inplace = True)

    # Get distance and angle matrices
    dist_matrix, angl_matrix = get_dist_and_angl(data)

    # Get all possible pairings of available tests
    pairs = get_pairings(data, dist_matrix, angl_matrix)
    
    # Make sure that data is in equal intervals of depth
    resampled, mean, stdv = resample_data(data, bins_depth)

    # Calculate correlation coefficients for all test pairs
    all_corr_coeffs = calc_coeffs(pairs, resampled, min_pts, mean, stdv)

    # Calculate average correleation as a function of distance and angle
    corr_vs_dist = get_corr_vs_dist(all_corr_coeffs, bins_dist, 'dist')
    corr_vs_angl = get_corr_vs_dist(all_corr_coeffs, bins_angl, 'angl')

    # Organize results for output
    results = {'dist_matrix'     : dist_matrix,
               'angl_matrix'     : angl_matrix,
               'resampled_data'  : resampled,
               'all_corr_coeffs' : all_corr_coeffs,
               'corr_vs_dist'    : corr_vs_dist,
               'corr_vs_angl'    : corr_vs_angl}

    return results


# ------------------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------------------

def get_dist_and_angl(data):

    # Get unique names and coordinates 
    unique_data_loc = data.drop_duplicates(subset = ['name', 'x', 'y'])
    Ns = unique_data_loc['name'].values
    Xs = unique_data_loc['x'].values.reshape(-1, 1)
    Ys = unique_data_loc['y'].values.reshape(-1, 1)

    # Calculate difference matrices
    x_deltas = Xs*np.ones(np.shape(Xs.T)) - np.ones(np.shape(Xs))*Xs.T
    y_deltas = Ys*np.ones(np.shape(Ys.T)) - np.ones(np.shape(Ys))*Ys.T

    # Determine distance and angle matrices
    dists = np.sqrt(x_deltas**2 + y_deltas**2)
    angl  = np.arctan2(y_deltas, x_deltas)
    angl[angl<0] = angl[angl<0] + np.pi # Orientation fix

    # Organize into dataframes
    dist_matrix = pd.DataFrame(dists, columns = Ns, index = Ns)
    angl_matrix = pd.DataFrame(angl,  columns = Ns, index = Ns)

    return dist_matrix, angl_matrix


def get_pairings(data, dist_matrix, angl_matrix):

    # Get all possible combinations of CPTs
    names = np.unique(data['name'])
    pairs = []

    for i, one_name in enumerate(names):

        pairB = np.array(names[i:])
        pairA = np.array([one_name] * len(pairB))

        dist  = [float(dist_matrix.loc[A, B]) for A, B  in zip(pairA, pairB)] 
        angl  = [float(angl_matrix.loc[A, B]) for A, B  in zip(pairA, pairB)]

        pairs += [np.stack([pairA, pairB, dist, angl], axis = 1)]

    pairs = np.concatenate(pairs, axis=0)
    pairs = pd.DataFrame(pairs, columns=['A','B','dist','angl'])

    return pairs


def resample_data(all_data, dbin_edges):

    # Create depth bins

    resampled = pd.DataFrame({'d_from': dbin_edges[:-1],
                              'd_to'  : dbin_edges[1:],
                              'd_mid' : (dbin_edges[:-1] + dbin_edges[1:]) / 2})

    # Get the mean and standard deviation for each depth bin
    for (i, row) in resampled.iterrows():

        # Get location of values within this depth bin
        mask = (all_data['d'] >= row['d_from']) & (all_data['d'] < row['d_to'])

        # Calculate mean and standard deviation
        resampled.loc[i, 'mean'] = np.mean(all_data.loc[mask, 'v'])
        resampled.loc[i, 'stdv'] =  np.std(all_data.loc[mask, 'v'], ddof = 1)

        for name, data in all_data.groupby('name'):
            mask = (data['d'] >= row['d_from']) & (data['d'] < row['d_to'])

            if np.sum(mask) > 1:
                mssg = 'Uh oh: '+str(name)+' has '+str(np.sum(mask))+' pts at '
                mssg+= '{:2.1f} - {:2.1f} m'.format(row['d_from'], row['d_to'])
                print(mssg)

            resampled.loc[i, name] = np.average(data.loc[mask, 'v'])

    # Get global mean and global standard deviation
    exclude_cols = ['d_from', 'd_to', 'd_mid', 'mean', 'stdv']
    cols = [c for c in list(resampled) if c not in exclude_cols]
    all_data = resampled.loc[:, cols].dropna().values
    glob_mean = np.mean(all_data.flatten())
    glob_stdv = np.std(all_data.flatten(), ddof = 1)

    return resampled, glob_mean, glob_stdv


def calc_coeffs(pairs, resampled, min_pts, glob_mean = None, glob_stdv = None):
    
    # Initialize output
    all_corr_coeffs = pairs.copy()

    # Calculate correlation coefficient between all test pairs
    for pair_idx, pair_row in pairs.iterrows():

        # Print progress
        if (pair_idx) % 500 == 0:
            print('{:4.2f}%'.format(100*(pair_idx+1)/len(pairs)))

        # Extract names
        nameA, nameB = pair_row['A'], pair_row['B']
    
        # Extract available data for this pair
        pair_data = resampled.loc[:, ['mean', 'stdv', nameA, nameB]]
        pair_data.dropna(inplace = True)
        num_pts = len(pair_data)

        if num_pts > min_pts:

            if nameA == nameB:
                vA = pair_data[nameA].values[:, 0]
                vB = pair_data[nameB].values[:, 1]
            else:
                vA = pair_data[nameA].values 
                vB = pair_data[nameB].values

            # if glob_mean is None:
            #     mean = pair_data['mean'].values
            # else:
            #     mean = glob_mean
            
            # if glob_stdv is None:
            #     stdv = pair_data['stdv'].values
            # else:
            #     stdv = glob_stdv

            corr_coeff = np.average((vA - np.mean(vA)) * (vB - np.mean(vB)) / (np.std(vA, ddof = 1) * np.std(vB, ddof = 1)))

        else:
            corr_coeff = np.nan

        all_corr_coeffs.loc[pair_idx, 'corr_coeff'] = corr_coeff
        all_corr_coeffs.loc[pair_idx, 'num_pts'] = num_pts
        
    return all_corr_coeffs


def get_corr_vs_dist(all_corr_coeffs, dist_bin_edges, dist_type = 'dist'):

    corr = []

    for d_from, d_to in zip(dist_bin_edges[:-1], dist_bin_edges[1:]):
        mask = (all_corr_coeffs[dist_type] >= d_from) & \
               (all_corr_coeffs[dist_type] < d_to)
        corr += [np.average(all_corr_coeffs.loc[mask, 'corr_coeff'])]

    dist_mid = (dist_bin_edges[:-1]+dist_bin_edges[1:])/2
    corr_vs_dist = pd.DataFrame({dist_type+'_from' : dist_bin_edges[:-1],
                                 dist_type+'_to'   : dist_bin_edges[1:],
                                 dist_type+'_mid'  : dist_mid,
                                 'corr_coeff'      : corr})

    corr_vs_dist.dropna(inplace = True)

    return corr_vs_dist