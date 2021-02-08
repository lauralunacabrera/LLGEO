''' Automate the generation of QUAD4M input files

DESCRIPTION:
This module contains functions that help create input files for QUAD4M, so that 
the program can be automized.

MAIN FUNCTIONS:
This module contains the following functions:
    * gen_q4r: makes QUAD4M input file based on settings, elems, & nodes.
'''

# ------------------------------------------------------------------------------
# Import Modules
# ------------------------------------------------------------------------------
# Standard libaries
import numpy as np
import pandas as pd
import os

# LLGEO modules
import llgeo.utilities.formatters as fff

# ------------------------------------------------------------------------------
# Main Functions
# ------------------------------------------------------------------------------

def gen_q4r(Q, elems, nodes, out_path, out_file):
    ''' generates QUAD4M input file (.q4r) from given settings, elems, and nodes.
    
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
            [ n, N1, N2, N3, N4, s_num, unit_w, po, Gmax, G, XL, LSTR ]

    nodes : pandas DataFrame
        DataFrame with information for nodes (initialized in geometry module)
        Minimum required columns are:
            [ node_n, x, y, BC, OUT, X2IH, X1IH, XIH, X2IV, X1IV, XIV ]

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
    * TODO-soon: Missing KSAV and NSLP functionalities. Will return False if asked.

    References
    ----------
    (1) Hudson, M., Idriss, I. M., & Beikae, M. (1994). User’s Manual for
        QUAD4M. National Science Foundation.
            See: Fortran code describing inputs (Pgs. A-3 to A-5)

    '''

    # Error Checking (only does basic stuff... I'm assuming user is smart)
    # --------------------------------------------------------------------------
    # TODO-wishlist: change to logging?

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

    # TODO-soon:
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
    with open(out_path+out_file, 'w') as q4r_file:
        [q4r_file.write(line + '\r\n') for line in L]
        q4r_file.close()

    return L
    

