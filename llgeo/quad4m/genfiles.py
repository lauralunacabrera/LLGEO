''' Automate the generation of QUAD4M input files

DESCRIPTION:
This module contains functions that help create input files for QUAD4M, so that 
the program can be automized.

MAIN FUNCTIONS:
This module contains the following functions:
    * gen_QUAD4M_q4r generates QUAD4M input file based on settings, elements, and nodes.
    
TODOS:
    *** (IMPORTANT) gen_QUAD4M_q4r IS NOT COMPLETE!!!
        SEISMIC COEFFICIENT LINES AND KSAV ARE NOT DONE
'''
# ------------------------------------------------------------------------------
# Import Modules
# ------------------------------------------------------------------------------
import numpy as np
import pandas as pd

# ------------------------------------------------------------------------------
# Main Functions
# ------------------------------------------------------------------------------
def gen_QUAD4M_q4r(Q, elems, nodes, out_path, out_file):
    ''' generates QUAD4M input file based on settings, elements, and nodes.
    
    Purpose
    -------
    Given a dictionary of QUAD4M settings (q), and dataframe with element and 
    node information (nodes), this creates a file (out_path+out_file) that can
    be used as input for the ground response analysis software QUAD4M (REF 1).
    
    Parameters
    ----------
    Q : dict
        dictionary with settings for QUAD4M analyses. See ref (1).
    elems : pandas DataFrame
        DataFrame with information for elements (initialized in geometry module)
        Minimum required columns are:
            n, N1, N2, N3, N4, s_num, unit_w, po, Gmax, G, XL, LSTR
    nodes : pandas DataFrame
        DataFrame with information for nodes (initialized in geometry module)
        Minimum required columns are:
            node_n, x, y, BC, OUT, X2IH, X1IH, XIH, X2IV, X1IV, XIV
    out_path : str
        path to directory where output will be saved
    out_file : str
        name of text file to store outputs

    Returns
    -------
    L : list of str
        List of strings corresponding to QUAD4M input file that was printed
        If error checking catchers error, returns FALSE instead.
        
    Notes
    -----
    * TODO: Missing KSAV and NSLP functionalities. Will return False if asked.

    References
    ----------
    (1) Hudson, M., Idriss, I. M., & Beikae, M. (1994). User’s Manual for
        QUAD4M. National Science Foundation.
            See: Fortran code describing inputs (Pgs. A-3 to A-5)

    '''

    # Error Checking (only does basic stuff... I'm assuming user is smart)
    # --------------------------------------------------------------------------
    
    # Check that all required node and element information is present
    req_elem_cols = ['n', 'N1', 'N2', 'N3', 'N4',
                     's_num', 'unit_w','po', 'Gmax', 'G', 'XL', 'LSTR']

    req_node_cols = ['node_n', 'x', 'y', 'BC', 'OUT',
                     'X2IH', 'X1IH', 'XIH', 'X2IV', 'X1IV', 'XIV'] 

    elems_check = check_cols(req_elem_cols, list(elems), err_subtitle = 'elems') 
    nodes_check = check_cols(req_node_cols, list(nodes), err_subtitle = 'nodes') 

    if not all([elems_check, nodes_check]):
        print('Cannot create QUAD4M input file')
        return False

    # Ensure proper data types for some columns in nodes and elements tables
    etypes = 6*[int] + 5*[float] + [int]
    elems = elems.astype({col:t for col, t in zip(req_elem_cols, etypes)})

    ntypes = [int] + 2*[float] + 2*[int] + 6*[float]
    nodes = nodes.astype({col:t for col, t in zip(req_node_cols, ntypes)})

    # Check that number of nodes,elements, and earthquake steps are within lims
    if len(elems) > 99999:
        print('Too many elements. Must be less than 99,999')
        print('Cannot create QUAD4M input file')
        return False

    if len(nodes) > 99999:
        print('Too many nodal points. Must be less than 99,999')
        print('Cannot create QUAD4M input file')
        return False

    if Q['KGMAX'] > 99999:
        print('Too many earthquake time steos. KGMAX must be less than 99,999')
        print('Cannot create QUAD4M input file')
        return False

    # Prepare numeric outputs (formatting)
    # --------------------------------------------------------------------------
    # Damping settings and rock properties
    N = [Q[s] for s in ['DRF','PRM','ROCKVP','ROCKVS','ROCKRHO']]
    L_05 = format_line(N, 5*['{:10f}'])

    # Number of elements, nodes, and seismic coefficient lines
    N = [Q[s] for s in ['NELM','NDPT','NSLP']]
    L_07 = format_line(N, 3*['{:5d}'])

    # Computational switches
    N = [Q[s] for s in ['KGMAX','KGEQ','N1EQ','N2EQ','N3EQ','NUMB','KV','KSAV']]
    L_09 = format_line(N,  8*['{:5d}'])

    # Earthquake file descriptors
    N = [Q[s] for s in ['DTEQ','EQMUL1','EQMUL2','UGMAX1','UGMAX2','HDRX',
                        'HDRY','NPLX','NPLY','PRINPUT']]
    L_11 = format_line(N, 5*['{:10f}'] + 4*['{:5d}'] + 1*['{:10f}'])

    # Output flags
    N = [Q[s] for s in ['SOUT','AOUT','KOUT']]
    L_18 = format_line(N, 3*['{:5d}'])

    # Element table
    out_elems = elems[req_elem_cols].astype('O')
    Fs = 6*['{:5d}']+['{:10.0f}','{:10.2f}']+2*['{:10.3e}']+['{:10.4f}','{:5d}']
    Ls_40 = [format_line(N, Fs) for _, N in out_elems.iterrows()]

    # Node table
    out_nodes = nodes[req_node_cols].astype('O')
    Fs = ['{:5d}']+2*['{:10.4f}']+2*['{:5d}']+6*['{:>13.7f}']
    Ls_42 = [format_line(N, Fs) for _, N in out_nodes.iterrows()]

    # Create list of file lines 
    # --------------------------------------------------------------------------
    L = []
    L += ['MODEL:' + Q['FTITLE'] + '  |  ' + Q['STITLE']]                #C(L01)
    L += ['UNITS (E for English, S for SI): (A1)']                       #C(L02)
    L += [Q['UNITS']]                                                    #V(L03)
    L += ['       DRF       PRM    ROCKVP    ROCKVS   ROCKRHO (5F10.0)'] #C(L04)
    L += [L_05]                                                          #V(L05) 
    L += [' NELM NDPT NSLP (3I5)']                                       #C(L06) 
    L += [L_07]                                                          #V(L07)
    L += ['KGMAX KGEQ N1EQ N2EQ N3EQ NUMB   KV KSAV (8I5)']              #C(L08)
    L += [L_09]                                                          #V(L09)
    L += ['      DTEQ    EQMUL1    EQMUL2    UGMAX1    UGMAX2 ' +        #C(L10)
              'HDRX HDRY NPLX NPLY   PRINPUT (5F10.0,4I5,F10.0)']
    L += [L_11]                                                          #V(L11)
    L += ['EARTHQUAKE INPUT FILE NAME(S) & FORMAT(S) (* for free)  (A)'] #C(L12)
    L += [ Q['EARTHQH'] ]                                                #V(L13)
    L += [ Q['EQINPFMT1'] ]                                              #V(L14)

    if Q['KV'] == 2:
        L += [ Q['EARTHQV'] ]                                            #V(L15)
        L += [ Q['EQINPFMT2'] ]                                          #V(L16)

    L+= [' SOUT AOUT KOUT (3I5)']                                        #C(L17)
    L+= [L_18]                                                           #V(L18) 

    if Q['SOUT'] == 1:
        L+= ['STRESS OUTPUT FORMAT, FILE PREFIX AND SUFFIX: (A)']        #C(L19)
        L+= [ Q['SHISTFMT']  ]                                           #V(L20)
        L+= [ Q['SFILEOUT'] ]                                            #V(L21)
        L+= [ Q['SSUFFIX']   ]                                           #V(L22)

    if Q['AOUT'] == 1:
        L+= ['ACCELERATION OUTPUT FORMAT, FILE PREFIX AND SUFFIX: (A)']  #C(L23)
        L+= [ Q['AHISTFMT']  ]                                           #V(L24)
        L+= [ Q['AFILEOUT']  ]                                           #V(L25)
        L+= [ Q['ASUFFIX']   ]                                           #V(L26)

    if Q['KOUT'] == 1:
        L+= ['SEISMIC COEFF OUTPUT FORMAT, FILE PREFIX AND SUFFIX: (A)'] #C(L27)
        L+= [ Q['KHISTFMT']  ]                                           #V(L28)
        L+= [ Q['KFILEOUT'] ]                                            #V(L29)
        L+= [ Q['KSUFFIX']   ]                                           #V(L30)

    # TODO:
    #   Putting these here so I am aware of the work that still needs to be done
    #   Don't think I'll be using the KSAV option
    #   I will eventually have to figure out the seismic coefifcient part though

    # Restart file name descriptors (Lines 31 to 32)
    if Q['KSAV'] == 1:
        print('The KSAV functionality has not been coded yet. Turn to 0')
        return False

    # Seismic coefficient lines (Lines 33 to 38) * NSLP times
    for _ in range(Q['NSLP']):
        print('The seismic coefficient line options have not been coded yet')
        return False

    L += [(6*'{:>5s}'+5*'{:>10s}'+'{:>5s}').format(*req_elem_cols)]      #C(L39)             
    L += Ls_40                                                           #V(L40) 

    L += [('{:>5s}'+2*'{:>10s}'+2*'{:>5s}'+6*'{:>13s}'). \
                                    format(*req_node_cols)]              #C(L41)
    L += Ls_42                                                           #V(L42)

    # Print lines to a file and return 
    # --------------------------------------------------------------------------
    with open(out_path+out_file, 'w') as file:
        [file.write(l+'\n') for l in L]
        file.close()

    return L


