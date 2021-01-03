''' Automate populating element properties for QUAD4M analyses

DESCRIPTION:
This module contains functions that help populate element properties for QUAD4M
analysis, generally adding columns to the dataframe "elems" that then gets 
exported to a ".q4r" file.

MAIN FUNCTIONS:
This module contains the following functions:
    * elem_stresses: adds vertical and mean effective stress to elems dataframe
    * map_rf: map random field to elems dataframe.
    
'''

# ------------------------------------------------------------------------------
# Import Modules
# ------------------------------------------------------------------------------
import numpy as np
import pandas as pd

# ------------------------------------------------------------------------------
# Main Functions
# ------------------------------------------------------------------------------

def elem_stresses(nodes, elems, k = 0.5, unit_w = 21000):
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
        
    unit_w : float (defaults = 21000)
        unit weight for material, *ONLY* used if "elems" does not already 
        include a 'unit_w' column!!!

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
      calculations. Otherwise, a "unit_w" value will be used, which
      defaults to 21000 N/m3. CAREFUL WITH UNITS!!
    '''

    # If there isn't already a unit_w in elems dataframe, then choose a uniform
    # one for all (if none provided, defaults to 21000 N/m3)
    if 'unit_w' not in list(elems):
        elems['unit_w'] = unit_w * np.ones(len(elems))

    # Get the top of each node column (goes left to right)
    top_ys_nodes = [col['y'].max() for _, col in nodes.groupby('node_i')]

    # Get top of each element col (average of top left and top right nodes)
    # (moving average of top_ys_nodes with window of 2; see shorturl.at/iwFLY)
    top_ys_elems = np.convolve(top_ys_nodes, [0.5, 0.5], 'valid')

    # Initialize space for vertical stress column
    elems[['sigma_v', 'sigma_m']] = np.zeros((len(elems), 2))
    
    # Iterate through element soil columns (goes left to right) 
    for (_, soil_col), y_top in zip(elems.groupby('xc'), top_ys_elems):

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


def map_rf(elems, prop, z):
  ''' map random field to elems dataframe.
    
    Purpose
    -------
    Given a table of elems, this function adds a column called "props" and maps
    the values in the array "z" to the appropriate elements.
    
    Parameters
    ----------
    elems : pandas DataFrame
        Contains information for elements, usually created by 'geometry.py'
        At a *minumum*, must have columns: [elem_n, elem_i, elem_j].
        IMPORTANT! Element numbering i and j must agree with z convention below.

    prop : str
        name of the property being added to elems, used as column header.
        
    z : numpy array
        random field realization (generally created by randfields package)
        it is assumed that indexing in this array is of size n1xn2 if 2D. 
        Indexing is as follows:
          Z(1,1) is the lower left cell.
          Z(2,1) is the next cell in the X direction (to right).
          Z(1,2) is the next cell in the Y direction (upwards).

    Returns
    -------
    elems : pandas DataFrame
        Returns elems DataFrame that was provided, with added columns 
        for the desired property.
        
    Notes
    -----
    * Take extreme care that the indexing of elems i and j is consistent with 
      the indexing in the z array. That is:
        i starts left and moves rightwards
        j starts down and move upwards
    * Note that Z is assumed to be equispaced, which might not be true of the
      elements. Up to you to check.
    *   
    '''
  
  # Do some basic error checking
  err_check = map_rf_check_inputs(elems, prop, z)

  if len(err_check) > 0:
    print(err_check)
    return 0

  # Mapping
  mapped_z = [z[i-1, j-1] for i, j in zip(elems['i'], elems['j'])] 
  elems[prop] = mapped_z

  return elems


def add_bound_conds(bc_type, nodes):
  ''' Assigns boundary conditions to the "nodes" dataframe

  Purpose
  -------
  Given a type of boundary conditions (bc_type), this adds a "BC" column to 
  the dataframe "nodes" with integers that determine the type of boundary
  condition that QUAD4M will apply at that node. 
  
  From QUAD4M manual:
    0 - Free nodal point
    1 - Input horizontal earthquake motion applied. Free in Y direction.
    2 - Input vertical earthquake motion applied. Free in X direction.
    3 - Input horizontal and vertical earthquake motion applied.
    4 - Transmitting base node.
      
  Parameters
  ----------
  bc_type : str
      Describes the type of boundary condition configuration (limited so far).
      One of:
        rigidbase_box: fixes Y on left and right boundaries, rigid base at the
                       bottom. Since assignment relies on min(x), max(x), and
                       min(y), the edges of the mesh must be straight (box-like)
                       otherwise this function will fail.

  nodes : dataframe
      contains geometry information of nodes in QUAD4M model (see geometry.py)
      Must, at a minimum, contain: [n, x, y]
      
  Returns
  -------
  nodes : dataframe
      Returns the same dataframe, except with a new column: ['BC']

  Notes
  -----
  * This should really be extended to have more options.
      
  Refs
  ----
    (1) Hudson, M., Idriss, I. M., & Beikae, M. (1994). User’s Manual for
        QUAD4M. National Science Foundation.
            See: Fortran code describing inputs (Pg. A-5)
  '''

  # Initialize array of boundary conditions (0 = free nodes)
  ndpt = len(nodes)
  BC = 0 * np.ones(ndpt)

  if bc_type == 'rigidbase_box':

    # Apply a fixed-y BC at left (0, all) and right (1, all) boundaries
    loc_mask = get_nodes_mask([(0, 'all'), (1, 'all')], nodes)
    BC[loc_mask] = 2

    # Apply a rigid-base at the bottom boundary (all, 0)
    loc_mask = get_nodes_mask([('all', 0)], nodes)
    BC[loc_mask] = 3

  else:

    # If bc_type doesn't match any pre-coded options, raise an error 
    error  = 'Type of boundary condition not recorgnized\n'
    error += 'Only "rigidbase_box" is available so far.'
    raise Exception(error)

  nodes['BC']  = BC
  
  return(nodes)


def add_acc_outputs(locations, out_types, nodes):
  ''' Adds output acceleration options at nodes for QUAD4M analyses.
      
  Purpose
  -------
  This adds a column 'OUT' to the nodes dataframe, that determines the locations
  where acceleration time histories will be printed after a QUAD4M analyses.

  Parameters
  ----------
  locations : list of touples of float or str
      Each element is a touple with (horz_location, vert_location, out_type)
      that dictates where and which output accelerations will be printed.
      
      horz_loc : ratio from the left and rightwards
                0 = left corner, 1 = right corner, 0.5 = center, or 'all'
                
      vert_loc : ratio from the bottom and upwards
                0 = bott corner, 1 = top corner, 0.5 = center, or 'all
                
      out_type : type of acceleration to output. [ 'X', 'Y', 'B'(oth) ]

  Returns
  -------
  nodes : datafrmame
      Description of the parameter.
      Include assumptions, defaults, and limitations!
      
  Returns
  -------
  nodes : dataframe
      Returns the same dataframe, except with a new column: ['OUT']

  Notes
  -----
  * This should really be extended to have more options.
  * From QUAD4MU manual:
      0 - No acceleration history output
      1 - X acceleration history output
      2 - Y acceleration history output
      3 - Both X and Y acceleration history output

  Refs
  ----
    (1) Hudson, M., Idriss, I. M., & Beikae, M. (1994). User’s Manual for
        QUAD4M. National Science Foundation.
            See: Fortran code describing inputs (Pg. A-5)
  '''

  # Initialize array of output options (0 = no output)
  out_types_opts = {'X': 1, 'Y':2, 'B':2}
  ndpt = len(nodes)
  OUT = 0 * np.ones(ndpt)
      
  # If out_types is just a string, turn into list so that the loop works
  if isinstance(out_types, str):
    out_types = len(locations) * [out_types]
      
  # Iterate through provided locations:
  for loc, out_type in zip(locations, out_types):
    loc_mask = get_nodes_mask([loc], nodes) # Get mask of where to apply out_type
    out_int = out_types_opts[out_type]      # Get int corresponding to out_type 
    OUT[loc_mask] = out_int                 # Apply to array
  
  # Add results to nodes dataframe and return
  nodes['OUT'] = OUT
  return nodes


def add_ini_conds(locations, ics, nodes):
  ''' TODO-asap: document''' 

  # Initialize array of output options (0 = no output)
  ndpt = len(nodes)
  params = ['X2IH', 'X1IH', 'XIH', 'X2IV', 'X1IV', 'XIV']
  INITARR = np.zeros((ndpt, len(params)))

  for loc, ic in zip(locations, ics):
    loc_mask = get_nodes_mask(loc, nodes) # Get mask of where to apply out_type
    INITARR[loc_mask] = ic                 # Apply boundary conditions
  
  # Add results to nodes dataframe and return
  nodes[params] = INITARR
  return nodes


def add_uniform_props(properties, elems):
  ''' TODO-asap: document this'''

  for prop, val in properties.items():
    elems[prop] = val * np.ones(len(elems))
  
  return elems


# ------------------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------------------

def get_nodes_mask(locations, nodes):
  ndpt = len(nodes)

  # Iterate through provided locations:
  one_location_masks = []
  for horz, vert in locations:

    # First do X mask, then Y mask, then combine using AND logical
    xy_masks = []
    
    for coord, ratio in zip(['x', 'y'], [horz, vert]):

      if ratio == 'all':
        # If user specified 'all', then everywhere
        xy_masks += [ True * np.ones(ndpt) ]
      
      # Otherwise, find the closest match to the provided ratio
      else:
        values  = nodes[coord] # List of coordinates (x then y)

        # Find the exact coordinate the user asked for (based on "ratio") 
        target  = np.min(values) + ratio * (np.max(values)-np.min(values))
        
        # Find the closest match in the mesh to the calculated target
        closest = values [np.argmin((values - target)**2)] 

        # Return a mask for the locations that are closest to the target
        xy_masks += [ values == closest ]
     
    one_location_masks += [np.all(xy_masks, axis = 0)]

  # Combine across all locations using OR logical operator
  all_locations_mask = np.any(one_location_masks, axis = 0)
  
  return(all_locations_mask)


def map_rf_check_inputs(elems, prop, z):
  ''' Does some really basic error checking for the inputs to map_rf '''

  # Some (really) basic error checking
  errors = {1: 'Missing i or j in elemes table. Please add.' ,
            2: 'Random field and q4m mesh do not have same num of is and js.',
            3: 'Property name already exists in elems. Please change.'}

  # Check that elems i and j exists, and that the random field is large enough
  err_flags = []
  try:
    max_i = np.max(elems['i'])
    max_j = np.max(elems['j'])
  except:
    err_flags += [1]
  else: 
    if (max_i != np.shape(z)[0]) or (max_j != np.shape(z)[1]):
      err_flags += [2]

  # Make sure that new property doesn't already exist in elems
  if prop in list(elems):
    err_flags += [3]

  # Print out errors
  err_out = [errors[f] for f in err_flags]
  return err_out