def gen_dat(soil_curves, out_path, out_file):
    ''' generates QUAD4M soil data file (.dat) based on given soil curves.
    
    Purpose
    -------
    Given a list of "soil_curves", this creates an file (out_path+out_file) that
    can be used as soil properties input for the ground response analysis
    software QUAD4M (REF 1).
    
    Parameters
    ----------
    soil_curves : list of dict
        list containing one dictionary per soil curve.
        Keys MUST include:
            { 'S_name', 'S_desc', 'G_strn', 'G_mred', 'D_strn', 'D_damp'}

    out_path : str
        path to directory where output will be saved.

    out_file : str
        name of text file to store outputs (generally ending in .dat)

    Returns
    -------
    L : list of str
        List of strings corresponding to QUAD4M soil data file that was printed.
        
    Notes
    -----
    * The F70/F90 formatting may be slow because it was coded in a quick-fix
      mindset... and when I was tired ¯|_(ツ)_|¯

    References
    ----------
    (1) Hudson, M., Idriss, I. M., & Beikae, M. (1994). User’s Manual for
        QUAD4M. National Science Foundation.
            See: Fortran code describing inputs (Pgs. A-3 to A-5)

    '''
    # Some (extremely) basic error checking
    # ----------------------------------------------------------------------
    # TODO-wishlist: change to logging?
    
    # TODO-soon: add more checks and create separate function?
    # Checks to complete:
    #   0) check that number of properties < 5-digit number
    #   1) ensure dictionary keys match requirements
    #   2) ensure that G_strn and G_mred are the same size
    #   3) ensure that D_strn and D_damp are the same size
    #   4) make sure that G_strn, G_mred, D_strn, and D_damp values
    #      don't exceed formatting requirements
    #   5) warn if soil name or description are too large
    check_keys = ['S_name','S_desc','G_strn','G_mred','D_strn','D_damp']
    
    for soil in soil_curves:
        if not all (key in soil for key in check_keys):
            raise Exception('Soil curves missing dictionary keys.')
        
        if len(soil['G_strn']) != len(soil['G_mred']):
            raise Exception('Modulus reduction curve has unequal array lenghts')
    
        if len(soil['D_strn']) != len(soil['D_damp']):
            raise Exception('Damping curve has unequal array lenghts')

    # Initialize lines by adding number of soil curves.
    NUMPROPS = len(soil_curves)
    L = ['{:5d}'.format(NUMPROPS)]

    # Format specifications that will be used to create the file lines.
    fmt01 = {'cols': 8, 'width': 10, 'space': 4}
    fmt02 = '{N:5d}  | {T:^18s} | {S:^8s} | {D:^20s} | '
    fmt03 = '{lbl}'
    clim  = fmt01['cols'] * fmt01['width'] # max characters per line

    # Iterate through given soil_curves and add relevant lines
    
    for soil in soil_curves:
    
        # THIS PART MAY BECOME AN ISSUE IN THE FUTURE!
        # ----------------------------------------------------------------------
        # Note: I'm still deciding on how to approach data handling, which means
        #       the structure of inputs is likely to change.  I am adding the
        #       next few lines to make it easier fix in the future if neeeded.
        # TODO-soon: Figure out the final configuration for inputs to here.

        S_name = soil['S_name']
        S_desc = soil['S_desc']
        G_strn = soil['G_strn']
        G_mred = soil['G_mred']
        D_strn = soil['D_strn']
        D_damp = soil['D_damp']

        # Add modulus reduction curve
        # ---------------------------------------------------------------------- 
        lbl = fmt02.format(N = len(G_strn),
                           T = 'MODULUS REDUCTION',
                           S = S_name,
                           D = S_desc)

        L += [fmt03.format(lbl = lbl) ]  # Header
        L += [ fff.arr2str(G_strn, **fmt01) ]  # Shear strain
        L += [ fff.arr2str(G_mred, **fmt01) ]  # G/Gmax

        # Add damping curve
        # ----------------------------------------------------------------------
        lbl = fmt02.format(N = len(D_strn),
                           T = 'ELEMENT DAMPING',
                           S = S_name,
                           D = S_desc)

        L += [fmt03.format(lbl = lbl, W = clim) ]  # Header
        L += [ fff.arr2str(D_strn, **fmt01) ]  # Shear strain
        L += [ fff.arr2str(D_damp, **fmt01) ]  # Damping


    # Print lines to a file and return 
    # --------------------------------------------------------------------------
    if not os.path.exists(out_path):
        os.makedirs(out_path)

    with open(out_path + out_file, 'w') as dat_file:
        [dat_file.write(line + '\r\n') for line in L]
        dat_file.close()

    return L