# ------------------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------------------
def check_cols(req_cols, exist_cols, err_subtitle = ''):
    ''' Helper function to check that all required columns exist in a dataframe

    Purpose
    -------
    Given a list of required columns, "req_cols", checks that all exist in the 
    list "exist_cols". Returns True if they all exist, False if any are missing,
    and prints error messages whenever columns are missing.
    
    Parameters
    ----------
    req_cols : list of str
        list of required columns
    exist_cols : list of str
        list of existing columns in dataframe (just pass list(df))
    error_subtitle : str (optional, defaults to '')
        additional error line to print, if necessary.
    dec : int
        number of decimals to round coordinates to (defaults to 4 if none given)
        
    Returns
    -------
    []   : logical
        Returns True if all columns exist, and False if any are missing.
    '''
    missing = [col for col in req_cols if col not in exist_cols]
    
    if len(missing) == 0:
        return True

    else:
        print('Error: missing columns')
        print(err_subtitle)
        [print('      {:s}'.format(m)) for m in missing]
        print(' ')
        return False


def format_line(nums, fmts):
    ''' Helper function to format list numbers (nums) in list of formats (fmts)

    Purpose
    -------
    Format numbers (nums) in one string according to given formats (fmts)
    
    Parameters
    ----------
    nums : list
        numbers or contents to be formatted
    fmts : list
        list of format specifiers

    Returns
    -------
    line   : str
        String of nums formatted according to fmts
    '''
    
    line = ''
    for num, fmt in zip(nums, fmts):
        if num != '':
            line += fmt.format(num)
    return(line)