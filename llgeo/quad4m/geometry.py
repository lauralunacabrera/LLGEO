''' Automate the generation of QUAD4M model geometry

DESCRIPTION:
This module contains functions that help automize the geometry processing for
QUAD4M analyses. These functions transform a DXF file to Pandas dataframes with
node and elemen info for QUAD4M. 

THIS MODULE ASSUMES VERTICAL SOIL COLUMNS!!

MAIN FUNCTIONS:
This module contains the following functions:
    * dxf_to_dfs
    * dfs_to_dxf
    * get_geom_summary
'''

# ------------------------------------------------------------------------------
# Import Modules
# ------------------------------------------------------------------------------
import numpy as np
import pandas as pd
import ezdxf as ez
import warnings

warnings.simplefilter('default')
warnings.filterwarnings('ignore', category = DeprecationWarning)

# ------------------------------------------------------------------------------
# Main Functions
# ------------------------------------------------------------------------------
def dxf_to_dfs(in_path, in_file, lay_id = 'soil_', dec = 4):
    ''' returns node and element dataframes from DXF file (for QUAD4M).
    
    Purpose
    -------
    Given a DXF path and file name, it returns two DataFrame tables: one with
    node information and one for element information.
    
    Parameters
    ----------
    in_path : str
        path to directory containing DXF file of interest
    
    in_file : str
        name of DXF file to be processed
    
    lay_id : str
        DXF layers to be processed must include this string in their name.
        Defaults to "soil_"
    
    dec : int
        number of decimals to round coordinates to (defaults to 4 if none given)
        
    Returns
    -------
    nodes : pandas DataFrame
        DataFrame with information for nodes: [n, i, j, x, y]
    
    elems : pandas DataFrame
        DataFrame with information for elemnts.
        Nodes are number starting from low left corner and counterclockwise.
        Contents of DataFrame are as follows:
        [elem_n, elem_i, elem_j, elem_t, elem_soil, xc, yc, N1, N2, N3, N4]    
        
    Notes
    -----
    * Elements must all be LWPOLYLINES. No other obejcts will be examined.
    * Only works for vertical soil columns attached horizontally
    '''
    
    # Get DXF model space
    doc = ez.readfile(in_path + in_file)
    msp = doc.modelspace()
    
    # Get soil layers of interst
    soil_layers = [layer.dxf.name for layer in doc.layers
                   if lay_id in layer.dxf.name]

    # Raise exception if no layers match lay_id
    if len(soil_layers) == 0:
        raise Exception('Geometry: no layers in DXF contain lay_id')
        
    # Find polylines in msp and query by layer
    lines_by_layer = msp.query('LWPOLYLINE').groupby('layer') #dict keys=layer
    
    # Extract polylines that are saved in soil layers
    soil_lines = []

    for lay in soil_layers:
        # Warn the user if there is a soil layer that doesn't have polylines
        if lay not in lines_by_layer.keys():
            message = 'No LWPOLYLINES in DXF layer ' + lay
            warnings.showwarning(message,
                                 category = UserWarning,
                                 filename = 'geometry.py',
                                 lineno   = '') 
            continue

        # Otherwise, extract polylines in the layer
        else:
            soil_lines += lines_by_layer[lay]

    # Get node information
    nodes = get_nodes_df(soil_lines, dec)
    
    # Get element information
    elems = get_elems_df(soil_lines, nodes, dec, lay_id)

    return(nodes, elems)
    
    
