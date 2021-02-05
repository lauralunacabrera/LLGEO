''' Utilities for handling "databases" for QUAD4M analyses.

DESCRIPTION:

This module helps create and manage "databases" of:
    * Geometries (db_geoms)
    * Earhtquakes (db_accs)
    * Non-linear properties (db_nonlins)
    * Random fields (db_rfs)

MAIN FUNCTIONS:
This module contains the following functions:
    * uptdate_db_geoms
    * 
    
'''

# ------------------------------------------------------------------------------
# Import Modules
# ------------------------------------------------------------------------------
import pandas as pd
import numpy as np
import os
import warnings

# LLGEO
import llgeo.quad4m.geometry as q4m_geom
import llgeo.utilities.files as llgeo_fls

# ------------------------------------------------------------------------------
# Main Functions
# ------------------------------------------------------------------------------
def update_db_accs(path_db, file_db, acc, tstep):
    ''' 
    This will be completed at another time.

    I initially processed the ground motions before doing things this way, and I
    don't want to waste time re-doing work. So, problem for another time. 

    For now, all the motions have been processed already and are saved.

    Either way, not sure that this function can even be written, since the nature
    of the text files would be different for each type of project. So maybe it's 
    just better to do individually each time.
    '''

    return False


def update_db_geoms(path_db, file_db, path_DXF, new_DXF_files, path_check):
    ''' Adds new entries to database of geometries
        
    Purpose
    -------
    Given a list of dxf files, this:
        * Processes new entries by generating elems and nodes dataframes and
          getting sizes of mesh. 
        * Saves pkl for each new geometry with all info
        * Updates the summary file "file_db" with new entries and returns it.
        * Returns list of dict with geometry info that was saved.

    Each processed geometry dictionary contains the following keys:
       *id     | entry id
       *name   | entry name
       *fname  | name of file where dfs are saved (includes extension .pkl)
       *W      | maximum width of the overall mesh
       *H      | maximum height of the overall meesh
       *nelm   | number of elements in the mesh
       *welm   | average width of all elements in mesh
       *helm   | average height of all elements in mesh
        nodes  | dataframe with node info (see llgeo/quad4m/geometry.py)
        elems  | dataframe with element info (see llgeo/quad4m/geometry.py)
        readme | short description of file

    (Items marked with * are included in summary file)
        
    Parameters
    ----------
    path_db : str
        directory containing geometry "database".
        
    file_db : str
        name of "database" summary file (usually ending in .pkl).

    path_DXF : str
        directory contianing new DXF files to be processed

    new_DXF_files : list of str
        list of dxf file names (usually ending in .dxf)

    path_check : str
        directory where "check" DXFs will be printed out
        If doesn't exist, will exit eith error.
        if set to False, then no check DXFs will be printed

    Returns
    -------
    db_geoms : dataframe
        "database" summary file, which now includes information on new_DXF_files

    geom_dicts : list of dictionaries
        Each element corresponds to a the DXF files provided in "new_DXF_files".
        Each element is a dict containing geometry info as described above. 
                        
    '''

    # Get the current database
    db_geoms = get_db(path_db, file_db, db_type = 'geoms' )

    # Determine current id based on database
    if len(db_geoms) > 0:
        i = np.max(db_geoms['id'])
    else:
        i = 0

    # Readme to be included in new entries
    readme = ''' This geometry was processed using llgeo/quad4m/db_utils.
                 It contains dataframes of elems and nodes, and some summary
                 info. Will be used to probabilistically run ground response 
                 analyses using QUAD4MU.'''
    
    # Loop through new files and process them
    geom_dicts = []
    for new_DXF_file in new_DXF_files:

        # Name of entry to be processed
        name = new_DXF_file.replace('.dxf', '')

        # If name already exists, read data continue to next entry
        if name in db_geoms['name'].tolist():

            # Warn user that no new data is being processed
            mssg = 'Entry alread exists: {:10s}'.format(name)
            mssg +=  '\n Reading (not creating) data'
            warnings.showwarning(mssg , UserWarning, 'db_utils.py', '')

            # Determine name of entry
            f_exist = db_geoms.loc[db_geoms['name'] == name, 'fname'].item()

            # Read existing file and add to output dictionary
            geom_dicts += [llgeo_fls.read_pkl(path_db, f_exist)]
            continue
    
        # Otherwise, process new entry
        i += 1  # Update entry ID
        nodes, elems  = q4m_geom.dxf_to_dfs(path_DXF, new_DXF_file)
        W, H, N, w, h = q4m_geom.get_mesh_sizes(nodes, elems)

        # Save new entry to pickle in database directory
        fname = '{i:03d}_{name}.pkl'.format(i = i, name = name) 
        out_data = {'id': i, 'name': name, 'fname': fname, 'W': W, 'H': H, 
                    'nelm': N, 'welm': w, 'helm':h, 'nodes':nodes,
                    'elems':elems, 'readme': readme}
        
        llgeo_fls.save_pkl(path_db, fname, out_data, True)

        # Make sure check directory exists (if needed)
        if path_check and not os.path.exists(path_check):
            err  = 'DXF check directory does not exists\n'
            err += 'Create it, or set path_check = False'
            raise Exception(err)

        # Output DXFs as a check (if path_check is not False)        
        elif path_check:
            file_check = fname.replace('.pkl', '.dxf')
            q4m_geom.dfs_to_dxf(path_check, file_check, nodes, elems)

        # Add summary info to db_geoms
        cols = list(db_geoms)
        new_row = pd.DataFrame([[i, name, fname, W, H, N, w, h]], columns= cols)
        db_geoms = db_geoms.append(new_row, ignore_index = True)

        # Add new data for list export
        geom_dicts += [out_data]

    # Save db_geoms summary file
    db_geoms.to_pickle(path_db + file_db)

    return db_geoms, geom_dicts


