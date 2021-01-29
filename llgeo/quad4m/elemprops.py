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
    for (_, soil_col), y_top in zip(elems.groupby('i'), top_ys_elems):

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


def map_vs_powerfit(nodes, elems, pfits, add_G, unit_fix, unit_w = 21000):
    ''' Maps powerfits of shear wave velocity to elems. pfits shoudl be a list
    of dict with const and power. List order should correspond to 'lay' in elems
    If add_G = True, will also add a column to elems where G = Gmax 
    If unit_fix = True, will divide Gmax (and G) by 1000 since QUAD4M works in 
        those units
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

    # Iterate through element soil columns (goes left to right)
    elems['vs'] = np.empty(len(elems)) 
    elems['Gmax'] = np.empty(len(elems))
    elems['depth'] = np.empty(len(elems))

    for (i, soil_col), y_top in zip(elems.groupby('i'), top_ys_elems):

        # Get array of y-coords at center of element and unit weights
        # Note that in elems dataframe, elements are ordered from the bot to top
        # Here I flip the order so that its easier for stress calc (top down)  
        ys = soil_col['yc'].values
        gs = soil_col['unit_w'].values
        ds = y_top - ys

        # Determine power and constant as function of depth (based on layer)
        layers = soil_col['layer'].values
        powers = [pfits[int(L)]['power'] for L in layers]
        consts = [pfits[int(L)]['const'] for L in layers]
        pluss  = [pfits[int(L)]['plus']  for L in layers]
        
        # Calculate vs and Gmax
        vs = np.array([c*d**power+plus for c, d, power, plus in
                       zip(consts, ds, powers, pluss)])
        Gm = (gs/9.81) * (vs**2)

        # Export results
        elems.loc[elems['i'] == i, 'vs']    = vs
        elems.loc[elems['i'] == i, 'Gmax']  = Gm
        elems.loc[elems['i'] == i, 'depth'] = ds
    
    # Fix units if necessary
    if unit_fix:
      elems['Gmax'] = elems['Gmax'] / 1000
    
    # Add new column "G" if necessary
    if add_G:
      elems['G'] = elems['Gmax']

    return elems


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


def map_layers(elems, lay_1D, reverse_lay = True):
  ''' Adds layering to elems given lay_1d.
      it is assumed that the first element in lay_1d corresponds to the ground 
      surface, and that elems are numbered first at the bottom. Then, the 
      default behaviour is to reverse the lay_1D array (can be set to False).
  '''
  js = elems['j'].values
  elems['layer'] = np.nan * np.ones(len(elems))

  if reverse_lay:
    lay_1D = np.flip(lay_1D)

  for j in np.unique(js):
    elems.loc[elems['j'] == j, 'layer'] = lay_1D[j - 1] # python is 0-indexed, j is 1-indexed
  
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
    loc_mask = get_mask([(0, 'all', 'dec'), (1, 'all', 'dec')], nodes)
    BC[loc_mask] = 2

    # Apply a rigid-base at the bottom boundary (all, 0)
    loc_mask = get_mask([('all', 0, 'dec')], nodes)
    BC[loc_mask] = 3

  else:

    # If bc_type doesn't match any pre-coded options, raise an error 
    error  = 'Type of boundary condition not recorgnized\n'
    error += 'Only "rigidbase_box" is available so far.'
    raise Exception(error)

  nodes['BC']  = BC
  
  return(nodes)


def add_acc_outputs(locations, out_type, nodes):
  ''' Adds output acceleration options at nodes for QUAD4M analyses.
      
  Purpose
  -------
  This adds a column 'OUT' to the nodes dataframe, that determines the locations
  where acceleration time histories will be printed after a QUAD4M analyses.

  Parameters
  ----------
  locations : list of touples
      Each element is a touple with: (horz, vert, ij_or_dec, out_type)
      that dictates where and which output accelerations will be printed.
      
      horz : horizontal location where accelerations should be printed
             if ij: must be "i" of node number (or be 'all')
             if dec:ratio from the left and rightwards
                    (0 = left corner, 1 = right corner, 0.5 = center, or 'all')
                
      vert : vertical location where accelerations should be printed
             if ij: must be "j" of node number (or be 'all')
             if dec: ratio from the bottom and upwards
                     (0 = bott corner, 1 = top corner, 0.5 = center, or 'all')
      
      ij_or_dec : either 'ij' or 'dec', determines how horz and vert are read
                   if 'ij'  : horz and vert must be node numbers.
                   if 'dec' : horz and vert must be ratio of domain

  out_type :
      Type of acceleration to output.
      Can either be a single string: 'X', 'Y', 'B'(oth), in which case the same
      acceleration output will be applied to all locations, 
      OR it can be a list of strings with same length as locations, where 
      each location will be applied a different out_type.

  nodes : datafrmame
      Dataframe with node information where acc outputs will added
      Generally created by "geometry.py"
      At a minimum, must include: ['x', 'y']
      
  Returns
  -------
  nodes : dataframe
      Returns the same dataframe, except with a new column: ['OUT']

  Notes
  -----
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
  ndpt = len(nodes)
  OUT = 0 * np.ones(ndpt)
  out_types_opts = {'X': 1, 'Y':2, 'B':2, 'x': 1, 'y':2, 'b':2}
  
  # Turn out_type into list if it is not one
  if not isinstance(out_type, list):
    out_type = [out_type] * len(locations)

  # Iterate through provided locations:
  for loc, out in zip(locations, out_type):
    loc_mask = get_mask([loc], nodes) # Get mask of where to apply out_type
    out_int = out_types_opts[out]           # Get int corresponding to out_type 
    OUT[loc_mask] = out_int                 # Apply to array
  
  # Add results to nodes dataframe and return
  nodes['OUT'] = OUT
  return nodes


