''' I'm lazy with Pickle files

DESCRIPTION:
This module contains super simple functions that handle files and directories

FUNCTIONS:
This module contains the following functions:
    * read
    * save
'''

import pickle as pkl
import os

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
    