def gen_Q(overwrites = False):
    '''
    Generates default settings for QUAD4M analyses. If a dictionary "overwrites"
    is passed, then the defaults will be updated to whatever is passed.
    '''

    Q = {
    # JOB INFORMATION 
    'FTITLE' : np.nan ,    # Job title
    'STITLE' : np.nan ,    # Job subtitle
    'UNITS'  : 'S'    ,    # Units (S = SI, E = Imperial)

    # DAMPING AND STRAIN
    'DRF' : 1.00       ,  # Damping reduction factor
    'PRM' : (7.5-1)/10 ,  # Factor max to eq uniform strain (typ.0.55 to 0.75)

    # ROCK PROPERTIES (only if compliant base!!!)
    'ROCKVP'  : 0 ,  # Rock p-wave velocity (m/s)
    'ROCKVS'  : 0 ,  # Rock s-wave velocity (m/s)
    'ROCKRHO' : 0 ,  # Rock unit weight (N/m3)

    # MESH SETTINGS
    'NELM' : np.nan ,    # Number of finite elements
    'NDPT' : np.nan ,    # Total number of nodal points
    'NSLP' : 0      ,    # Number of surfaces for seismic coefficient analysis

    # COMPUTATION SWITCHES
    'KGMAX' : np.nan  ,    # No. time steps in input earthquake record
    'KGEQ'  : np.nan  ,    # No. last  time step for last  iteration
    'N1EQ'  : 1       ,    # No. first time step for last  iteration
    'N2EQ'  : 1       ,    # No. first time step for first iterations
    'N3EQ'  : np.nan  ,    # No. last  time step for first iterations
    'NUMB'  : 30      ,    # No. iterations on soil properties
    'KV'    : 1       ,    # Flag vertical record (1 = no record, 2 = read record)
    'KSAV'  : 0       ,    # Flag save final state (0 = no save, 1 = save)

    # EARTHQUKE FILE DESCRIPTORS
    'DTEQ'    : np.nan   ,    # Time step of input motion (s)
    'EQMUL1'  : 1        ,    # Scaling factor horizontal component  
    'EQMUL2'  : 0        ,    # Scaling factor vertical component
    'UGMAX1'  : 0        ,    # Max. horizontal acceleration - will scale motion
    'UGMAX2'  : 0        ,    # Max. vertical acceleration - will scale motion
    'HDRX'    : np.nan   ,    # Header lines in horizontal input time history
    'HDRY'    : 0        ,    # Header lines in vertical input time history
    'NPLX'    : np.nan   ,    # Data pts / line in horz time history (0 = none)
    'NPLY'    : 0        ,    # Data pts / line in vert time history (0 = none)
    'PRINPUT' : 0.25     ,    # Period max spectral accel of horz input motion

    # EARTHQUAKE FILE INFORMATION
    'EARTHQH'   :  np.nan   ,    # Name of file with horz. input motion
    'EQINPFMT1' :  np.nan   ,    # Format of horz. input motion
    'EARTHQV'   :  ''       ,    # Name of file with horz. input motion
    'EQINPFMT2' :  ''       ,    # Format of horz. input motion

    # OUTPUT OPTIONS
    'SOUT' : 1 ,    # Flag: 1 = read stress output file descriptors
    'AOUT' : 1 ,    # Flag: 1 = read acceleration output file descriptors 
    'KOUT' : 0 ,    # Flag: 1 = read seismic coefficient output file descriptors

    # STRESS OUTPUT FILE DESCRIPTORS (ONLY USED IF SOUT = 1)
    'SHISTFMT' : 'C'     ,   # Dump data into 'COMBINED' or 'MULTIPLE' files
    'SFILEOUT' : np.nan  ,   # Output file name
    'SSUFFIX'  : 'str'   ,   # Output file name sufix (3 character max)

    # ACCELERATION OUTPUT FILE DESCRIPTORS (ONLY USED IF AOUT = 1)
    'AHISTFMT' : 'C'    ,    # Dump data into '(C)OMBINED' or '(M)ULTIPLE' files
    'AFILEOUT' : np.nan ,    # Output file name (8 char max)
    'ASUFFIX'  : 'acc'  ,    # Output file name sufix (3 character max)

    # SEISMIC COEFFICIENT OUTPUT FILE DESCRIPTORS (ONLY USED IF KOUT = 1)
    'KHISTFMT' : '' ,    # Dump data into '(C)OMBINED' or '(M)ULTIPLE' files
    'KFILEOUT' : '' ,    # Output file name
    'KSUFFIX'  : '' ,    # Output file name sufix (3 character max)

    # RESTART FILE NAME DESCRIPTOR (ONLY USED IF KSAV = 1)
    'SAVEFILE' : '' ,    # Output file name for last state (no path)

    # SEISMIC COEFFICIENT LINES (ONLY IF NSLP > 0, REPEAT NSLP TIMES)
    'NSEG'  : '' ,    # Number of nodes intersected by surface 
    'ESEG'  : '' ,    # Number of elements within surface
    'NOSEG' : '' ,    # Node J intersected by surface I (NSEG nodes) ?????
    'ELSEG' : '' ,    # Element J within surfce I (ESEG elements) ????
    }

    if overwrites:
        Q.update(overwrites)

    return Q

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