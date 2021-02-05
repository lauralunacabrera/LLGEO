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

def plot_mesh_elem_prop(verts, verts_elem, nodes, prop, units, fig, ax,
                        colors = False, pc_kwargs = {}, cb_kwargs = {}):
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
        
    verts_elem : list of df series
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

    # Make sure that the property exists in elems
    if prop not in verts_elem[0].index.to_list():
        msg = 'Error in plotting mesh of '+ prop + '\n'
        msg+= 'the property does not exist in elems dataframe'    
        raise Exception(msg)

    # Specify default kwargs, but update to provided ones
    kwargs = {'edgecolor': 'k', 'linewidth': 0.05}
    kwargs.update(pc_kwargs)

    # Get velues from "verts_elem"
    vals = np.array([float(elem[prop]) for elem in verts_elem])

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

        kwargs.update({'facecolors' : facecolors})
    
    else:
        kwargs.update({'array' : vals})

    # Add to plot
    pc = mpl.collections.PolyCollection(verts, **kwargs)
    ax.add_collection(pc)
    # ax.axis('equal')
    
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
    "verts_elem" where each row is an row of the elems dataframe, corresponding
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
        
    verts_elem : list of df series
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