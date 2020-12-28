''' Utilities for formatting numbers into strings

DESCRIPTION:
This module contains functions that help turn numbers into strings, mostly 
needed when specific Fotran 70 formats are required.

FUNCTIONS:
This module contains the following functions:
    * arr2str_F70: Converts np array to a string using F70-like formatting.
    * num2str_F70: Converts a number to a string using F70-like formatting.
    
'''
# ------------------------------------------------------------------------------
# Import Modules
# ------------------------------------------------------------------------------

# Standard libraries
import numpy as np

# ------------------------------------------------------------------------------
# Main Functions
# ------------------------------------------------------------------------------

def arr2str_F70(data, cols, width, dec = False):
    ''' Converts np array to a string using F70-like formatting.

    Purpose
    -------
	To easily convert arrays to strings while complying with F70/F90 string
    requirements.

    Example: for '8F10.0' use: cols = 8, width = 10, dec = False
             for 'F5.2'   use: cols = 1, width =  5, dec = 2
    
    Parameters
    ----------
    data : array of floats
        contains data to be transformed to string.

    cols : int
        number of columns in which to organize the data.
    
    width : int
        number of characters that each number in "data" array will occupy. 
   
    dec : int (optional) 
        number of decimals to include. When none passed, defaults to returning
        as many decimals as fit within specified width.
        
    Returns
    -------
    str_out : str
        data transformed into a string based on specified formatting.

    Notes
    -----
    * Careful that the width and decimals specified work for the given data,
      otherwise, functions will raise exceptions.
	* Probably not the smartest way of doing things, but I'm tired and grumpy.
    '''

    # Round to specific decimal palces if required
    if dec: data = np.round(data, dec)

    # Iterate through array, figure out formatting, and concat output string
    str_out = ''

    for i, num in enumerate(data):

        # Add a line break if necessary
        if i % cols == 0:
            str_out += '\n'
        
        str_out += num2str_F70(num, width, dec) 

    return(str_out)


def num2str_F70(num, width, dec = False):
    ''' Converts a number to a string using F70-like formatting.

    Purpose
    -------
	To easily convert numbers to strings while complying with F70/F90 string
    requirements.

    Example: for 'F10.0' use: width = 10, dec = False
             for 'F5.2'  use: width =  5, dec = 2
    
    Parameters
    ----------
    num : floats
        number to be transformed to string.

    width : int
        number of characters that number will occupy. 
   
    dec : int (optional) 
        number of decimals to include. When none passed, defaults to returning
        as many decimals as fit within specified width.
        
    Returns
    -------
    str_out : str
        number transformed into a string based on specified formatting.

    Notes
    -----
    * Careful that the width and decimals specified work for the given number,
      otherwise, functions will raise exceptions.
	* Probably not the smartest way of doing things, but I'm tired and grumpy.
    '''

    # Determine number of digits
    digits = len(str(int(num)))

    # Raise error if digits don't fit in specified width
    if digits > width:
        raise Exception('Digits > width | Use scientific notation?')

    # Raise error if digits + dec don't fit in specified width
    if digits + dec + 1 > width:
        raise Exception('Digits + Dec > width | Use scientific notation? ')

    # Specify lpad and prec if exact digits were required
    if dec:
        prec = dec
        lpad = max(0, width - prec - 1)

    # Specify lpad and prec if there are no decimals in digit            
    elif digits == len(str(num)):
        lpad = width
        prec = 0

    # Specify lapd and prec if there are decimals
    else:
        prec = max(0, width - digits - 1)
        lpad = max(0, width - prec - 1)

    # Convert digit to string (note that pad includes digits!!) and output
    frmt  = {'precision': prec, 'pad_left': lpad, 'unique': False}
    str_out = np.format_float_positional(num, **frmt)

    return(str_out)