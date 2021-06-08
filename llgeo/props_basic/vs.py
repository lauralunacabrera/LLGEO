import numpy as np


def get_vs30(depth_from, depth_to, vs):
    ''' Calculates Vs30 for a given shear wave velocity sounding
        
    Purpose
    -------
    Calculates the average shear wave velocity in the top 30 meters for a given
    shear wave velocity sounding.
        
    Parameters
    ----------
    depth_from : numpy array
        Starting depth interval for the measured shear wave velocity
        
    depth_to : numpy array
        Ending depth interval for the measured shear wave velocity

    vs : numpy array
        Measured shear wave velocity
        
    Returns
    -------
    vs30 : float
        Average shear wave velocity in the top 30 meters, calculated as follows:
        Vs30 = (total thickness of all layers) / sum(layer thickness / layer Vs)
        ^ only for layers within the top 30 meters of soil

    output_name : output_data_type
        Description of the parameter.
        Include assumptions, defaults, and limitations!
        
    Notes
    -----
    * Anything the user should know?
        
    Refs
    ----
    * Include *VERY DETAILED* bibliography. 
      State publications, urls, pages, equations, etc.
      YOU'RE. AN. ENGINEER. NOT. A. CODER.
    '''

    # Make copies of arrays (otherwise modifies original?)
    depth_to30 = depth_to.copy()
    depth_from30 = depth_from.copy()

    # Limit "depth_to" and "depth_from" to 30 meters below ground surface
    lim = 30
    depth_to30[depth_to30 > lim] = lim
    depth_from30[depth_from30 > lim] = lim

    # Calculate layer thickness using "depth_to30"
    # Now, any layers beyond the 30m mark will have zero thickness     
    thickness = depth_to - depth_from

    # Calculate vs30 = (thickness of all layers)/sum(layer thickness/layer vs)
    vs30 = np.sum(thickness) / np.sum(thickness/vs)

    return vs30