def dfs_to_dxf(out_path, out_file, nodes, elems, elems_add_col = 0):
    ''' Given node and element dfs, prints labelled mesh to DXF file as a check.
    
    Purpose
    -------
    Given node and element dfs, prints labelled mesh to DXF file. This is done
    to check that all information was processed correctly.
    
    Parameters
    ----------
    out_path : str
        Path to directory where output DXF will be saved

    out_file : str
        Name of DXF file to store outputs

    nodes : pandas DataFrame
        DataFrame with information for nodes: [n, i, j, x, y]

    elems : pandas DataFrame
        DataFrame with information for elemnts.
        Nodes are number starting from low left corner and counterclockwise.
        Contents of DataFrame are as follows:
        [elem_n, elem_i, elem_j, elem_t, elem_soil, xc, yc, N1, N2, N3, N4]    
    
    elems_add_col : str
        Must correspond to a column in elems dataframe. If passed, it will add 
        the values in the column as text onto the DXF. Defaults to 0, so no 
        extra information is printed. (Used mostly to ensure random field 
        mapping was done correctly). 
        
    Returns
    -------
    Nothing is returned driectly - simply creates DXF file
        
    Notes
    -----
    * IF DXF FILE ALREADY EXISTS, MAKE SURE THAT THE FILE IS CLOSED!!
    '''
    
    # Create new drawing and get model space
    dwg = ez.new(dxfversion = 'R2004')
    msp = dwg.modelspace()
    
    # Add needed layers
    lays = ['Geometry', 'Elem_Geom', 'Elem_Info', 'Node_Geom']
    clrs = [1, 2, 3, 4]

    if elems_add_col:
        lays += ['Extr_Info']
        clrs += [6]

    [dwg.layers.new(name=n, dxfattribs={'color':c}) for n, c in zip(lays, clrs)]
    
    # Loop through elements and draw them
    for _, elem in elems.iterrows():

        # Draw mesh lines
        masks = [nodes['node_n'] == elem[s] for s in ['N1','N2','N3','N4','N1']]
        points = [(float(nodes.loc[m, 'x']), float(nodes.loc[m, 'y']))
                  for m in masks]
        msp.add_lwpolyline(points, dxfattribs={'layer': 'Geometry'})

        # Draw labels for elem_n, elem_i, and elem_j
        label = '{:d} ({:d}, {:d})'.format(elem['n'], elem['i'], elem['j'])
        props = {'layer': 'Elem_Geom', 'height': 0.05}
        pos   = (- 0.2 + elem['xc'], - 0.05 + elem['yc'])
        msp.add_text(label, dxfattribs = props).set_pos(pos)

        # Draw labels for soil type and element type
        label = elem['s'] + '_' + elem['t']
        props = {'layer': 'Elem_Info', 'height': 0.05}
        pos   = (- 0.2 + elem['xc'], + 0.05 + elem['yc'])
        msp.add_text(label, dxfattribs=props).set_pos(pos)

        # If requested, draw additional info at element centers
        if elems_add_col:
            label = elem[elems_add_col]
            props = {'layer': 'Extr_Info', 'height': 0.05}
            pos   = (- 0.2 + elem['xc'], - 0.15 + elem['yc'])
            msp.add_text(label, dxfattribs = props).set_pos(pos)
            
    # Loop through nodes and draw them
    for _, node in nodes.iterrows():
        label = '{:02.0f} ({:02.0f}, {:02.0f})'.format(node['node_n'],
                                                       node['node_i'],
                                                       node['node_j'])
        props = {'layer': 'Node_Geom', 'height': 0.03}
        pos   = (node['x'] + 0.02, node['y'] + 0.02)
        msp.add_text(label, dxfattribs = props).set_pos(pos)
            
    # Save and return
    dwg.saveas(out_path + out_file)


def get_mesh_sizes(nodes, elems):
    ''' Gets mesh size: width, height, number of elems, average elem size.
        
    Purpose
    -------
    Given node and elems dataframes, this determines:
        * Height and width of the overall mesh
        * Number of elements in the mesh
        * The average element width and element height
        
    Parameters
    ----------
    nodes : pandas DataFrame
        DataFrame with information for nodes.
        Here it must contain, at a minimum:
            [node_n, x, y]
    
    elems : pandas DataFrame
        DataFrame with information for elemnts.
        Nodes are number starting from low left corner and counterclockwise.
        Here it must contain, at a minimum:
            [N1, N2, N3, N4]    
       
    Returns
    -------
    mesh_w : float
        Maximum width of the model (max x_coord - min x_coord)

    mesh_h : float
        Maximum height of the model (max y_coord - min y_coord)
    
    nelm : int
        Number of elements in the mesh

    elem_w : float
        Average width of the elements in the mesh
 
    elem_h : float
        Average height of the elements in the mesh

    '''

    # Get mesh width. height, and number of elements
    mesh_w = np.ptp(nodes['x']) # ptp = point to point (max - min)
    mesh_h = np.ptp(nodes['y'])
    nelm   = len(elems)
    elem_w = np.average(elems['w'])
    elem_h = np.average(elems['h'])

    return mesh_w, mesh_h, nelm, elem_w, elem_h