def add_str_outputs(locations, out_type, elems):
  ''' Adds stress output options at nodes for QUAD4M analyses.
      
  Purpose
  -------
  This adds a column 'LSTR' to the nodes dataframe, that determines locations
  where stress time histories will be printed after a QUAD4M analyses.

  Parameters
  ----------
  locations : list of touples
      Each element is a touple with: (horz, vert, ij_or_dec, out_type)
      that dictates where and which output accelerations will be printed.
      
      horz : horizontal location where accelerations should be printed
             if ij: must be "i" of node number (or be 'all')
             if dec:ratio from the left and rightwards
                    (0 = left corner, 1 = right corner, 0.5 = center, or 'all')
                
      vert : vertical location where accelerations should be printed
             if ij: must be "j" of node number (or be 'all')
             if dec: ratio from the bottom and upwards
                     (0 = bott corner, 1 = top corner, 0.5 = center, or 'all')
      
      ij_or_dec : either 'ij' or 'dec', determines how horz and vert are read
                   if 'ij'  : horz and vert must be node numbers.
                   if 'dec' : horz and vert must be ratio of domain

  out_type : str
      Type of stress to output. Can be a single string, or a list of strings 
      of same length as locations.

      Must be one of the following:
        'SX'     : 1 (SIGMA_X)
        'SY'     : 2 (SIGMA_Y)
        'TXY'    : 4 (TAU_XY)
        'SX_SY'  : 3 (SIGMA_X AND SIGMA_Y)
        'SX_TXY' : 5 (SIGMA_X AND TAU_XY)
        'SY_TXY' : 6 (SIGMA_Y AND TAU_XY)
        'all'    : 7 (SIGMA_X AND SIGMA_Y AND TAU_XY)

  elems : datafrmame
      Dataframe with element information where stress outputs will added
      Generally created by "geometry.py"
      
  Returns
  -------
  elems : dataframe
      Returns the same dataframe, except with a new column: ['LSTR']

  Notes
  -----
  * From QUAD4MU manual:
      1 - sigma x
      2 - sigma y
      4 - tau xy

  Refs
  ----
    (1) Hudson, M., Idriss, I. M., & Beikae, M. (1994). User’s Manual for
        QUAD4M. National Science Foundation.
            See: Fortran code describing inputs (Pg. A-5)
  '''

  # Initialize array of output options (0 = no output)
  nelm = len(elems)
  LSTR = 0 * np.ones(nelm) # 0 = No output
  lstr_types_opts = {'SX':1, 'SY':2, 'TXY':4, 'SX_SY':3, 'SX_TXY':5, 'SY_TXY':6,
                     'all':7, 'ALL':7}
  
  # Turn out_type into list if it is not one
  if not isinstance(out_type, list):
    out_type = [out_type] * len(locations)

  # Iterate through provided locations:
  for loc, out in zip(locations, out_type):
    # Get mask of where to apply out_type
    # (it being elems instead of nodes doesn't matter for get_mask funct.)
    loc_mask = get_mask([loc], elems) # Get mask of where to apply out_type
    lstr_i = lstr_types_opts[out]           # Get int corresponding to out_type 
    LSTR[loc_mask] = lstr_i                 # Apply to array
  
  # Add results to nodes dataframe and return
  elems['LSTR'] = LSTR
  return elems

