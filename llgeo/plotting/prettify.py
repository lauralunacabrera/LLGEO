''' one_line_description

DESCRIPTION:
Insert a paragraph-long description of the module here.

FUNCTIONS:
This module contains the following (main) functions:
    * fun_name : one_line_description
                 (only add user-facing ones)

'''
#%%
import matplotlib.pyplot as plt
import matplotlib as mpl
from cycler import cycler

# ------------------------------------------------------------------------------
# Main Functions
# ------------------------------------------------------------------------------

def set_rcprops(prop_dict):
    ''' Update matplotlib parameters '''
    mpl.rcParams.update(mpl.rcParamsDefault)

    prop_keys = prop_dict.keys()
    checked_keys = []

    if 'llgeo_ccycle' in prop_keys:
        checked_keys += ['llgeo_ccycle']
        colors = get_ccycler(prop_dict['llgeo_ccycle'])
        mpl.rcParams.update({'axes.prop_cycle': colors})


def set_axprops(ax, prop_dict):

    prop_keys = prop_dict.keys()
    checked_keys = []

    if 'xlims' in prop_keys:
        checked_keys += ['xlims']
        xlims = prop_dict['xlims']
        ax.set_xlim(xlims)


    if 'ylims' in prop_keys:
        checked_keys += ['ylims']
        ylims = prop_dict['ylims']
        ax.set_ylim(ylims)


    if 'labels' in prop_keys:
        checked_keys += ['labels']
        xlabel, ylabel = prop_dict['labels']
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)


    if 'major_grid' in prop_keys:
        checked_keys += ['major_grid']
        color = prop_dict['major_grid']
        if not color: color = (0.85, .85, .85)
        ax.grid('major', color = color)
        ax.set_axisbelow(True)


    if 'reverse' in prop_keys:
        checked_keys += ['reverse']
        which = prop_dict['reverse']

        if which not in ['x', 'y', 'both']:
            raise Exception('Reverse property must be "x", "y", or "both"')
        
        if which in ['x', 'both']:
            xmin, xmax = ax.get_xlim()
            ax.set_xlim(xmax, xmin)
    
        if which in ['y', 'both']:
            ymin, ymax = ax.get_ylim()
            ax.set_ylim(ymax, ymin)
                   

    if 'legend' in prop_keys:
        checked_keys += ['legend']
        legend_props = {'loc':6, 'bbox_to_anchor': (1, .5), 'edgecolor':'None',
                        'facecolor':'None'}
        given_props  = prop_dict['legend']

        if given_props:
            legend_props.update(given_props)

        ax.legend(**legend_props)


    for key in prop_keys:
        if key not in checked_keys:
            print('WARNING: unrecognized property ' + key)

    return ax


def get_colors(name):
    
    llgeo_colors = {

    'dutch' : ['#FFC312', '#F79F1F', '#EE5A24', '#EA2027', '#C4E538', '#A3CB38',
               '#009432', '#006266', '#12CBC4', '#1289A7', '#0652DD', '#1B1464',
               '#FDA7DF', '#D980FA', '#9980FA', '#5758BB', '#ED4C67', '#B53471',
               '#833471', '#6F1E51']
    }

    return llgeo_colors[name]

def get_ccycler(name):
    out_cycler = cycler(color = get_colors(name))
    return out_cycler 


def save_figure(fig, fig_path, fig_file, title, change_metadata):
    ''' Saves figure as png and pdf at specified location with metadata.
        
    Parameters
    ----------
    fig : figure handle

    fig_path + fig_file : strings indicating where the file should be saved

    title : description of figure

    change_metadata : dictionary to overwrite the following defaults: 
                      {Author : LauraLuna, Software : Python3, 
        
    Returns
    -------
    None
    '''

# ------------------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------------------



#%%