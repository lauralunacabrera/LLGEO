''' Automate populating element properties for QUAD4M analyses

DESCRIPTION:
This module contains functions that help populate element properties for QUAD4M
analysis, generally adding columns to the dataframe "elems" that then gets 
exported to a ".q4r" file.

MAIN FUNCTIONS:
This module contains the following functions:
    * elem_stresses: adds vertical and mean effective stress to elems dataframe
    
TODOS:
'''
# ------------------------------------------------------------------------------
# Import Modules
# ------------------------------------------------------------------------------
import numpy as np
import pandas as pd

# ------------------------------------------------------------------------------
# Main Functions
# ------------------------------------------------------------------------------

def elem_stresses(nodes, elems, k = 0.5, def_unit_w = 21000):
    ''' add vertical and mean effective stress to elements data frame
    
    Purpose
    -------
    Given the dataframes "elems" and "nodes" (created by 'geometry' module),
    this function adds columns for the vertical stress and the mean stress at 
    the center of each element.
    
    Parameters
    ----------
    nodes : pandas dataframe
        Contains information for elements, usually created by 'geometry.py'
        At a *minumum*, must have columns: [node number, x, y]

    elems : pandas DataFrame
        Contains information for elements, usually created by 'geometry.py'
        At a *minumum*, must have columns: [element number, xc, yc]

    k : float (defaults = 0.5)
        coefficient of lateral earth pressure at rest.
        
    def_unit_w : float (defaults = 21000)
        unit weight for material, *ONLY* used if "elems" does not already 
        include a 'unit_w' column.

    Returns
    -------
    elems : pandas DataFrame
        Returns elems DataFrame that was provided, with added columns for effec-
        tive and mean stress: ['unit_v', 'unit_m]. CAREFUL WITH UNITS.
        
    Notes
    -----
    * If unit_w provided is effective, stresses will be effective.
      Be careful with units!! unit_w and coordinate units must somehow agree.
    * As in 'geometry' module, elements are assumed to be arranged in verti-
      cal columns (no slanting).
    * Elements and nodes should be numbered bottom-up, and left-to-right
      (start at lower left column, move upwards to surface, then one col 
      to the right).
    * Unless provided otherwise, a value of 0.5 is used for lateral earth
      pressure coefficient at rest.
    * If a unit weight column already exists in elems, this will be used in
      calculations. Otherwise, a "def_unit_w" value will be used, which
      defaults to 21000 N/m3. CAREFUL WITH UNITS!!
    '''

    # If there isn't already a unit_w in elems dataframe, then choose a uniform
    # one for all (if none provided, defaults to 21000 N/m3)
    if 'unit_w' not in list(elems):
        elems['unit_w'] = def_unit_w * np.ones(len(elems))

    # Get the top of each node column (goes left to right)
    top_ys_nodes = [col['y'].max() for _, col in nodes.groupby('node_i')]

    # Get top of each element col (average of top left and top right nodes)
    # (moving average of top_ys_nodes with window of 2; see shorturl.at/iwFLY)
    top_ys_elems = np.convolve(top_ys_nodes, [0.5, 0.5], 'valid')

    # Initialize space for vertical stress column
    elems[['sigma_v', 'sigma_v']] = np.zeros((len(elems), 2))
    
    # Iterate through element soil columns (goes left to right) 
    for (x_coord, soil_col), y_top in zip(elems.groupby('xc'), top_ys_elems):

        # Get array of y-coords at center of element and unit weights
        # Note that in elems dataframe, elements are ordered from the bot to top
        # Here I flip the order so that its easier for stress calc (top down)  
        ns = np.flip(soil_col['n'].to_numpy())
        ys = np.flip(soil_col['yc'].to_numpy())
        gs = np.flip(soil_col['unit_w'].to_numpy())

        # Get y_diff, the depth intervals between center of elements
        y_diff_start = y_top - np.max(ys) # depth to center of top element
        y_diff_rest  = ys[0:-1] - ys[1:]  # depth intervals for rest of elements
        y_diff = np.append(y_diff_start, y_diff_rest) # depth intervals for all
    
        # Calculate vertical stress increments, and then vertical stress profile
        vert_stress_diff = y_diff * gs
        vert_stress_prof = np.cumsum(vert_stress_diff)

        # Convet vertical stress to mean effective stress
        # (assumes ko = 0.5 unless another value is provided)
        mean_stress_prof = (vert_stress_prof + 2 * k * vert_stress_prof) / 3

        for n, vert, mean in zip(ns, vert_stress_prof, mean_stress_prof):
            elems.loc[elems['n'] == n, 'sigma_v'] = vert
            elems.loc[elems['n'] == n, 'sigma_m'] = mean

    return(elems)