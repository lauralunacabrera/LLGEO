''' Automate populating nodal properties for QUAD4M analyses

DESCRIPTION:
This module contains functions that help populate nodal properties for QUAD4M
analyses, generally adding columns to the dataframe "nodes" that then gets 
exported to a ".q4r" file.

'''
import numpy as np
import pandas as pd

# ------------------------------------------------------------------------------
# Main Functions
# ------------------------------------------------------------------------------

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
  out_types_opts = {'X': 1, 'Y':2, 'B':3, 'x': 1, 'y':2, 'b':3}
  
  # Turn out_type into list if it is not one
  if not isinstance(locations, list):
    locations = [locations]
    
  if not isinstance(out_type, list):
    out_type = [out_type] * len(locations)

  # Iterate through provided locations:
  for loc, out in zip(locations, out_type):
    loc_mask = get_mask(loc, nodes)    # Get mask of where to apply out_type
    out_int = out_types_opts[out]      # Get int corresponding to out_type 
    OUT[loc_mask] = out_int            # Apply to array
  
  # Add results to nodes dataframe and return
  nodes['OUT'] = OUT
  return nodes


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
  ndpt = len(nodes)

  # If locations is not a list, turn it into one
  if not isinstance(locations, list):
    locations = [locations]

  # Iterate through provided locations:
  one_location_masks = []
  for horz, vert, ij_or_dec in locations:

    # First do X mask, then Y mask, then combine using AND logical
    xy_masks = []
    
    # Determine appropriate key to access from nodes
    if ij_or_dec == 'ij':
      coord_lbls = ['node_i', 'node_j']
    else:
      coord_lbls = ['x', 'y']

    for coord_lbl, coord in zip(coord_lbls, [horz, vert]):

      # If user specified 'all', then everywhere
      if coord == 'all':
        xy_masks += [ True * np.ones(ndpt) ]
      
      # If i or j is given, just find where a match occurs
      elif ij_or_dec == 'ij':
        xy_masks += [ nodes[coord_lbl] == coord ] 

      # Otherwise, find the closest match to the provided ratio
      elif ij_or_dec == 'dec':
        values  = nodes[coord_lbl] # List of coordinates (x then y)

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

