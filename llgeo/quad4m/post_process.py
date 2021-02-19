''' Functions for post-processing QUAD4M analyses

DESCRIPTION:
These functions read output files from QUAD4M (.out, .bug, .acc and .str) and 
parse the results into Python data objects to allow the user to review the
results.

'''
import pandas as pd
import numpy as np
import os

import llgeo.utilities.files as llgeo_fls

# ------------------------------------------------------------------------------
# Main Functions
# ------------------------------------------------------------------------------
def postprocessQ4M(model_path, model_name, out_path = None, out_file = None,
                   read_flags = None, del_txt = False):
    ''' Post-process a single QUAD4M model with name "model_name".
        
    Purpose
    -------
    This module post-processes a single QUAD4M file and turns the results into
    a python-friendly format.
        
    Parameters
    ----------
    model_path : str
        Directory where output files are saved. All files must be contained 
        in this same directory.
        
    model_name : str
        Name of the model to post-process. All files must have the same name, 
        with only the extension changing
        (Ex. model1.out, model1.acc, model1.str, model1.bug)

    out_path : str (optional)
        Directory to save processed results as a pickle.
        Defaults to None, so that no output file is created.

    out_file : str (optional)
        Name of file to save processed results as a pickle (should end in .pkl)
        Defaults to None, so that no output file is created.

    read_flags : dict (optional)
        Dictionary indicating which output files to process. If given, should
        at a minimum have the keys: ['out', 'acc', 'str'], with values being
        bools. If false, this won't process that type of output file.
        Defaults to all being True (make sure the files exist!)
        
    del_txt : bool (optional)
        If true (and post = true), the text files for QUAD4M analyses will all
        be deleted. Defaults to false. Note that the files will only be deleted
        if the model was deemed to finish succcessfully, so that errors can be
        properly debugged.

    Returns
    -------
    outputs : dict
        Dictionary of outputs from the model, where the contents depend on the
        provided flags.
        If no flags are given, dictionary will include:
            ['model', 'run_success', 'peak_str', 'peak_acc', 'eq_props', 'Ts',
            'acc_hist', 'str_hist']
    '''
    # If no flags were provided, turn all of them on
    if not read_flags:
        read_flags = {'out': True, 'acc': True, 'str': True}
    
    # Print progress
    print('Now post-processing model {:s}'.format(model_name), flush = True)
        
    # Initialize output dictionary and success flags for this model
    output = {'model': model_name}
    success_flags = []

    # Output file 
    if read_flags['out']:
        labels = ['peak_str', 'peak_acc', 'eq_props', 'Ts']
        flag, values = process_out(model_path, model_name + '.out')
        output.update({k : v for k, v in zip(labels, values)} )
        success_flags += [flag]
            
    # Acceleration histories file
    if read_flags['acc']:
        flag, values = process_hist(model_path, model_name + '.acc')
        output.update({'acc_hist' : values})
        success_flags += [flag]

    # Stress histories file
    if read_flags['str']:
        flag, values = process_hist(model_path, model_name + '.str')
        output.update({'acc_str' : values})
        success_flags += [flag]

    # Determine whether the model ran everything correctly
    if np.all(success_flags):
        output.update({'run_success': True})
    else:
        output.update({'run_success': False})
                  
    # If required, save output file
    if (out_path is not None) & (out_file is not None):
        llgeo_fls.save_pkl(out_path, out_file, output, True)

    # If required, delete text files
    # Delete input files (if required)
    extensions = ['.q4r', '.dat', '.shk', '.out', '.acc', '.str', '.bug']
    [os.remove(model_path + model_name + e) for e in extensions 
        if (del_txt) & # Delete if del_txt flag is True, AND
           (output['run_success']) & # if the model ran successfully, ABD
           (os.path.exists(model_path + model_name + e))] # if the file exists
    
    return output