def add_ini_xl(locations, value, elems):
  ''' Very simple function: adds column "XL" to elems where all are "value".
  
  This function is written to keep format as other properties.... can't
  see why we would have to add different init value for different elements,
  so keeping it simple, but adding a placeholder in case some other features
  need to be added later on.  

  Locations needs to be 'all'; otherwise exception will be raised.
  '''

  if locations != 'all':
    mssg = ''' Locations should be all... XL was assumed to be the same for all
               elements. If you now have a reason for initializing different 
               values, you'll have to code it in. Sorry! '''
    raise Exception(mssg)

  elems['XL'] = value

  return elems

def add_ini_conds(locations, ics, nodes):
  ''' Adds initial conditions to nodes (disp, vel, acc). 
      
  Purpose
  -------
  Adds initial conditions (disp, vel, acc) given by *ics* to *nodes* as given
  by *locations*. 
      
  Parameters
  ----------
  locations : list of touples
      Each element is a touple with: (horz, vert, ij_or_dec, out_type)
      that dictates which nodes apply to given value.
      
      horz : horizontal location where accelerations should be printed
             if ij: must be "i" of node number (or be 'all')
             if dec:ratio from the left and rightwards
                    (0 = left corner, 1 = right corner, 0.5 = center, or 'all')
                
      vert : vertical location where accelerations should be printed
             if ij: must be "j" of node number (or be 'all')
             if dec: ratio from the bottom and upwards
                     (0 = bott corner, 1 = top corner, 0.5 = center, or 'all')
      
      ij_or_dec : either 'ij' or 'dec', determines how horz and vert are read
                   if 'ij'  : horz and vert must be node numbers.
                   if 'dec' : horz and vert must be ratio of domain
      
  ics : list of numpy arrays
      Each element should by a (1, 6) array containing the initial conditions
      for the node. The length of the list should be same as length of locations
      since both will be iterated through together.      

  nodes : datafrmame
      Dataframe with node information where acc outputs will added
      Generally created by "geometry.py"

  Returns
  -------
  nodes : datafrmame
      Outputs same dataframe, but with new columns: 
       ['X2IH','X1IH','XIH','X2IV','X1IV','XIV']

  Refs
  ----
    (1) Hudson, M., Idriss, I. M., & Beikae, M. (1994). User’s Manual for
        QUAD4M. National Science Foundation.
            See: Fortran code describing inputs (Pg. A-5)
  '''

  # Initialize array of output options (0 = no output)
  ndpt = len(nodes)
  params = ['X2IH', 'X1IH', 'XIH', 'X2IV', 'X1IV', 'XIV']
  INITARR = np.zeros((ndpt, len(params)))

  for loc, ic in zip(locations, ics):
    loc_mask = get_mask(loc, nodes) # Get mask of where to apply out_type
    INITARR[loc_mask, :] = ic                # Apply boundary conditions
  
  # Add results to nodes dataframe and return
  nodes[params] = INITARR
  return nodes


def add_uniform_props(properties, elems):
  ''' TODO-asap: document this'''

  if 'layer' not in list(elems):
    raise Exception('Add layering to elems before adding properties')
  
  layers = elems['layer'].values
  
  for i in np.unique(layers):
    properties_for_layer = properties[int(i)] 
    mask = layers == i
    for prop,val in properties_for_layer.items():
      elems.loc[mask, prop] = val

  return elems