# ------------------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------------------
def get_nodes_df(lines, dec):
    ''' gets node dataframe from list of LWPOLYLINES
    
    Purpose
    -------
    Given a list of LWPOLYLINES, returns DataFrame with nodal coordinates.
    This is to be used later in QUAD4M models.
    
    Parameters
    ----------
    lines : list of LWPOLYLINES
        lines containing coordinates to be extracted
    dec : int
        number of decimal places to incude in coordinate table
        
    Returns
    -------
    nodes : pandas DataFrame
        DataFrame with information for nodes: [n, i, j, x, y]
        
    Notes
    -----
    * Elements must all be LWPOLYLINES. No other obejcts will be examined.
    * Only works for vertical soil columns attached horizontally
    '''
    
    xy = get_node_coords(lines, dec)
    unique_x = np.sort(np.unique(xy[:, 0]))

    # Create DataFrame structure
    cols = ['node_n', 'node_i', 'node_j', 'x', 'y']
    nodes = pd.DataFrame([], columns = cols)
    
    # Loop through each soil column:
    for i in np.arange(0, len(unique_x)):
        
        # Get x and y coordinates for column i
        mask = xy[:,0] == unique_x[i]
        col_x = xy[mask, 0]
        col_y = xy[mask, 1]
        
        # Sort from bottom to top
        order = np.argsort(col_y)
        col_x = col_x[order]
        col_y = col_y[order]
        
        # Number the nodes (1-indexed for QUAD4M!!!)
        node_n = 0 * np.ones(np.shape(col_x)) # Placeholder - replaced later
        node_i = 1 + i * np.ones(np.shape(col_x), dtype = int)
        node_j = 1 + np.arange(0, len(col_x))
        
        # Append results to nodes DataFrame
        new = np.stack([node_n, node_i, node_j, col_x, col_y], axis = 1)
        new = pd.DataFrame(new, columns = cols)
        nodes = nodes.append(new, ignore_index = True)
        
    # Number nodes (1-indexed for QUAD4M!!!)
    nodes['node_n'] = 1 + np.arange(0, len(nodes))

    return(nodes)

    