def postprocess_stage(stage_path, out_path = None, out_file = None,
                      read_flags = None, save_sep = False, del_txt = False):
    ''' Post-processes all QUAD4M models within a stage.
        
    Purpose
    -------
    A stage is a collection of QUAD4M models, which are all saved in the di-
    rectory "stage_path". This function processes the output files contained in
    those directories and returns a list of outputs in Python-friendly formats.
    This is simply a wrapper function for "postprocessQ4M".
        
    Parameters
    ----------
    stage_path : str
        Directory where models are saved. All files in this directory will
        be processed.
    
    out_path : str (optional)
        Directory to save processed results as a pickle.
        Defaults to None, so that no output file is created.

    out_file : str (optional)
        Name of file to save processed results as a pickle (should end in .pkl)
        Defaults to None, so that no output file is created.

    read_flags : dict (optional)
        Dictionary indicating which output files to process. If given, should
        at a minimum have the keys: ['out', 'acc', 'str'], with values being
        bools. If false, this won't process that type of output file.
        Defaults to all being True (make sure the files exist!)

    save_sep : bool (optional)
        If true, each model will be saved as a separate pickle, with the name
        of the file being out_path + model_name.pkl (the paremeter out_file
        is tus ignored). If false, all the results will be saved in a single 
        pickle file if both out_path and out_file parameters are passed.
        
    del_txt : bool (optional)
        If true (and post = true), the text files for QUAD4M analyses will all
        be deleted. Defaults to false. Note that the files will only be deleted
        if the model was deemed to finish succcessfully, so that errors can be
        properly debugged.

    Returns
    -------
    outputs : list of dict
        list where each element contains a dictionary of outputs from a model.
        the contents of the output dictionary depend on provided flags. If no
        flags are given, dictionary will include:
        ['model', 'run_success',
        'peak_str', 'peak_acc',
        'eq_props', 'Ts', 'acc_hist', 'str_hist']
        
    '''
    
    # Initialize output list and read-in files to be processed
    outputs = []
    models = sorted([f.replace('.out', '') for f in os.listdir(stage_path)
                                                 if f.endswith('.out')])
    N = len(models) # number of models to be processed

    # Iterate through the models and process as needed
    for m, model in enumerate(models):

        if (out_path is not None) & (save_sep):
            out_file_model = model + '.pkl'
        else:
            out_file_model = None

        output = postprocessQ4M(stage_path, model, out_path, out_file_model,
                   read_flags, del_txt)

        # Add to the output list
        outputs += [output]

        # Report progress
        print('({:d}/{:d})'.format(m, N), flush = True)

    # If required, save output file
    if (out_path is not None) & (out_file is not None) & (not save_sep):
        llgeo_fls.save_pkl(out_path, out_file, outputs, True)

    return outputs


# ------------------------------------------------------------------------------
# Intermediate Functions
# ------------------------------------------------------------------------------

def process_hist(in_path, in_file):
    ''' Post-processing for QUAD4M stress or acceleration time histories. 
        
    Purpose
    -------
    Given stress or acceleration outputs from QUAD4M, this reads and parses the
    contents to return a dataframe with stress or accelration time histories.  
    IMPORTANT: this assumes that the output file was created using QUAD4M's 
               "combined" option. Probably won't work otherwise.

    The function will check that there are more than 5 lines. If there aren't
    will return NaN because the model must have failed.

    Parameters
    ----------
    in_path : str
        Location of stress or acceleration output file.
        
    in_file : str
        Name of the stress or acceleration output file. IMPORTANT! The string 
        'in_file' must end in either '.acc' for acceleration outputs or 
        '.str' for stress outputs. This determines how the file is read.

    Returns
    -------
    success : bool
        Returns true if model ran successfuly, false if it didn't

    hist : dataframe
        Stress or acceleration time history results organized in dataframe,
        where first column is time and each column is the time history for
        an element (for stress) or node (for acceleration).
        
    '''
    # Read contents of the file (exit with NaN if it doesn't exist)    
    try:
        with open(in_path + in_file, "r") as f:
            lines = f.readlines()
    except IOError: #(means the file doesn't exist)
        return False, np.nan

    # Return nan's if the histories weren't printed (job exploded)
    if len(lines) < 5:
        return False, np.nan
        
    # Parameters of the file
    if in_file.endswith('.str'):
        s = 3 # Line where the actual values start (0-indexed!)
        w = 8 # Width of the printed values
    elif in_file.endswith('.acc'):
        s = 3 # Line where the actual values start (0-indexed!)
        w = 10 # Width of the printed values
    else:
        mssg  = 'Error when reading :' + in_file + '\n'
        mssg += '   The file must end in .acc or .str'
        raise Exception(mssg)

    # Read data headers (split every 10 characters)
    cols = [lines[s-1][i:i+10] for i in range(0, len(lines[s-1]), 10)]

    # Extract time history values
    hist = np.empty((len(lines)-s, len(cols)))

    for i, line in enumerate(lines[s:]):
        # Read and clean-up values in line
        vals = [line[i:i+w].strip() for i in range(0, len(line), w)] # delimited
        vals = vals[0:len(cols)] # Remove trailing white-space
        vals = pd.to_numeric(vals, errors = 'coerce') # Turn str to float

        # Some nodes have additional acceleration or stress points later in time
        # This fills other nodes iwth NAN values as needed
        vals = np.append(vals, ( len(cols) - len(vals) ) * [np.nan] )

        # Add to outut array
        hist[i, :] =  vals

    # Transform to DataFrame and output
    hist = pd.DataFrame(hist, columns = cols)

    return True, hist