def add_watertable(j, elems, unitw_water = 9807):
  ''' Accounts for watertable to unit weights.
      (ALL THIS DOES IS DO GAMMA_BELOW_WATER = GAMMA - GAMMA_WATER).
      i : float | first element that is fully submerged
      AS USUAL, THIS ASSUMES i IS NUMBERED FROM THE BOTTOM UP. 
  '''
  # Quick error check
  if 'j' not in list(elems):
    raise Exception('Need elements j in elems to add water table')
  if 'unit_w' not in list(elems):
    raise Exception('Need unit_w in elems to add water table')

  # Detrmine where water will be
  diff_gamma = np.zeros(len(elems))
  mask = (elems['j'].values) <= j
  diff_gamma[mask] = unitw_water

  # Add water effects 
  old_gamma = elems['unit_w'].values
  new_gamma = old_gamma - diff_gamma
  elems['unit_w'] = new_gamma

  return elems


# ------------------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------------------

def get_mask(locations, nodes):
  ''' Determines nodes mask of where locations is met
      
  Purpose
  -------
  Given a list of locations, this function will return A SINGLE MASK, that 
  specifies nodes that meet conditions for ANY OF THE locations specified.
      
  Parameters
  ----------
  locations : list of touples
      Each element is a touple with: (horz, vert, ij_or_dec)
      that dictates which nodes are to be included in mask.
      Any node that meets conditions of *any* one location will be included.
      
      horz : horizontal location where accelerations should be printed
             if ij: must be "i" of node number (or be 'all')
             if dec:ratio from the left and rightwards
                    (0 = left corner, 1 = right corner, 0.5 = center, or 'all')
                
      vert : vertical location where accelerations should be printed
             if ij: must be "j" of node number (or be 'all')
             if dec: ratio from the bottom and upwards
                     (0 = bott corner, 1 = top corner, 0.5 = center, or 'all')
      
      ij_or_dec : either 'ij' or 'dec', determines how horz and vert are read
                   if 'ij'  : horz and vert must be node numbers.
                   if 'dec' : horz and vert must be ratio of domain

      out_type : type of acceleration to output. [ 'X', 'Y', 'B'(oth) ]

  nodes : datafrmame
      Dataframe with node information where acc outputs will added
      Generally created by "geometry.py"
      At a minimum, must include: ['x', 'y']
      NOTE THAT THIS CAN ACTUALLY BE NODES OR ELEMS... 

  Returns
  -------
  masks : list of numpy arrays
      list of masks, where each element is a mask of length len(nodes), 
      specifying whether each node is to be included in location.
  '''

  # Determine if dataframe provided is nodes or elems, and change keys appr.
  coord_cols = ['x', 'y']

  if not set(coord_cols).issubset(list(nodes)):
    coord_cols = ['xc', 'yc']
    
    if not set(coord_cols).issubset(list(nodes)):
      mssg = '''Cannot determine if nodes or elems... fix!!!
                Should have either 'y' or 'yc' in columns '''
      raise Exception(mssg)
  
  # Note that from now on, I refer to "nodes", even though it could be "elems"
  ndpt = len(nodes)

  # Iterate through provided locations:
  one_location_masks = []
  for horz, vert, ij_or_dec in locations:

    # First do X mask, then Y mask, then combine using AND logical
    xy_masks = []
    
    for coord_type, coord in zip(coord_cols, [horz, vert]):

      # If user specified 'all', then everywhere
      if coord == 'all':
        xy_masks += [ True * np.ones(ndpt) ]
      
      # If i or j is given, just find where a match occurs
      elif ij_or_dec == 'ij':
        xy_masks += [ nodes[coord_type] == coord ] 

      # Otherwise, find the closest match to the provided ratio
      elif ij_or_dec == 'dec':
        values  = nodes[coord_type] # List of coordinates (x then y)

        # Find the exact coordinate the user asked for (based on coord="ratio") 
        target  = np.min(values) + coord * (np.max(values)-np.min(values))
        
        # Find the closest match in the mesh to the calculated target
        closest = values [np.argmin((values - target)**2)] 

        # Return a mask for the locations that are closest to the target
        xy_masks += [ values == closest ]
     
    # Combine x and y requirements using AND logical operator
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