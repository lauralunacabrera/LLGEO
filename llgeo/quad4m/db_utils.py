import pickle as pkl
import pandas as pd
import numpy as np
import os
import warnings
import llgeo.quad4m.geometry as q4m_geom


def update_db_geom(path_db, file_db, path_DXF, new_DXF_files,
                   path_check = 'check/'):
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
        sub-directory from path_db where check DXFs will be printed out
        IF DOESN'T EXISTS, WILL EXIT WITH ERROR!
        if set to False, then no check DXFs will be printed

    Returns
    -------
    db_geom : dataframe
        "database" summary file, which now includes information on new_DXF_files

    geom_dicts : list of dictionaries
        Each element corresponds to a the DXF files provided in "new_DXF_files".
        Each element is a dict containing geometry info as described above. 
                        
    '''

    # Get the current database
    db_geom = get_db_geom(path_db, file_db)

    # Determine current id based on database
    if len(db_geom) > 0:
        i = np.max(db_geom['id'])
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
        if name in db_geom['name'].tolist():

            # Warn user that no new data is being processed
            mssg = 'Entry alread exists: {:10s}'.format(name)
            mssg +=  '\n Reading (not creating) data'
            warnings.showwarning(mssg , UserWarning, 'db_utils.py', '')

            # Determine name of entry
            i_exist = int(db_geom.loc[db_geom['name'] == name, 'id'])
            f_exist = '{i:03d}_{name}.pkl'.format(i = i_exist, name = name)

            # Read existing file
            handler = open(f_exist, 'rb')
            d_exist = pkl.load(handler) # data that already exists
            handler.close()

            # Add to output data and continue to next entry
            geom_dicts += [d_exist]
            continue
    
        # Otherwise, process new entry
        i += 1  # Update entry ID
        nodes, elems  = q4m_geom.dxf_to_dfs(path_DXF, new_DXF_file)
        W, H, N, w, h = q4m_geom.get_mesh_sizes(nodes, elems)

        # Save new entry to pickle in database directory
        out_file = '{i:03d}_{name}.pkl'.format(i = i, name = name) 
        out_data = {'id': i, 'name': name, 'W': W, 'H': H, 'nelm': N, 'welm': w,
                    'helm':h, 'nodes':nodes, 'elems':elems, 'readme': readme}
        
        handler = open(out_file, 'wb')
        pkl.dump(out_data, handler)
        handler.close()

        # Make sure check directory exists (if needed)
        if path_check and not os.path.exists(path_db + path_check):
            err  = 'DXF check directory does not exists\n'
            err += 'Create it, or set path_check = False'
            raise Exception()

        # Output DXFs as a check (if path_check is not False)        
        elif path_check:
            file_check = out_file.replace('.pkl', '.dxf')
            q4m_geom.dfs_to_dxf(path_db + path_check, file_check, nodes, elems)

        # Add summary info to db_geom
        cols = list(db_geom)
        new_row = pd.DataFrame([[i, name, W, H, N, w, h]], columns = cols)
        db_geom = db_geom.append(new_row, ignore_index = True)

        # Add new data for list export
        geom_dicts += [out_data]

    # Save db_geom summary file
    db_geom.to_pickle(path_db + file_db)

    return db_geom, geom_dicts


def get_db_geom(path_db, file_db, reset = False):
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

    reset : bool (optional)
        set TRUE to replace summary file with an empty one (BE CAREFUL!).

    Returns
    -------
    db : DataFrame
        Returns dataframe with summary info of available geometries. It is
        either an empty DF, or a read of a file_db (depends on inputs) 
    '''

    # Columns to add in summary file
    cols = ['id', 'name', 'W', 'H', 'nelm', 'welm', 'helm']

    # Check whether file exists
    exists = os.path.isfile(path_db + file_db)

    # Print warning if reset = True
    if reset:
        mssg  = 'Database summary file was deleted!!!'
        mssg += ' Make sure to remove pkl files or fix this somehow!'
        warnings.showwarning(mssg, UserWarning, 'db_utils.py', '')

    # Create new file, if needed
    if not exists or reset:
        db = pd.DataFrame([], columns = cols)
        db.to_pickle(path_db + file_db)

        mssg = 'New database summary file created! :)'
        warnings.showwarning(mssg, UserWarning, 'db_utils.py', '')

    # If no new file is needed, read existing one
    else:
        handler = open(path_db + file_db, 'rb')
        db = pkl.load(handler)
        handler.close()

    return db