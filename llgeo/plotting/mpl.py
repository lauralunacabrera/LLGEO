''' Functions to customize matplotlib (mpl)

DESCRIPTION:
These functions are used to customize matplotlib and (hopefully) make the pro-
cess of generating quality figures a bit less tedious. It is also created in
hopes of standardizing the way my figures are created to have my own styyyle.

'''

import matplotlib.pyplot as plt
import matplotlib as mpl
from cycler import cycler
from datetime import datetime

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

    [prop_dict.pop(k) for k in checked_keys]
    mpl.rcParams.update(prop_dict)

def set_axprops(ax, prop_dict):
    ''' Changes properties of the axes '''

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


    if 'xaxis_top' in prop_keys:
        checked_keys += ['xaxis_top']
        xaxis_top = prop_dict['xaxis_top']

        if xaxis_top:
            ax.xaxis.set_label_position('top')
            ax.xaxis.tick_top()

    if 'turn_off' in prop_keys:
        checked_keys += ['turn_off']
        turn_off = prop_dict['turn_off'] 

        if (turn_off == 'both') or (turn_off == 'x'):
            ax.get_xaxis().set_visible(False)
        
        if (turn_off == 'both') or (turn_off == 'y'):
            ax.get_yaxis().set_visible(False)


    for key in prop_keys:
        if key not in checked_keys:
            print('WARNING: unrecognized property ' + key)

    return ax


def get_colors(name):
    ''' Color cycles that are commonly used in my figures '''
    
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


def save_figure(fig, fig_path, fig_name, src_name, png_meta = {}, pdf_meta = {}, 
                png_opt = {}, pdf_opt = {}, save_png = True, save_pdf = True):

    ''' Saves matplotlib figure as a PNG and/or PDF at specified location. 
        
    Purpose
    -------
    This saves a figure at the specified location, having the ability to save
    both PNG and PDF versions. A set of default saving options and metadata
    are automatically generated, but these can be overwritten by the user using
    dictionaries.
        
    Parameters
    ----------
    fig : matlpotlib handles
        Figure handles of the figure that is to be saved.
        
    fig_path : str
        Directory where the figure will saved.

    fig_name : str
        Name of the figure WITHOUT EXTENSION! The extensions are added by
        this function (.png and/or .pdf).

    src_name : str
        Name of the Python script that is generating the figure.

    png_meta : dict (optional)
        Dictionary with metadata that will be included in the PNG figure. Keys
        provided will overwrite existing defaults, but other default keys will
        still be included if not replaced.

        Possible keys are:
            Title, Author, Description, Copyright, Software, Source,
            Creation Time, Disclaimer, Warning, Comment
            (For more info see: https://tinyurl.com/d8nx7ye8)
    
    pdf_meta : dict (optional)
        Dictionary with metadata that will be included in the PDF figure. Keys
        provided will overwrite existing defaults, but other default keys will
        still be included if not replaced.

        Possible keys are:
            Creator, Authore, Title, Subject, Keywords, Producer, CreationDate, 
            ModDate, Trapped
            (For more info see: https://tinyurl.com/3hduzhtf)
    
    png_opt : dict (optional)
        Keyword arguments to be passed to matplotlib's save_fig. Keys
        provided will overwrite existing defaults, but other default keys will
        still be included if not replaced.
            
    pdf_opt : dict (optional)
        Keyword arguments to be passed to matplotlib's save_fig. Keys
        provided will overwrite existing defaults, but other default keys will
        still be included if not replaced.
        
    save_png : bool (optional)
        Whether a png should be saved, defaults to True. 

    save_pdf : bool (optional)
        Whether a pdf should be saved, defaults to True.   

    Returns
    -------
        Nada.

    Notes
    -----
    * This is just a custom wrapper for matplotlib's save_fig. Look at that doc!        
    '''

    # Default PNG and PDF metadata
    f_png_meta = {'Title'        : fig_name,
                 'Author'        : 'LauraLuna',
                 'Software'      : 'Python',
                 'Source'        : src_name,
                 'Comment'       : 'Huh... someone is actually reading this!?!',
                 'Creation Time' : datetime.today().strftime("%Y-%m-%d %X")}

    f_pdf_meta = {'Title'        : f_png_meta['Title'],
                 'Author'        : f_png_meta['Author'],
                 'Creator'       : f_png_meta['Software'],
                 'Producer'      : f_png_meta['Source'],
                 'CreationDate'  : f_png_meta['Creation Time']}

    # Update metadata based on user input to get final metadata
    f_png_meta.update(png_meta)
    f_pdf_meta.update(pdf_meta)
    
    # Default saving options
    f_png_opt = {'bbox_inches': 'tight', 'dpi' : 500, 'pad_inches':0,
                 'metadata': f_png_meta}

    f_pdf_opt = {'bbox_inches': 'tight', 'pad_inches':0,
                 'metadata': f_pdf_meta}
    
    # Update default saving options based on user's input to get final options
    f_png_opt.update(png_opt)
    f_pdf_opt.update(pdf_opt)

    # Save figure, in formats requested
    if save_png:
        fig.savefig(fig_path + fig_name + '.png', **f_png_opt)
    
    if save_pdf:
        fig.savefig(fig_path + fig_name + '.pdf', **f_pdf_opt)

     
# ------------------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------------------



#%%