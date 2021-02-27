''' Functions for transforming coordinate systems that I usually work in.

DESCRIPTION:
These help transform different projections. This is very basic... just learning
how to do this stuff now. 

Need to look into these resources:
https://www.earthdatascience.org/

EPGS Explanation:
https://en.wikipedia.org/wiki/EPSG_Geodetic_Parameter_Dataset

'''

import pyproj as proj

# ------------------------------------------------------------------------------
# Main Functions
# ------------------------------------------------------------------------------
def epgs_transform(cfrom, cto, old_x, old_y):
    ''' Transforms coordinates (numpy arrays) to a different coordinate system.

    Commonly used:
        4326  = WGS84 Lat and Long (https://tinyurl.com/3hcylf25) - Everywhere
        26710 = NAD27 UTM Zone 10N (https://tinyurl.com/3lrb9pva) - Vancouver
        32610 = WGS84 UTM Zone 10N (https://tinyurl.com/gdh8zfvy) - Vancouver
    
    TODO - properly document this!
    '''
    
    # Get coordinate reference systems
    cfrom = proj.CRS.from_epsg(cfrom)
    cto   = proj.CRS.from_epsg(cto)

    # Initialize transformer
    transformer = proj.Transformer.from_crs(cfrom, cto)
    
    # Transform! (and return)
    new_x, new_y = transformer.transform(old_x, old_y)
    
    return new_x, new_y


# ------------------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------------------