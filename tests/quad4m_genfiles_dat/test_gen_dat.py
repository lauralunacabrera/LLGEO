'''
TITLE:     test_gen_dat.py
TASK_TYPE: test
PURPOSE:   Make sure that generation of data files works somewhat decently 
LAST_UPDATED: 28 December 2020
'''
#%% Import modules

# Standard libraries
import numpy as np

# Import LLGEO
import llgeo.quad4m.genfiles as q4m_files
import llgeo.props_nonlinear.darendeli_2011 as darendeli


#%% Example that should work
 
soil_curves = [{'S_name' : 'Sand'               ,
                'S_desc' : 'darendeli mean'     ,
                'G_strn' : np.logspace(-4, 0)   ,
                'G_mred' : np.linspace(1, 0)    ,
                'D_strn' : np.logspace(-4, 0)   ,
                'D_damp' : np.linspace(0, 25)   ,
               },
               {'S_name' : 'Clay'               ,
                'S_desc' : 'darendeli mean'     ,
                'G_strn' : np.logspace(-4, 0)   ,
                'G_mred' : np.linspace(1, .5)   ,
                'D_strn' : np.logspace(-4, 0)   ,
                'D_damp' : np.linspace(0, 15)   ,
               },
               ]

L = q4m_files.gen_dat(soil_curves, out_path = './', out_file = 'test.dat')


#%% Example that shouldn't work due to missing soil_curve data

incomplete = [{'S_name' : 'Sand'                ,
                'S_desc' : 'darendeli mean'     ,
                'D_damp' : np.linspace(0, 25)   ,
               },
               {'S_name' : 'Clay'               ,
                'G_mred' : np.linspace(1, .5)   ,
                'D_damp' : np.linspace(0, 15)   ,
               },
               ]

L = q4m_files.gen_dat(incomplete, out_path = './', out_file = 'test.dat')

# %%
