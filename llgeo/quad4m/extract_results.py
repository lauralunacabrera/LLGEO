''' Extract specific results from QUAD4M analyses that have been post-processed

DESCRIPTION:
These functions read the pickle fiels of post-processed results from QUAD4M 
analyses (see post_process.py) and extracts specific sections of those results 
for plotting or presentation purposes.
'''

import numpy as np
import pandas as pd
import llgeo.utilities.files as llgeo_fls
import llgeo.motions.spectra as llgeo_spc

# ------------------------------------------------------------------------------
# Functions that extract results from elems dataframes or results dictionary
# ------------------------------------------------------------------------------
def get_elems_prop(elem_dfs, names, target_col, target_val, return_col,
                   summ_stats = True, verbose = True):
    ''' Extract information from elements dataframe.
        
    Purpose
    -------
    Quick function to extract properties from element dataframe. For example, if
    I want the shear wave velocity for soil column i = 49, I would pass:
        get_elems_prop(elem_dfs, 'i', 49, 'vs').

    Parameters
    ----------
    elems_dfs : list of dataframes
        List of dfs containting the element information for the model (order 
        with results_dicts must match!!). Must contain at least the columns
        ['target_col' and 'return_col'] as well as ['n', 'i', 'j', 'xc', 'yc'.
        THESE MUST BE SAVED AHEAD OF TIME IN  THE MODEL GENERATION SCRIPTS!

    names : list of str
        Each string identifies which model the elements are coming from

    target_col : str
        Name of column of where to find "target_val"

    target_val : (?)
        Value to look for

    return_col " str
        Name of column to return

    summ_stats : bool (optinal)
        If true, will include summary statistics across models in the output
        dataframe. Will include: mean, stdv, min, and max. Defaults to true.

    verbose : bool (optional)
        If true (default), will print out progress to console.
        
    Returns
    -------
    out_df : dataframe
        returns element properties as well as elem_n, xc, yc.
        Each additional column represents one elem_df.
        Inlcudes summary statistics if required

    Notes
    -----
    * This will make a lot more sense if you also look at post_process.py
    * ALL MODELS IN RESULT_DICTS MUST HAVE THE SAME GEOMETRY
    '''

     # Initialize outputs
    if verbose: print('Now getting element property ' + return_col)
    dfs = []

    # Iterate through provided result files
    for i, (elems, name) in enumerate(zip(elem_dfs, names)):

        # Print progress
        if verbose:
            prog = '({:d}/{:d})'.format(i+1, len(elem_dfs))
            print('\t Processing element ' + prog, flush = True)

        # Find location to return
        mask = (elems[target_col] == target_val)

        # Create new dataframe and add to outputs
        if i == 0:
            cols = ['n', 'i', 'j', 'xc', 'yc', return_col] 
        else:
            cols = ['n', return_col] 

        # Extract only the necessary data
        new_df = elems.loc[mask, cols]

        # Rename, re-index and add to outputs
        col_name = name + '_' + return_col
        new_df.rename(columns = {return_col: col_name}, inplace = True)
        new_df.set_index('n', inplace = True)
        dfs += [new_df]
    
    # Combine into single df
    out_df = pd.concat(dfs, axis = 1)

    # If necessary, add summary statistics
    if summ_stats:
        cols = [c for c in list(out_df) if return_col in c]
        out_df['mean'] = out_df[cols].mean(axis = 1)
        out_df['stdv'] = out_df[cols].std(axis = 1)
        out_df['min']  = out_df[cols].min(axis = 1)
        out_df['max']  = out_df[cols].max(axis = 1)

    return out_df


