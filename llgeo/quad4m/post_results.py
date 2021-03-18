# TODO - document this!!!!!!!!!!!!!

import numpy as np
import pandas as pd
import llgeo.utilities.files as llgeo_fls
import llgeo.motions.spectra as llgeo_spc


def get_peak_acc(in_path, in_files, x_loc = False, verbose = True,
                 check_success = False):

    dfs = [] # List of output dataframes

    # Iterate through provided result files
    for i, one_file in enumerate(in_files):

        # Read result file
        result = llgeo_fls.read_pkl(in_path, one_file)

        # Check if model has failed
        if (check_success) & (not result['run_success']):
            print('Uh oh... ' + result['model'] + 'failed', flush = True)
            continue

        # Print progress
        if verbose:
            prog = '({:d}/{:d})'.format(i+1, len(in_files))
            print('\t' + result['model'] + prog, flush = True)

        # Read results
        name = result['model'] + '_pga'
        acc_df = result['peak_acc']
    
        # Determine data to extract if a specific x is given
        if x_loc:
            mask = (acc_df['x'] == x_loc)
        else:
            mask = (acc_df['x'] == x_loc)

        # Determine columns that are needed
        if i == 0:
           cols = ['node_n', 'x', 'y', 'x_acc']
        else:
            cols = ['node_n', 'x_acc']

        # Extract only the necessary data
        acc_df = acc_df.loc[mask, cols]

        # Rename, re-index and add to outputs
        acc_df.rename(columns = {'x_acc': name}, inplace = True)
        acc_df.set_index('node_n', inplace = True)
        dfs += [acc_df]
    
    # Combine into single df
    peak_acc = pd.concat(dfs, axis = 1)

    return peak_acc


def get_peak_csr(in_path, elem_files, resl_files, target_i = False,
                 verbose = True, check_success = False):
    
    # Initalize outputs
    dfs = []

    # Iterate through pairs of element and results files
    for i, (elem_f, resl_f) in enumerate(zip(elem_files, resl_files)):

        # Get elements information and results
        elems = llgeo_fls.read_pkl(in_path, elem_f)
        reslt = llgeo_fls.read_pkl(in_path, resl_f)
        strs  = reslt['peak_str']
        
        # Check if model failed
        if (check_success) & (not reslt['run_success']):
            print('Uh oh... ' + reslt['model'] + 'failed', flush = True)
            continue

        # Print progress
        if verbose:
            prog = '({:d}/{:d})'.format(i+1, len(elem_files))
            print('\t' + reslt['model'] + prog, flush = True)

        # Get locations of interest
        if target_i:
            i_mask = (elems['i'] == target_i)
        else:
            i_mask = np.ones(len(elems))

        # Extract needed information from elements dataframe
        ns = elems.loc[i_mask, 'n'].values
        xs = elems.loc[i_mask, 'xc'].values
        ys = elems.loc[i_mask, 'yc'].values
        sv = elems.loc[i_mask, 'sigma_v'].values

        # Get cyclic stress ratio 
        sigxy = np.array([float(strs.loc[strs['n'] == n, 'sigxy']) for n in ns])
        CSR = sigxy / sv

        # Create new dataframe and add to outputs
        if i == 0:
            new_df = pd.DataFrame({'n':ns, 'x':xs, 'y': ys, 'CSR':CSR})
            new_df.set_index('n', inplace = True)
        else:
            new_df = pd.DataFrame({'n':ns, 'CSR':CSR})
            new_df.set_index('n', inplace = True)

        dfs += [new_df]

    # Combine into a single df
    csr = pd.concat(dfs, axis = 1)

    return csr


def get_SAspectra(in_path, in_files, n, Ts, verbose = True,
                  check_success = False):

    dfs = [] # List of output dataframes

    # Iterate through provided result files
    for i, result_file in enumerate(in_files):

        # Read result file
        result = llgeo_fls.read_pkl(in_path, result_file)

        # Check if model has failed
        if (check_success) & (not result['run_success']):
            print('Uh oh... ' + result['model'] + 'failed', flush = True)
            continue

        # Print progress
        if verbose:
            prog = '({:d}/{:d})'.format(i+1, len(in_files))
            print('\t' + result['model'] + prog, flush = True)

        # Extract time history of interest
        acc_df = result['acc_hist']
        node_lbl  = ' Node{:4d}X'.format(n)
        acc_hist = acc_df.loc[:, node_lbl].values

        # Get response spectra
        dt = acc_df.iloc[1, 0] - acc_df.iloc[0, 0]
        _, _, _, SA, _, _ = llgeo_spc.resp_spectra_wang(acc_hist, dt, Ts)

        # Create new dataframe and add to outputs
        new_df = pd.DataFrame({'Ts': Ts, 'SA':SA})
        new_df.set_index('Ts', inplace = True)
        dfs += [new_df]

    # Combine into a single df
    SAspectra = pd.concat(dfs, axis = 1)

    return SAspectra