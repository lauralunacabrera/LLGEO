'''
TITLE:     ADD FILE NAME HERE.py
TASK_TYPE: test
PURPOSE:   ADD DESCRIPTION HERE
LAST_UPDATED: 15 December 2020
STATUS: WIP
TO_DO:
'''
#%% Import modules

# Path fix for testing the modules (not needed when llgeo is installed)
import os
import sys
rel_path = os.path.join(os.path.dirname(__file__), '../../../')
sys.path.insert(0, os.path.abspath(rel_path))

# Change workind directory to wherever this file is saved
import pathlib
cpath = pathlib.Path(__file__).parent.absolute()
os.chdir(cpath)

# Import LLGEO
import llgeo.quad4m.genfiles as gfile
import llgeo.props_nonlinear.darendeli_2011 as darendeli

#%%

params = darendeli.params(0, 1, 50, )
help(darendeli)

s# %%
