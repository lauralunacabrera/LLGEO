''' I'm lazy with Pickle files hehe

DESCRIPTION:
This module contains super simple functions that handle files and directories.

'''

import os
import inspect
import pickle as pkl
from datetime import datetime

# ------------------------------------------------------------------------------
# Functions for handling Pickle files
# ------------------------------------------------------------------------------

def read_pkl(in_path, in_file):
    ''' very simple wrapper for reading pickle files '''

    handler = open(in_path + in_file, 'rb')
    contents = pkl.load(handler)
    handler.close()
    return contents
    

def save_pkl(out_path, out_file, contents, flag_save):
    ''' very simple wrapper for saving pickle files '''

    if not os.path.exists(out_path):
        os.mkdir(out_path)

    if flag_save:
        handler = open(out_path + out_file, 'wb')
        pkl.dump(contents, handler)
        handler.close()
        print('Pickle file saved at: \n' + out_path + out_file)

# ------------------------------------------------------------------------------
# Functions for handling files in directories
# ------------------------------------------------------------------------------

def delete_contents(del_path, extensions, verbose = True):
    ''' for quikly wiping out contents from folder. Careful!! '''

    # If a single extension was given, then turn to list
    if not isinstance(extensions, list): extensions = [extensions]
    
    # Check whether files exist
    if not os.path.exists(del_path): raise Exception('Delete path not found')
    
    # Get files
    for ext in extensions:
        files = [f for f in os.listdir(del_path) if f.endswith('.' + ext)]

        if len(files) == 0:
            if verbose:
                print('No files with extention .{:s} found.'.format(ext))
        else:
            [os.remove(del_path + f) for f in files]
            if verbose:
                print('Deleted the following files:')
                print(files)
    
# ------------------------------------------------------------------------------
# For proper documenting
# ------------------------------------------------------------------------------

def save_outputs(out_path, out_file, out_dict, src_name = None):
    ''' Saves a pickle with contents, adding src_file and datetime
        
    Purpose
    -------
    This saves "out_dict" as a pickle at the location out_path + out_file, while
    adding a timestamp and source file (if provided).
        
    Parameters
    ----------
    out_path : str
        Directory where output file will be saved. Note that if the path does 
        not exist, this function will create it. (Careful!)
        
    out_file : str
        Name of file (strongly recommended to end in .pkl !!).
        
    out_dict : dictionary
        Dictionary with contents to be saved.

    src_file : str (optional)
        Name of file that produced outputs. If none is provided, will be
        automatically detected (NOT WORKING IN IPYTHON!!)

    Returns
    -------
    out_dict : dictionary
        Returns the provided dictionary but with new keys:
            [saved_by_file, saved_on]
        
    Notes
    -----
    * TODO 
    Unfortunately the filename doesn' seem to work if using ipython (idk why)
    For now just pass src_name to avoid issue.
        
    '''

    # Get name of file that called this function
    # (Shameless steal from here: https://tinyurl.com/66fbrr31)
    caller = inspect.getframeinfo(inspect.stack()[1][0])
    
    # Add information to output dictionary
    new_info = {'saved_by_file'   : caller.filename,
                'saved_on' : datetime.today().strftime("%Y-%m-%d %X")}

    if src_name is not None:
        new_info.update({'saved_by_file' : src_name})

    out_dict.update(new_info)

    # Create output path if it doesn't exist
    if not os.path.exists(out_path):
        os.mkdir(out_path)

    # Save outputs
    save_pkl(out_path, out_file, out_dict, True)

    # Return output dictionary
    return out_dict


    