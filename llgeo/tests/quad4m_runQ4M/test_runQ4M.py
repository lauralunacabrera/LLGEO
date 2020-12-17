'''
TITLE:     test_runQ4M.py
TASK_TYPE: test
PURPOSE:   Run a test Quad4M simulation to make sure that the created function
           works properly.
LAST_UPDATED: 10 December 2020
STATUS: WIP
TO_DO:
'''
#%% Import modules

# Import LLGEO
import llgeo.quad4m.runQ4Ms as runQ4Ms

#%% Run a test Q4M model

# Specify directories
dir_q4m = './'
dir_wrk = 'inputs/'
dir_out = 'outputs/'

# Specify files
file_q4r = '1dst.q4r'
file_dat = 'red.dat'
file_out = file_q4r.replace('.q4r','.out')
file_bug = file_q4r.replace('.q4r','.bug')

# Run model
check = runQ4Ms.runQ4M(dir_q4m, dir_wrk, dir_out,
                       file_q4r, file_dat, file_out, file_bug)

if check:
    print('Success!')
else:
    print('Uh oh...')

# %%
