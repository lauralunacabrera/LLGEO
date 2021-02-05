''' Functions for post-processing QUAD4M analyses

DESCRIPTION:
These functions read output files from QUAD4M (.out, .bug, .acc and .str) and 
parse the results into Python data objects to allow the user to review the
results.

'''

import pandas as pd
import numpy as np

# ------------------------------------------------------------------------------
# Main Functions
# ------------------------------------------------------------------------------
def process_hist(in_path, in_file):
    ''' Post-processing for QUAD4M stress or acceleration time histories. 
        
    Purpose
    -------
    Given stress or acceleration outputs from QUAD4M, this reads and parses the
    contents to return a dataframe with stress or accelration time histories.  
    IMPORTANT: this assumes that the output file was created using QUAD4M's 
               "combined" option. Probably won't work otherwise.

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
    hist : dataframe
        Stress or acceleration time history results organized in dataframe,
        where first column is time and each column is the time history for
        an element (for stress) or node (for acceleration).
        
    '''

    # Read contents of the file    
    with open(in_path + in_file, "r") as f:
        lines = f.readlines()

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

    # Read data headers
    cols = lines[s-1].split()

    # Extract time history values
    hist = np.empty((len(lines)-s, len(cols)))

    for i, line in enumerate(lines[s:]):
        # Read and clean-up values in line
        vals = [line[i:i+w].strip() for i in range(0, len(line), w)] # delimited
        vals = vals[0:len(cols)] # Remove trailing white-space
        vals = pd.to_numeric(vals, errors = 'coerce') # Turn str to float

        # Add to outut array
        hist[i, :] =  vals

    # Transform to DataFrame and output
    hist = pd.DataFrame(hist, columns = cols)

    return hist

# ------------------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------------------


