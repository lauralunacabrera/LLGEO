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

def arr2str_F70(data, cols, width, dec = False, space = 0):
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

    space : int (optional)
        blank characters to keep between adjecent numbers
        THIS ARGUMENT WILL ONLY BE USED IF DEC = FALSE.

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
        if (i > 0) & (i % cols == 0):
            str_out += '\n'
        
        str_out += num2str_F70(num, width, dec, space) 

    return(str_out)


def num2str_F70(num, width, dec = False, space = 0):
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

    space : int (optional)
        blank characters to keep between adjecent numbers
        THIS ARGUMENT WILL ONLY BE USED IF DEC = FALSE.
        
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
        raise Exception('Digits > width | Use scientific?')

    # Raise error if digits + dec + space don't fit in specified width
    if digits + dec + space + 1 > width:
        raise Exception('Digits + dec + space > width | Use scientific?')

    # Specify lpad and prec if exact digits were required
    if dec:
        prec = dec
        lpad = max(0, width - prec - 1)

    # Specify lpad and prec if there are no decimals in digit            
    elif digits == len(str(num)):
        lpad = width - space
        prec = 0

    # Specify lapd and prec if there are decimals
    else:
        prec = max(0, width - space - digits - 1)
        lpad = max(0, width - prec - 1)

    # Convert digit to string (note that pad includes digits!!) and output
    frmt  = {'precision': prec, 'pad_left': lpad, 'unique': False}
    str_out = np.format_float_positional(num, **frmt)

    return(str_out)


def list_to_matrix(i, j, values):
    ''' Given a series of row values (i) and column values (j), and corresponding
        values, this re-formats the data into a matrix. i becomes the rows and 
        j becomes the columns, and the matrix is zero-indeced. Will return error
        if there are duplicate ij values.'''

    # Make sure i and j are 2D arrays of integers
    i = np.array(i, dtype = int).reshape(-1, 1)
    j = np.array(j, dtype = int).reshape(-1, 1)

    # Make sure that ij pairs are unique
    ij = np.concatenate([i, j], axis = 1)
    ij_unique = np.unique(ij, axis = 0)

    if len(ij_unique) < len(ij):
        mssg = 'error in list_to_matrix function:'
        mssg+= 'i and j values must be unique'
        raise Exception(mssg)

    # Turn list to column
    nrows = np.max(i) # assumes 1-indexed
    ncols = np.max(j) # assumes 1-indexed
    matrix = np.full((nrows, ncols), np.nan)

    for row, col, val in zip(i, j, values):
        matrix[row - 1, col - 1] = val # assumes 1-indexed
 
    return matrix


