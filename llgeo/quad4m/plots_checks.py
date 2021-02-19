''' one_line_description

DESCRIPTION:
Insert a paragraph-long description of the module here.

FUNCTIONS:
This module contains the following (main) functions:
    * fun_name : one_line_description
                 (only add user-facing ones)

'''
import numpy as np
import matplotlib as mpl
import matplotlib.colors
import matplotlib.collections
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from mpl_toolkits.axes_grid1 import make_axes_locatable


# ------------------------------------------------------------------------------
# Main Functions
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------------------
def plot_mesh(verts, verts_elems, ax, mesh_kwargs = {}):

    # Get default kwargs and update with provided mesh_kwargs
    kwargs = {'edgecolor': 'k', 'linewidth': 0.2}
    kwargs.update(mesh_kwargs)

    # Plot mesh
    pc = mpl.collections.PolyCollection(verts, **kwargs)
    ax.add_collection(pc)
    ax.axis('equal')

    # Return axis handles and polycollection
    return ax, pc




def plot_mesh_node_prop(elems, nodes, prop, units, fig, ax,
                        sc_kwargs = {}):

    # Get vertices and elements in proper format
    verts, verts_elems = get_verts(elems, nodes)

    # TODO



def plot_mesh_elem_prop(elems, nodes, prop, units, fig, ax,
                        colors = False, mesh_kwargs = {}, cb_kwargs = {}):
    ''' Plots filled mesh with colots mapped to values of prop
        
    Purpose
    -------
    Paragraph-long description of function purpose
    State assumptions and limitations. Examples are great.
        
    Parameters
    ----------
    verts : list of list of touples 
        (see get_verts)
        List, where each element is a list of four touples (x, y) that defines
        the coordinates of an element in CCW order.
        
    verts_elems : list of df series
        (see get_verts)
        Each element contains rows from elems dataframe, in the same order as 
        verts.

    prop : string
        Propery to be used for contour colors. Must be in verts_elems

    ax : matplotlib axis handle
        axis handle on which to plot the figure

    kwargs : dict
        key word argumentsfor polycollection (colormap, edgecolor, etc.)
        
    Returns
    -------
    ax : matplotlib axis
        Returns the same axis, but with mesh added
                
    '''

    # Get vertices and elements in proper format
    verts, verts_elems = get_verts(elems, nodes)

    # Make sure that the property exists in elems
    if prop not in verts_elems[0].index.to_list():
        msg = 'Error in plotting mesh of '+ prop + '\n'
        msg+= 'the property does not exist in elems dataframe'    
        raise Exception(msg)

    # Get values from "verts_elems"
    vals = np.array([float(elem[prop]) for elem in verts_elems])

    # Outline color schemes (either discrete or continuous color maps)
    if colors:
        # Make sure colors are in RBG
        colors = [matplotlib.colors.to_rgba(c) for c in colors]
        unique_vals = np.sort(np.unique(vals))
        facecolors = []

        for v in vals:
            i = np.where(v == unique_vals)[0][0]
            idx = int(i % len(colors))
            facecolors += [colors[idx]]

        mesh_kwargs.update({'facecolors' : facecolors})
    
    else:
        mesh_kwargs.update({'array' : vals, 'edgecolor': 'k', 'linewidth':0.02})

 
    ax, pc = plot_mesh(verts, verts_elems, ax, mesh_kwargs)

    # Add colorbar 
    # TODO - fix this for discrete colors
    kwargs = {'visible': True, 'orientation':'horizontal',
              'ticklocation':'bottom'}
    kwargs.update(cb_kwargs)

    if kwargs['visible']:
        del kwargs['visible']
        divider = make_axes_locatable(ax)
        cax = divider.append_axes('bottom', size = '5%', pad = '2%')
        cb  = plt.colorbar(pc, cax = cax, **kwargs)
                
        # Colorbar plotting options
        cax.xaxis.set_major_locator(ticker.MaxNLocator())
        cb.outline.set_visible(False)
        cb.ax.tick_params(labelsize = 7, width = 0.1)
        cb.set_label(prop + ' (' + units + ')', fontsize = 7)
    else:
        cax = None
    
    # Plotting options
    ax.set_xbound(lower = np.min(nodes['x']), upper = np.max(nodes['x']))
    ax.set_ybound(lower = np.min(nodes['y']), upper = np.max(nodes['y']))
    ax.axis('off')
    ax.axis('equal')

    return fig, ax, cax


def get_verts(elems, nodes):
    ''' Returns list with element vertices coordinates, and list of elems.
        
    Purpose
    -------
    This function creates a list "verts", where each element is a list of four
    touples that defines the corners of the element. It also returns a list 
    "verts_elems" where each row is an row of the elems dataframe, corresponding
    to the "verts" order. 
        
    Parameters
    ----------
    elems : dataframe
        Information on elements. At a minimum must include:
            ['N1', 'N2', 'N3', 'N4']
        
    nodes : dataframe
        Contains node information. At a minimum, must include:
            ['x', 'y', 'node_n']
        
    Returns
    -------
    verts : list of list of touples 
        List, where each element is a list of four touples (x, y) that defines
        the coordinates of an element in CCW order.
        
    verts_elems : list of df series
        Each element contains rows from elems dataframe, in the same order as 
        verts.
        
    '''

    # Make nodes be index-eable by "node_n" just in case
    nodes_idx = nodes.set_index('node_n')

    # Create list of element vertices and element rows
    verts = []
    verts_elems = []

    for _, elem in elems.iterrows():

        elem_vert = []
        for nx in ['N1', 'N2', 'N3', 'N4']:
            n = int(elem[nx])
            elem_vert += [(nodes_idx.loc[n, 'x'], nodes_idx.loc[n, 'y'])]

        verts += [elem_vert]
        verts_elems += [elem]

    return(verts, verts_elems)