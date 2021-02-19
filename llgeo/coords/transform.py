''' Functions for transforming coordinate systems that I usually work in.

DESCRIPTION:
These help transform different projections. This is very basic... just learning
how to do this stuff now. 

Need to look into these resources:
https://www.earthdatascience.org/

'''
import pyproj as proj

# ------------------------------------------------------------------------------
# Main Functions
# ------------------------------------------------------------------------------
def transform_epsg_xy(cfrom, cto, old_x, old_y):
    ''' Transforms x and y coordinates (numpy arrays) to a different epsg.

    Commonly used:
        26710 = NAD27 UTM Zone 10N (https://tinyurl.com/3lrb9pva)
        32610 = WGS84 UTM Zone 10N (https://tinyurl.com/gdh8zfvy)
    
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