def get_peak_acc(result_dicts, x_loc = None, verbose = True,
                 check_success = False , summ_stats = True):
    ''' Extract peak acceleration values for nodes in QUAD4M model results
        
    Purpose
    -------
    Given a list of QUAD4M analyses results (see post_process.py), this function 
    extracts the horizontal peak ground acceleration for nodes at "x_loc". If 
    one is not given, it returns the horizontal peak acceleration for all nodes. 
        
    Parameters
    ----------
    result_dicts : list of dict
        List of dictionaries containting the analysis results, which must
        contain the key "peak_acc" and "model" (see post-process.py).

    x_loc : float or bool (optional)
        Specifies x-coordinate of interest, so that only nodes at this 
        coordinate are returned (a soil column). If one is not provided, all 
        nodes in the mesh will be returned. Defaults to all nodes.

    verbose : bool (optional)
        If true, progress will be printed to console. Defaults to True

    check_success : bool (optional)
        If true, this will skip models that have been flagged as not running 
        properly. This is determined using the key "run_success", which should 
        be included in the dicitonary saved in the pickle files. Defaults to
        False.

    summ_stats : bool (optinal)
        If true, will include summary statistics across models in the output
        dataframe. Will include: mean, stdv, min, and max. Defaults to true.
        
    Returns
    -------
    peak_acc : pandas dataframe
        Contains the peak acceleration for each model and requested node. Starts
        with [node_n, x, y], and then includes a column for each model ran.
        
    Notes
    -----
    * This will make a lot more sense if you also look at post_process.py
    * ALL MODELS IN RESULT_DICTS MUST HAVE THE SAME GEOMETRY
    '''

    # Initialize outputs
    if verbose: print('Now getting peak accelerations')
    dfs = []

    # Iterate through provided result files
    for i, result in enumerate(result_dicts):

        # Check if model has failed
        if (check_success) & (not result['run_success']):
            print('Uh oh... ' + result['model'] + 'failed', flush = True)
            continue

        # Print progress
        if verbose:
            prog = '({:d}/{:d})'.format(i+1, len(result_dicts))
            print('\t' + result['model'] + prog, flush = True)

        # Read results
        acc_df = result['peak_acc']

        # Double check that acc_df is a dataframe
        # (will not be if model failed or wasnt processed correctly)
        if not isinstance(acc_df, pd.DataFrame):
            msg = 'Watch out: model {:s} did not '.format(result['model'])
            msg+= 'run or process correctly because "peak_acc" key in result'
            msg+= ' dict does not contain  a dataframe'
            msg+= '\n Will skip this model but check what happened!'
            print(msg)
            continue
    
        # Determine data to extract if a specific x is given
        if x_loc is None:
            mask = np.ones(len(acc_df))            
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
        col_name = result['model'] + '_pga'
        acc_df.rename(columns = {'x_acc': col_name}, inplace = True)
        acc_df.set_index('node_n', inplace = True)
        dfs += [acc_df]
    
    # Combine into single df
    peak_acc = pd.concat(dfs, axis = 1)

    # If necessary, add summary statistics
    if summ_stats:
        pga_cols = [c for c in list(peak_acc) if '_pga' in c]
        peak_acc['mean'] = peak_acc[pga_cols].mean(axis = 1)
        peak_acc['stdv'] = peak_acc[pga_cols].std(axis = 1)
        peak_acc['min']  = peak_acc[pga_cols].min(axis = 1)
        peak_acc['max']  = peak_acc[pga_cols].max(axis = 1)

    return peak_acc