def get_elems_df(lines, nodes, dec, lay_id):
    ''' gets element dataframe from list of LWPOLYLINES and nodes DataFrame
    
    Purpose
    -------
    Given a list of LWPOLYLINES and a nodes DataFrame, returns DataFrame with
    element information.
    
    Parameters
    ----------
    lines : list of LWPOLYLINES
        lines containing coordinates to be extracted

    nodes : pandas DataFrame
        DataFrame with information for nodes: [n, i, j, x, y]

    dec : int
        number of decimal places to incude in coordinate table
        
    Returns
    -------
    elems : pandas DataFrame
        DataFrame with information for elemnts.
        Nodes are number starting from low left corner and counterclockwise.
        Contents of DataFrame are as follows:
        ['n', 'i', 'j', 't', 's', 'w', 'h', 'xc', 'yc', 'N1','N2','N3','N4']   
        
    Notes
    -----
    * Elements must all be LWPOLYLINES. No other obejcts will be examined.
    * Only works for vertical soil columns attached horizontally
    '''
    # Columns are: element number, i, j, type (quad or tri), soil, width,
    #              height, x center, y center, node numbers in CCW direction.
    cols = ['n', 'i', 'j', 't', 's', 'w', 'h', 'xc', 'yc', 'N1','N2','N3','N4']
    elems = pd.DataFrame([], columns = cols)

    for k, line in enumerate(lines):
        # Get coordinates within element
        points = line.get_points('xy')
        x = np.round([p[0] for p in points], dec)
        y = np.round([p[1] for p in points], dec) 
        xy = np.stack([x, y], axis = 1)
        xy = np.unique(xy, axis = 0)
        
        # Get element (rough?) center
        xc = np.mean(xy[:, 0])
        yc = np.mean(xy[:, 1])

        # Get CCW ordered coords if element is quadrilateral
        if len(xy) == 4:
            etype = 'quad'
            xy1 = xy[(xy[:, 0] < xc) & (xy[:, 1] < yc), :]
            xy2 = xy[(xy[:, 0] > xc) & (xy[:, 1] < yc), :]
            xy3 = xy[(xy[:, 0] > xc) & (xy[:, 1] > yc), :]
            xy4 = xy[(xy[:, 0] < xc) & (xy[:, 1] > yc), :]
        
        # Get CCW ordered coords if element is triangular 
        elif len(xy) == 3:
            etype = 'tri'
            xy1 = xy[(xy[:, 0] < xc) & (xy[:, 1] < yc), :]
            xy2 = xy[(xy[:, 0] > xc) & (xy[:, 1] < yc), :]
            
            LT = (xy[:, 0] < xc) & (xy[:, 1] > yc)
            RT = (xy[:, 0] > xc) & (xy[:, 1] > yc)

            if sum(LT) > 0:
                xy3 = xy[LT, :]
                xy4 = xy[LT, :]
            if sum(RT) > 0:
                xy3 = xy[RT, :]
                xy4 = xy[RT, :]

        # If not quad or tri, print error and continue
        else:
            print('Unknown element type - check {:i}'.format(k))
            continue

        # Determine approximate width
        width_bot = xy2[0, 0] - xy1[0, 0]
        width_top = xy3[0, 0] - xy4[0, 0]
        w = (width_bot + width_top) / 2

        # Determine approximate height
        height_left  = xy4[0, 1] - xy1[0, 1]
        height_right = xy3[0, 1] - xy2[0, 1]
        h = (height_left + height_right) / 2

        # Get node numbers, i and j
        Ns = []
        for one_xy in [xy1, xy2, xy3, xy4]:
            dfmask = (nodes['x'] == one_xy[0,0]) & (nodes['y'] == one_xy[0,1])
            Ns.append(int(nodes.loc[dfmask, 'node_n']))

        # Get element i, j, s
        n = 0 # will get filled later
        i = int(nodes.loc[nodes['node_n'] == Ns[0], 'node_i'])
        j = int(nodes.loc[nodes['node_n'] == Ns[0], 'node_j'])
        s = line.dxf.layer.replace(lay_id, '') #(remove layer id; easier read)

        # Export outputs
        out = pd.DataFrame([[n,i,j,etype,s,w,h,xc,yc]+Ns], columns = cols)
        elems = elems.append(out, ignore_index = True)
    
    # Sort for easier handling, populate element numbers, and return
    elems = elems.sort_values(by = ['j', 'i']) # F-ordered (column major)
    elems['n'] = 1 + np.arange(0, len(elems))  # 1-indexed!!!
    elems.reset_index(inplace = True)
    return(elems)
    
    
def get_node_coords(lines, dec):
    ''' gets node coordinates for a list of LWPOLYLINES
    
    Purpose
    -------
    Given a list of LWPOLYLINES, returns (nx2) np array with x and y coords.
    Will return UNIQUE coordinates rounded to "dec" decimal places.
    
    Parameters
    ----------
    lines : list of LWPOLYLINES
        lines containing coordinates to be extracted
    dec : int
        number of decimal places to incude in coordinate table
        
    Returns
    -------
    xy : numpy float array
        (2 x n) array with coordinates of unique points
        
    Notes
    -----
    * Elements must all be LWPOLYLINES. No other obejcts will be examined.
    
    '''
    # Loop through lines and get coordinates
    all_xy = np.empty((0,2)) # Initialize array

    for line in lines:
        points = line.get_points('xy')
        xy = np.array([[p[0], p[1]]  for p in points])
        all_xy = np.concatenate([all_xy, np.round(xy, dec)], axis = 0)
    
    # Remove duplicates and return
    xy = np.unique(all_xy, axis = 0)
    return(xy)