def get_unique_accs(db_accs, cols = ['T', 'type', 'name']):
    ''' Sometimes, acceleration database contains duplicate earthquakes
        (same earhquake and return period, but different orientation).
        This function returns unique earthquakes (as defined by "cols").
        Just returns the first entry it finds, so it's pretty arbitary.
    '''
    
    # Remove duplicates looking only at "cols"
    opts = {'keep':'first', 'inplace':True, 'ignore_index':True}
    db_accs.drop_duplicates(subset = cols, **opts)

    return db_accs


# ------------------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------------------
def search(db, conditions, return_col = 'all'):
    ''' Returns entries from db that meet desired condition
        
    Purpose
    -------
    Given a "database" summary file (db), this returns the entries that match
    the conditions specified in the dictionary "conditions". 
        
    Parameters
    ----------
    db : dataframe
        Database summary file 
        
    conditions : dict
        Conditions to be met. Ex: {'T': 2475} will return db entries in which
        the column T has a value of 2475. So far, only equality is checked
        (no > or <)

    return_col : list of str (or str) (optional)
        list of column names to return, or a single string for one coloumn
        if a single column is given, then the return will be a numpy array (not 
        dataframe series). Otherwise, the return will be a DataFrame.
        Defaults to returning all columns.
        
    Returns
    -------
    result : numpy array or dataframe
        db entries that match condition, with output columns dictated by
        return_col. If there is only one return_col, then result is np array,
        otherwise it is a dataframe.

    Notes
    -----
    * TODO-wishlist: could this include > and < at some point?
    '''

    # Find which db entries meet ALL conditions 
    masks = [ db[col] == val for col, val in conditions.items()]
    all_mask = np.all(masks, axis = 0)
   
   # If return_col is 'all', then return all columns.
    if return_col == 'all':
        return_col = list(db)
    
    # Extract desied columns
    result = db.loc[all_mask, return_col]

    # If only one column was requested, change to numpy array
    if not isinstance(return_col, list):
        result = result.values

    return result


def get_db(path_db, file_db, db_type = False, reset = False):
    ''' Gets the summary dataframe of available geometries.
        
    Purpose
    -------
    This function gets the dataframe that contains summary information of the
    available geometries in the "database" stored in "path_db".

    If path_db + file_db does not exist:
        An empty DF will be created, saved as pkl, and returned. 

    If path_db + file_db already exists and reset = False:
        Nothing will be created/saved. Existing pkl will be read and returned.

    (BE CAREFUL WITH THIS USE)
    If path_db + file_db already exists and reset = True:
        An empty DF will be created, saved as pkl, and returned. 
        CAREFUL: this will override existing file.

    (Not generally used directly)

    Parameters
    ----------
    path_db : str
        path to the geometry "database".
        
    file_db : str
        name of "database" summary file (usually ending in .pkl).

    db_type : str
        type of dataframe to get. One of: geoms | accs | nonlins | rfs |
        only needed if database is being created for the first time.

    reset : bool (optional)
        set TRUE to replace summary file with an empty one (BE CAREFUL!).

    Returns
    -------
    db : DataFrame
        Returns dataframe with summary info of available geometries. It is
        either an empty DF, or a read of a file_db (depends on inputs) 
    '''

    # Check whether file exists
    exists = os.path.isfile(path_db + file_db)

    # Print warning if reset = True
    if reset:
        mssg  = 'db_' + db_type + ' summary file was deleted!!!'
        mssg += ' Make sure to remove pickle files as well.'
        warnings.showwarning(mssg, UserWarning, 'db_utils.py', '')

    # Create new file, if needed
    if not exists or reset:
        
        # Columns to add in summary file
        if db_type == 'geoms':
            cols = ['id', 'name', 'fname', 'W', 'H', 'nelm', 'welm', 'helm']

        elif db_type == 'accs':
            raise Exception('heh, you didnt code this in silly')
            # cols = ['id', 'name', 'fname', 'T', 'kind', 'dir', 'n', 'step', 'max']

        elif db_type == 'nonlins':
            pass

        elif db_type == 'rfs':
            pass

        else:
            raise Exception('type of db not recognized.')

        db = pd.DataFrame([], columns = cols)
        db.to_pickle(path_db + file_db)

        mssg = 'New database summary file created! :)'
        warnings.showwarning(mssg, UserWarning, 'db_utils.py', '')

    # If no new file is needed, read existing one
    else:
        db = llgeo_fls.read_pkl(path_db, file_db)

    return db