def get_peak_csr(result_dicts, elems_dfs, target_i = False,
                 verbose = True, check_success = False, summ_stats = True):
    ''' Extract cyclic stress ratio for a elements in QUAD4M model results
        
    Purpose
    -------
    Given a single path and a list of files within that path, this function 
    will determine and return the peak cyclic stress ratio (tau_xy / sig'v).
    If target_i is given, it will do so for the soil column of elements matching
    that "i" value. If target_i is not given, it will return the peak CSR
    for all elements.  
        
    Parameters
    ----------
    result_dicts : list of dict
        List of dictionaries containting the analysis results, which must
        contain the key "peak_str" and "model" (see post-process.py).
        
    elems_dfs : list of dataframes
        List of dfs containting the element information for the model (order 
        with results_dicts must match!!). Must contain at least the columns
        ['n', 'xc', 'yc', 'sigma_v']. THESE MUST BE SAVED AHEAD OF TIME IN THE 
        MODEL GENERATION SCRIPTS!

    target_i : int (optional)
        The element "i" value of interest, so that results from a single soil
        column in the mesh are extracted. If one is not provided, results will
        be returned for all elements in the mesh (default).

    verbose : bool (optional)
        If true, progress will be printed to console. Defaults to True

    check_success : bool (optional)
        If true, this will skip models that have been flagged as not running 
        properly. This is determined using the key "run_success", which should 
        be included in the dicitonary saved in the pickle files. Defaults to
        False.

    summ_stats : bool (optinal)
        If true, will include summary statistics across models in the output
        dataframe. Will include: mean, stdv, min, and max. Defaults to true.
        
    Returns
    -------
    peak_acc : pandas dataframe
        Contains the peak acceleration for each model and requested node. Starts
        with [node_n, x, y], and then includes a column for each model ran.
        
    Notes
    -----
    * This will make a lot more sense if you also look at post_process.py
    * ALL MODELS IN RESULT_DICTS MUST HAVE THE SAME GEOMETRY
    '''

    # Initalize outputs
    if verbose: print('Now getting peak CSR')
    dfs = []

    # Iterate through pairs of element and results files
    for i, (elems, result) in enumerate(zip(elems_dfs, result_dicts)):

        # Check if model failed
        if (check_success) & (not result['run_success']):
            print('Uh oh... ' + result['model'] + 'failed', flush = True)
            continue

        # Print progress
        if verbose:
            prog = '({:d}/{:d})'.format(i+1, len(result_dicts))
            print('\t' + result['model'] + prog, flush = True)

        # Read peak stresses and get model name
        strs = result['peak_str']

        # Double check that strs is a dataframe
        # (will not be if model failed or wasnt processed correctly)
        if not isinstance(strs, pd.DataFrame):
            msg = 'Watch out: model {:s} did not '.format(result['model'])
            msg+= 'run or process correctly because "peak_str" key in result'
            msg+= ' dict does not contain  a dataframe'
            msg+= '\n Will skip this model but check what happened!'
            print(msg)
            continue

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
        col_name = result['model'] + '_csr'
        if i == 0:
            new_df = pd.DataFrame({'n':ns, 'x':xs, 'y': ys, col_name:CSR})
        else:
            new_df = pd.DataFrame({'n':ns, col_name:CSR})

        # Re-index and add to outputs
        new_df.set_index('n', inplace = True)
        dfs += [new_df]

    # Combine into a single df
    csr = pd.concat(dfs, axis = 1)

    # If necessary, add summary statistics
    if summ_stats:
        csr_cols = [c for c in list(csr) if '_csr' in c]
        csr['mean'] = csr[csr_cols].mean(axis = 1)
        csr['stdv'] = csr[csr_cols].std(axis = 1)
        csr['min']  = csr[csr_cols].min(axis = 1)
        csr['max']  = csr[csr_cols].max(axis = 1)

    return csr


def get_SAspectra(result_dicts, n, Ts,  zeta = 0.05, verbose = True,
                  check_success = False, summ_stats = True):
    ''' Returns acc response spectra for a given node and natural periods
        
    Purpose
    -------
    Given a single path and a list of files within that path, this function 
    will determine and return the acceleration response spectra at node "n" for
    natural periods of vibraion "Ts".  
        
    Parameters
    ----------
    result_dicts : list of dict
        List of dictionaries containting the analysis results, which must
        contain the key "acc_hist" and "model" (see post-process.py).

    n : int
        Node number for which to extract acceleration history. You must ensure
        that the time history was requested to QUAD4M and that it exists in the
        resutls. So far, only one node can be requested at a time. K.I.S.S.!

    Ts : numpy array
        Array of natural periods of vibration for which to determine the 
        response spectra.

    zeta : float (optional)
        Critical damping ratio to be used in calculations.
        Input as fractional number. Defaults to 0.05 (5% damping)     

    verbose : bool (optional)
        If true, progress will be printed to console. Defaults to True

    check_success : bool (optional)
        If true, this will skip models that have been flagged as not running 
        properly. This is determined using the key "run_success", which should 
        be included in the dicitonary saved in the pickle files. Defaults to
        False.

    summ_stats : bool (optinal)
        If true, will include summary statistics across models in the output
        dataframe. Will include: mean, stdv, min, and max. Defaults to true.
        
    Returns
    -------
    SAspectra : pandas dataframe
        Contains the response spectra of spectral accelerations for the models
        and nodes requested.
        
    Notes
    -----
    * This will make a lot more sense if you also look at post_process.py
    * ALL MODELS IN RESULT_DICTS MUST HAVE THE SAME GEOMETRY
    '''
    
    # Initalize outputs
    if verbose: print('Now getting acc spectra')
    dfs = []


    # Iterate through provided result files
    for i, result in enumerate(result_dicts):

        # Check if model has failed
        if (check_success) & (not result['run_success']):
            print('Uh oh... ' + result['model'] + 'failed', flush = True)
            continue

        # Print progress
        if verbose:
            prog = '({:d}/{:d})'.format(i+1, len(result_dicts))
            print('\t' + result['model'] + prog, flush = True)

        # Extract time history of interest
        acc_df = result['acc_hist']

        # Double check that acc_df is a dataframe
        # (will not be if model failed or wasnt processed correctly)
        if not isinstance(acc_df, pd.DataFrame):
            msg = 'Watch out: model {:s} did not '.format(result['model'])
            msg+= 'run or process correctly because "acc_hist" key in result'
            msg+= ' dict does not contain  a dataframe'
            msg+= '\n Will skip this model but check what happened!'
            print(msg)
            continue

        # Get response spectra
        node_lbl  = ' Node{:4d}X'.format(n)
        dt = acc_df.iloc[1, 0] - acc_df.iloc[0, 0]
        acc_hist = acc_df.loc[:, node_lbl].values
        _, _, _, SA, _, _ = llgeo_spc.resp_spectra_wang(acc_hist, dt, Ts, zeta)

        # Create new dataframe and add to outputs
        col_name = result['model'] + '_SA'
        new_df = pd.DataFrame({'Ts': Ts, col_name: SA})
        new_df.set_index('Ts', inplace = True)
        dfs += [new_df]

    # Combine into a single df
    SAspectra = pd.concat(dfs, axis = 1)

    # If necessary, add summary statistics
    if summ_stats:
        spectra_cols = [c for c in list(SAspectra) if 'SA' in c]
        SAspectra['mean'] = SAspectra[spectra_cols].mean(axis = 1)
        SAspectra['stdv'] = SAspectra[spectra_cols].std(axis = 1)
        SAspectra['min']  = SAspectra[spectra_cols].min(axis = 1)
        SAspectra['max']  = SAspectra[spectra_cols].max(axis = 1)

    return SAspectra

