''' Automate populating element properties for QUAD4M analyses

DESCRIPTION:
This module contains functions that help populate element properties for QUAD4M
analysis, generally adding columns to the dataframe "elems" that then gets 
exported to a ".q4r" file.

'''
import llgeo.props_nonlinear.darendeli_2011 as q4m_daran
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
    if 'unit_w_eff' not in list(elems):
        elems['unit_w_eff'] = unit_w * np.ones(len(elems))

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
        gs = np.flip(soil_col['unit_w_eff'].to_numpy())

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


def add_vs(nodes, elems, pfits, U_rf = None, cov = False,
           unit_fix = True, unit_w = 21000):
  ''' Adds shear-wave velocity based on power-fits and possible random field.
      
  Purpose
  -------
  Given the geometry information of the QUAD4M analysis (nodes and elems), this
  function adds Vs based on the following:
    1) pfits: which provides the best-fit relationship between depth and vs,
              possibly as a function of layering.
    2) U_rf:  a STANDARD UNIFORM random field to add a randomness component.
      
  Parameters
  ----------
  nodes : pandas dataframe
      Contains information for elements, usually created by 'geometry.py'
      At a *minumum*, must have columns: [node_i]

  elems : pandas DataFrame
      Contains information for elements, usually created by 'geometry.py'
      At a *minumum*, must have columns: [i, xc, yc, layer]

  pfits : list of dict
      Each elements correspond to a powefit between depth and vs specific to a
      given soil layer.
      
      The number of elements in this list must be equal to the unique number of
      layers specified in elems['layer'], where these will be mapped as:
          layer number = (index of pfits + 1) since layer number is assumed to
          be 1-indexed but python is 0-indexed. 
      
      Each dict must, at a minimum, have the keys: 'power', 'const' and 'plus',
      with this function assuming a form: vs = plust + const * depth ** power.

  U_rf : bool or numpy array (optional)
      If provided, this must be a STANDARD UNIFORM RANDOM FIELD to introduce
      randomness in the shear wave velocity measurements. Defaults to None,
      so that no randomness is added to the estimated shear wave velocity.

  cov : bool or float (optional)
      If provided, this is a single value representing coefficient of variation
      to be used (will only be used if an U_rf is also provided.). If one is not
      provided yet U_rf is provided, then a column 'cov' must exist in elems
      (this is done so that cov may change spatially, if desired).

  unit_fix : bool
      If true, Gmax will be divided by 1,000 since QUAD4M works in those units

  unit_w : optional
      If elems does not already have a 'unit_w' column, then a single value
      "unit_w" will be used for all the elements. Defaults to 21,000 N/m3.
      
  Returns
  -------
  elems : dataframe
      Returns same dataframe but with "Vs_mean" column added.
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

  # Add required columns if there is randomness
  if U_rf is not None:
    elems = map_rf(elems, 'rand_U', U_rf)
    elems['vs_mean'] = np.empty(len(elems)) 
    elems['vs_rand'] = np.empty(len(elems))

  # If a single coefficient of variation is provided, add it to elems
  if cov:
    elems['cov'] = cov * np.ones(len(elems))

  # Raise error if rf is given, no cov is given, and/or does not exist in elems
  if (U_rf is not None) & (not cov) & ('cov' not in list(elems)):
    raise Exception('If cov is provided, a cov column must exist in elems.')

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
    vs_mean = np.array([c*d**power+plus for c, d, power, plus in
                        zip(consts, ds, powers, pluss)])

    # If there is no randomness, add results
    elems.loc[elems['i'] == i, 'depth'] = ds
    
    # If there is no randomness, just add vs_mean and Gmax
    if U_rf is None:
      Gm = (gs/9.81) * (vs_mean**2)

      # Export results
      elems.loc[elems['i'] == i, 'vs']    = vs_mean
      elems.loc[elems['i'] == i, 'Gmax']  = Gm

    # Otherise, add the randomness here
    else:
      # Get the random component and the final one, then calc Gmax
      vs_rand  = (soil_col['rand_U'].values) * vs_mean * (soil_col['cov'].values)
      vs_final = vs_mean + vs_rand 
      Gm = (gs/9.81) * (vs_final**2)

      # Export results
      elems.loc[elems['i'] == i, 'vs_mean'] = vs_mean
      elems.loc[elems['i'] == i, 'vs_rand'] = vs_rand
      elems.loc[elems['i'] == i, 'vs']      = vs_final
      elems.loc[elems['i'] == i, 'Gmax']    = Gm

  # Fix units if necessary
  if unit_fix:
    elems['Gmax'] = elems['Gmax'] / 1000
  
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


def add_ini_xl(elems, curves, target, target_type):
  ''' Adds initial strain and G for QUAD4M analyses.
      
  Purpose
  -------
  This populates the initial strain and G to be used in QUAD4M analyses. It 
  takes in a "target", which can be either:
      1) Integer to index modulus red curve (target_type = "idx").
      2) Target strain level (target_type = "perc"). ~ no interpolation

  This then assigns the appropriate G and XL for each element given their 
  specified soil number.
      
  Parameters
  ----------
    elems : dataframe
      Contains element information. At a minimum here, it must include:
        [s_num, Gmax]
        IMPORTANT! s_num is assumed to be 1-indexed (as it should be)
      
    curves : list of dict
      Each list element corresponds to one curve, and contains soil number,
      description, and G/Gmax and damping curves.

    target : int or float
      Specifies which values from "curves" to initialize.
      Can be one of two types:

      1) Integer to index curves. THIS IS ZERO-INDEXED!
         (Ex: if target = 2, then the third element in curves will be used to
         initialize XL and G) 
         Here, target_type = 'idx'

      2) Float as percentage strain to target. Note that this funciton will not
         interpolate, but instead choose the closest available value.
         Here, target_type = 'perc'

    target_type : str
      Specifies the type of target type: 'idx' if target is an integer index
      or 'perc' if target is a percentage level of strain.

  Returns
  -------
  elems : dataframe
      Returns the same dataframe except with two new columns: [XL, G]
            
  Refs
  ----
  (1) Hudson, M., Idriss, I. M., & Beikae, M. (1994). User’s Manual for
      QUAD4M. National Science Foundation.
          See: Fortran code describing inputs (Pg. A-5)
  '''

  # Initalize outputs and extract soil numbers
  XL   = np.empty(len(elems))
  Gred = np.empty(len(elems))
  soil_nums = elems['s_num'].values

  # Iterate through unique soil numbers
  for snum in np.unique(soil_nums):

    # Correction: "curves" is zero indexed, but "soil_nums" is 1-indexed
    # Also need to make sure it is an integer so that it can be an index
    snum = int(snum - 1) # (turn to zero-indexed)

    # Get shear modulus reduction curve
    curve_xl   = curves[snum]['G_strn']
    curve_gred = curves[snum]['G_mred']

    # Get index based on target type; raise error if not understood
    if target_type == 'idx':
      idx = int(target)

    elif target_type == 'perc':
      idx = np.argmin((curve_xl - target)**2)

    else:
      mssg  = 'Error in initializing XL and G. Target type not understood.'
      mssg += 'Must either be "idx" or "perc". Please read function docs.'
      raise Exception(mssg)

    # Add initialized values
    mask = (elems['s_num'] == snum + 1) # CORRECT FOR 1 INDEXED
    XL[mask] = curve_xl[idx]
    Gred[mask] = curve_gred[idx]

  # Add results to the elems dataframe and return
  elems['XL'] = XL
  elems['G'] = elems['Gmax'].values * Gred # G = Gmax * Gred

  return elems


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
  elems['unit_w_eff'] = new_gamma

  return elems


def add_darendeli_curves(elems, dec = 0, min_Gred = False):
    ''' Generate Darendeli soil reduction curves and soil numbers.
        
    Purpose
    -------
    Given the elems dataframe, this creates darendeli curves with the mean 
    stress, plasticity index, and overconsolidation ratio. It will create 
    curves for unique combinations of these parameters, ROUNDED to "dec" decimal
    places. THIS ASSUMES STRESS IS GIVEN IN PASCALS, AND TRANSFORMS TO ATM.
        
    Parameters
    ----------
    elems : dataframe
        Contains element information. At a minimum, the following cols must 
        exist: ['PI', 'OCR', 'sigma_m']. This assumes sigma_m is in pascals 
        and transforms it to atm for the darendeli curves.
        
    dec : int
        Number of decimal places to use when rounding parameters, which will
        then be used to get unique combinations of parameters, to avoid 
        creating duplicate curves.

    min_Gred : float
        Will put a minimum on the shear modulus reduction curves, so that 
        it does not go to very low numbers at large strains. (CAREFUL!!!)
        
    Returns
    -------
    curves : list of dict
        Each list element corresponds to one curve, and contains soil number,
        description, and G/Gmax and damping curves.

    elems : dataframe
        Returns input dataframe except with added column: 's_num', which corr-
        esponds to the element number (+1) of the corresponding curve in curves. 

    '''
    
    if not set(['PI', 'OCR', 'sigma_m']).issubset(list(elems)):
        mssg = 'Error when adding Darendeli curves to elements:\n'
        mssg+= '   PI, OCRm and sigma_m columns must exist in elems dataframe'       
        raise Exception(elems)
    
    data = elems.loc[:, ['PI', 'OCR', 'sigma_m']].values
    data = np.round(data, dec)
    uniq_data = np.unique(data, axis = 0)
    elems['s_num'] = np.empty(len(elems))

    curves = []
    for i  in range(len(uniq_data)):

        # Assign soil number to the elements dataframe (must be 1-indexed)
        mask = np.where((data == uniq_data[i, :]).all(axis = 1))[0]
        elems.loc[mask, 's_num'] = i + 1 # 1-indexed

        # Inputs for Darendeli curves
        sstrn = np.outer(np.logspace(-4, 0, 5), np.arange(1,10,1)).flatten()
        daran_inputs = {'sstrn' : sstrn,
                        'PI'    : uniq_data[i, 0],
                        'OCR'   : uniq_data[i, 1],
                        'sigp_o': uniq_data[i, 2] / 101325}

        # Generate description of curve
        description = 'PI={:2.0f} OCR={:2.0f} S={:4.2f}atm'.\
                   format(*[daran_inputs[l] for l in ['PI', 'OCR', 'sigp_o']])

        # Get darandeli curves
        Gred, D_adjs = q4m_daran.curves(**daran_inputs)

        # Add minimum cap if one was provided
        if min_Gred:
          Gred[Gred < min_Gred] = min_Gred

        # Arrange in dictionary for output
        curves += [{'S_name': str(i + 1),
                    'S_desc': description,
                    'G_strn': daran_inputs['sstrn'],
                    'G_mred': Gred,
                    'D_strn': daran_inputs['sstrn'],
                    'D_damp': D_adjs}]

    return curves, elems


# ------------------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------------------

def get_mask(locations, elems):
  ''' Determines elements mask of where locations is met
      
  Purpose
  -------
  Given a list of locations, this function will return A SINGLE MASK, that 
  specifies elems that meet conditions for ANY OF THE locations specified.
      
  Parameters
  ----------
  locations : list of touples
      Each element is a touple with: (horz, vert, ij_or_dec)
      that dictates which elems are to be included in mask.
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

  elems : datafrmame
      Dataframe with elems information
      Generally created by "geometry.py"

  Returns
  -------
  masks : list of numpy arrays
      list of masks, where each element is a mask of length len(elems), 
      specifying whether each elem is to be included in location.
  '''

  # Iterate through provided locations:
  nelm = len(elems)
  one_location_masks = []
  for horz, vert, ij_or_dec in locations:

    # First do X mask, then Y mask, then combine using AND logical
    xy_masks = []
    
    # Determine appropriate key to access from nodes
    if ij_or_dec == 'ij':
      coord_lbls = ['i', 'j']
    else:
      coord_lbls = ['xc', 'yc']
    
    for coord_lbl, coord in zip(coord_lbls, [horz, vert]):

      # If user specified 'all', then everywhere
      if coord == 'all':
        xy_masks += [ True * np.ones(nelm) ]
      
      # If i or j is given, just find where a match occurs
      elif ij_or_dec == 'ij':
        xy_masks += [ elems[coord_lbl] == coord ] 

      # Otherwise, find the closest match to the provided ratio
      elif ij_or_dec == 'dec':
        values  = elems[coord_lbl] # List of coordinates (x then y)

        # Find the exact coordinate the user asked for (based on coord="ratio") 
        target  = np.min(values) + coord * (np.max(values) - np.min(values))
        
        # Find the closest match in the mesh to the calculated target
        closest = values [np.argmin((values - target)**2)] 

        # Return a mask for the locations that are closest to the target
        xy_masks += [ values == closest ]
     
    # Combine x and y requirements using AND logical operator
    one_location_masks += [np.all(xy_masks, axis = 0)]

  # Combine across all locations using OR logical operator
  all_locations_mask = np.any(one_location_masks, axis = 0)
  
  return(all_locations_mask)


def map_rf(elems, prop, z):
  ''' Maps a random field array (generated by simLAS) to elems dataframe.
    
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
    raise Exception('\n'.join(err_check))

  # Mapping
  mapped_z = [z[i-1, j-1] for i, j in zip(elems['i'], elems['j'])] 
  elems[prop] = mapped_z

  return elems


def map_rf_check_inputs(elems, prop, z):
  ''' Does some really basic error checking for the inputs to map_rf '''

  # Some (really) basic error checking
  errors = {1: 'Missing i or j in elemes table. Please add.' ,
            2: 'Random field and q4m mesh do not have same num of is and js.'}

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

  # Print out errors
  err_out = [errors[f] for f in err_flags]
  return err_out


