'''
TITLE:     01_01_21_00.py
TASK_TYPE: test
PURPOSE:   Carries out workflow for example QUAD4M analyses to test functions
           in the python package llgeo/quad4m
            stage:      01 Basic QUAD4M Proof of Concepts
            model:      01 Sand column with linear properties
            earthquake: 21 T = 2475yr Crustal HWA03 E 
            properties: 00 Homogeneous
           
LAST_UPDATED: 22 November 2020
TO_DO:
'''
#%% Import modules

# Import standard pacakges
import numpy as np
import pandas as pd

# Import LLGEO modules
import llgeo.quad4m.geometry as geom
import llgeo.quad4m.genfiles as gfile

#%% STEP #1 --------------------------------------------------------------------
#   Obtain model geometry from DXF file
print('Generating geometry')
nodes, elems = geom.dxf_to_dfs('./CAD/', '01_01.dxf')  # Read dxf and create dfs
geom.dfs_to_dxfs('./CAD/', '01_01_check.dxf', nodes, elems) # Output to dxf again, as a check 


#%% STEP #2 --------------------------------------------------------------------
#   Element and node properties
print('Filling soil properties')

# Get number of nodes and elements
nelm = len(elems)
ndpt = len(nodes)

# Boundary conditions
BC = 0 * np.ones(ndpt)
BC[nodes['x'] == np.min(nodes['x'])] = 2 # Left Boundary
BC[nodes['x'] == np.max(nodes['x'])] = 2 # Right Boundary
BC[nodes['y'] == np.min(nodes['y'])] = 3 # Bottom Boundary
nodes['BC'] = BC
nodes['OUT'] = np.ones(ndpt)

# Element properties (this will eventually be randomized)
params = ['X2IH', 'X1IH', 'XIH', 'X2IV', 'X1IV', 'XIV']
 
for param in params:
    nodes[param] = np.zeros(ndpt)

elems['unit_w'] = 21000 * np.ones(nelm) # ( N / m3 ) 
elems['po']     = 0.450 * np.ones(nelm) # ( ---- )
elems['Vs']     = 170   * np.ones(nelm) # ( m / s )
elems['Gmax']   = (elems['unit_w']/9.81) * (elems['Vs'] ** 2)/1000 # Gmax = rho * Vs^2
elems['s_num']  = np.ones(nelm) # quick fix - todo
elems['G']      = elems['Gmax'] # Gmax = rho * Vs^2
elems['XL']     = 0.05 * np.ones(nelm) # Gmax = rho * Vs^2
elems['LSTR']   = 4*np.ones(nelm) # Gmax = rho * Vs^2

#%% STEP #3 --------------------------------------------------------------------
#   Earthquake properties
print('Filling earthquake information')

# Get earthquake properties
acc_file = './motions/21_2475_crus_HWA03_E.acc'
acc = np.genfromtxt(acc_file)
hdr = open(acc_file, 'r').readline().split()
dt  = float(hdr[6])
num_steps = int(hdr[9])

# Earthquake file details
acc_file = acc_file.replace('/', '\\') # slash fix for QUAD4M
acc_fmt = '(1e14.5)' # number format
acc_nls = 1 # numbers per line
acc_hls = 1 # number of header liens

# Earthquake properties
M = 7.5

#%% STEP #4 --------------------------------------------------------------------
#   QUAD4M Model settings
print('Preparing QUAD4M file')

Q = {
    # JOB INFORMATION 
    'FTITLE' : '01_01_21_00'      ,    # Job title
    'STITLE' : 'Proof of Concept' ,    # Job subtitle
    'UNITS'  : 'S'                ,    # Units (S = SI, E = Imperial)

    # DAMPING AND STRAIN
    'DRF' : 1.00 ,        # Damping reduction factor
    'PRM' : (7.5-1)/10,   # Factor convert max to eq uniform strain (typ.0.55 to 0.75)

    # ROCK PROPERTIES (only if compliant base!!!)
    'ROCKVP'  : 0 ,    # Rock p-wave velocity (m/s)
    'ROCKVS'  : 0 ,    # Rock s-wave velocity (m/s)
    'ROCKRHO' : 0 ,    # Rock unit weight (N/m3)

    # MESH SETTINGS
    'NELM' : nelm ,    # Number of finite elements
    'NDPT' : ndpt ,    # Total number of nodal points
    'NSLP' : 0    ,    # Number of surfaces for seismic coefficient analysis

    # COMPUTATION SWITCHES
    'KGMAX' : num_steps ,    # No. time steps in input earthquake record
    'KGEQ'  : num_steps ,    # No. last  time step for last  iteration
    'N1EQ'  : 1         ,    # No. first time step for last  iteration
    'N2EQ'  : 1         ,    # No. first time step for first iterations
    'N3EQ'  : num_steps ,    # No. last  time step for first iterations
    'NUMB'  : 50        ,    # No. iterations on soil properties
    'KV'    : 1         ,    # Flag vertical record (1 = no record, 2 = read record)
    'KSAV'  : 0         ,    # Flag save final state (0 = no save, 1 = save)

    # EARTHQUKE FILE DESCRIPTORS
    'DTEQ'    : dt       ,    # Time step of input motion (s)
    'EQMUL1'  : 1        ,    # Scaling factor horizontal component  
    'EQMUL2'  : 0        ,    # Scaling factor vertical component
    'UGMAX1'  : 0        ,    # Max. horizontal acceleration - will scale motion
    'UGMAX2'  : 0        ,    # Max. vertical acceleration - will scale motion
    'HDRX'    : acc_hls  ,    # Header lines in horizontal input time history
    'HDRY'    : 0        ,    # Header lines in vertical input time history
    'NPLX'    : acc_nls  ,    # Data points per line in horizontal time history (0 = none)
    'NPLY'    : 0        ,    # Data points per line in vertical time history (0 = none)
    'PRINPUT' : 0.25     ,    # Period of max. spectral accel. of horz. input motion (s)

    # EARTHQUAKE FILE INFORMATION
    'EARTHQH'   :  acc_file   ,    # Name of file with horz. input motion
    'EQINPFMT1' :  acc_fmt    ,    # Format of horz. input motion
    'EARTHQV'   :  ''         ,    # Name of file with horz. input motion
    'EQINPFMT2' :  ''         ,    # Format of horz. input motion

    # OUTPUT OPTIONS
    'SOUT' : 1 ,    # Flag: 1 = read stress output file descriptors
    'AOUT' : 1 ,    # Flag: 1 = read acceleration output file descriptors 
    'KOUT' : 0 ,    # Flag: 1 = read seismic coefficient output file descriptors

    # STRESS OUTPUT FILE DESCRIPTORS (ONLY USED IF SOUT = 1)
    'SHISTFMT' : 'C' ,    # Dump data into 'COMBINED' or 'MULTIPLE' files
    'SFILEOUT' : 'test' ,    # Output file name
    'SSUFFIX'  : 'str' ,    # Output file name sufix (3 character max)

    # ACCELERATION OUTPUT FILE DESCRIPTORS (ONLY USED IF AOUT = 1)
    'AHISTFMT' : 'C'    ,    # Dump data into '(C)OMBINED' or '(M)ULTIPLE' files
    'AFILEOUT' : 'test' ,    # Output file name (8 char max)
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

#%%
print('Generating file')
model_id = '01_01_21_00'
gfile.gen_QUAD4M_q4r(Q, elems, nodes, out_path = '',
                            out_file = model_id+'.q4r')
print('All done!')

#%%