# ------------------------------------------------------------------------------
# For doing all these extractions on a set of files
# ------------------------------------------------------------------------------

def extract_results(in_path, result_files, elem_files, out_path, out_id,
                    src_name, karg_elem_prop = False,
                              karg_peak_acc  = False,
                              karg_peak_csr  = False,
                              karg_SAspectra = False):

    # TODO - document
 
    # --------------------------------------------------------------------------
    # Read files and basic set-up
    # --------------------------------------------------------------------------
    
    # Read all the result files
    result_dicts = [llgeo_fls.read_pkl(in_path, f) for f in result_files]

    # If necessary, read all the element files
    if (karg_elem_prop) or (karg_peak_csr):
        elem_dfs = [llgeo_fls.read_pkl(in_path, f) for f in elem_files]

    # --------------------------------------------------------------------------
    # Element property
    # --------------------------------------------------------------------------
    if karg_elem_prop:

        # Get element property dataframe
        names = [result['model'] for result in result_dicts]
        extracted_props = get_elems_prop(elem_dfs, names, **karg_elem_prop)
        
        # Save outputs
        return_col = karg_elem_prop['return_col']
        out_file = return_col + '_' + out_id + '.pkl' 
        outputs = {return_col: extracted_props,
                   'description': ' Contains summary of elements ' + return_col}
        llgeo_fls.save_outputs(out_path, out_file, outputs, src_name)

    # --------------------------------------------------------------------------
    # Peak Acceleration
    # --------------------------------------------------------------------------
    if karg_peak_acc:

        # Get element property dataframe
        peak_acc = get_peak_acc(result_dicts, **karg_peak_acc)
        
        # Save outputs
        out_file = 'PGA_' + out_id + '.pkl' 
        outputs = {'peak_acc': peak_acc,
                   'description': ' Contains peak accelerations'}
        llgeo_fls.save_outputs(out_path, out_file, outputs, src_name)

    # --------------------------------------------------------------------------
    # Peak CSR
    # --------------------------------------------------------------------------
    if karg_peak_csr:

        # Get element property dataframe
        peak_csr = get_peak_csr(result_dicts, elem_dfs, **karg_peak_csr)

        # Save outputs
        out_file = 'CSR_' + out_id + '.pkl' 
        outputs = {'peak_csr': peak_csr,
                   'description': ' Contains peak CSRs'}
        llgeo_fls.save_outputs(out_path, out_file, outputs, src_name)

    # --------------------------------------------------------------------------
    # Acceleration Response Spectra
    # --------------------------------------------------------------------------
    if karg_SAspectra:

        # Get element property dataframe0
        spectra = get_SAspectra(result_dicts, **karg_SAspectra)

        # Save outputs
        out_file = 'SPECTRA_' + out_id + '.pkl' 
        outputs = {'spectra': spectra,
                   'description': ' Contains acceleration spectra'}
        llgeo_fls.save_outputs(out_path, out_file, outputs, src_name)
   
    return True