def process_out(in_path, in_file):
    ''' Post-processing for QUAD4M output file
        
    Purpose
    -------
    Given a ".out" file from QUAD4M, this reads and parses the contents to re-
    turn dataframes with the most important information. The function checks
    for the "end of job" message, and if it is not there will return all NaN
    values since the model did not succesfully converge.
        
    Parameters
    ----------
    in_path : str
        Location of stress or acceleration output file.
        
    in_file : str
        Name of the stress or acceleration output file.
        
    Returns
    -------
    success : bool
        Returns true if model ran successfuly, false if it didn't

    output_tuple : tuple
        Second return is a touple containing:

        peak_str : dataframe
            Contains peak stresses (sig_x, sig_y, sig_xy) and corresponding time
            for all elements in the QUAD4M mesh.

        peak_acc : dataframe
            Contains peak x and y accelerations and corresponding times for all
            nodes in the QUAD4M mesh.

        eq_props : dataframe
            Contains the properties used in the final iteration of the program, 
            as well as the difference from the previous iteration (should make
            sure this is sufficiently small). 

        Ts : float
            Natural period of vibration as calculated in the last iteration.

    '''

    # Read contents of the file (exit with NaN if it doesn't exist)    
    try:
        with open(in_path + in_file, "r") as f:
            lines = f.readlines()
    except IOError: #(means the file doesn't exist)
        print('\t-->' + in_file + ' does not exist')
        return False, (np.nan, np.nan, np.nan, np.nan)

    # Check that the job ended, return NaNs if it didnt
    success = '     ** END OF JOB **\n'
    if lines[-2] != success:
        print('\t-->' + in_file + ' did not run completely')
        return False, (np.nan, np.nan, np.nan, np.nan)

    # Find section breaks (marked by a line with a "1" -> so len(line) = 1)
    lines = [l.strip() for l in lines]
    len_lines  = np.array([len(l) for l in lines])
    idx_breaks = np.where(len_lines == 1)[0]

    # Peak stresses
    cols = ['n', 'sigx', 'sigy', 'sigxy', 'strn', 'time']
    peak_str = extract_section(lines, idx_breaks[-1]+6, -12, cols)

    # Peak accelerations
    cols = ['node_n', 'x', 'y', 'x_acc', 'x_time', 'y_acc', 'y_time']
    peak_acc = extract_section(lines, idx_breaks[-2]+5, idx_breaks[-1]-3, cols)

    # Linear-equivalent properties
    cols = ['n', 'G_prev', 'G_final', 'G_diff', 'D_prev', 'D_final', 'D_diff']
    eq_props = extract_section(lines, idx_breaks[-3]+20, idx_breaks[-2], cols)

    # Natural Period of Vibration
    Ts = float(lines[idx_breaks[-3]+7].split()[-2])

    return True, (peak_str, peak_acc, eq_props, Ts)


# ------------------------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------------------------

def extract_section(lines, idx_from, idx_to, cols):
    ''' Reads lines from idx_from to idx_to and returns dataframe with cols''' 

    sec = lines[idx_from : idx_to]
    vals = np.genfromtxt(sec)
    df = pd.DataFrame(vals, columns = cols)

    return df

 