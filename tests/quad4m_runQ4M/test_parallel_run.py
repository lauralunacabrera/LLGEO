''' Automate running QUAD4M in a Linux system

DESCRIPTION:
This module contains functions that run the executable QUAD4MU.exe automatically
for a given set of QUAD4M input files.

MAIN FUNCTIONS:
This module contains the following functions:
    * run_QUAD4M: runs one instance of QUAD4MU, given all input files and dirs

'''
#%%
import time
import llgeo.quad4m.runQ4Ms as q4m_run

# Proof that parallelizing works!

# Specify directories
dir_q4m = './'
dir_wrk = 'inputs/'
dir_out = 'outputs/'

# Specify files
file_q4r = '1dst.q4r'
file_dat = 'red.dat'
file_out = file_q4r.replace('.q4r','.out')
file_bug = file_q4r.replace('.q4r','.bug')

k = 20
inputs = {
            'dq4ms' : k * [dir_q4m]  ,
            'dwrks' : k * [dir_wrk]  ,
            'douts' : k * [dir_out]  ,
            'fq4rs' : k * [file_q4r] ,
            'fdats' : k * [file_dat] ,
            'fouts' : [file_out.replace('.out', '.out'+str(i)) for i in range(k)],
            'fbugs' : [file_bug.replace('.bug', '.bug'+str(i)) for i in range(k)],
            'max_workers' : 10
        }

start = time.time()
max_mem = q4m_run.run_QUAD4Ms_parallel_mem(**inputs)
end = time.time()
print('Parallel code:')
print('    Took {:4.2f}s to run with a '.format(end - start))
print('    peak memory usage of {:6.2f}MiB'.format(max_mem))

start = time.time()
max_mem = q4m_run.run_QUAD4Ms_series_mem(**inputs)
end = time.time()
print('Series code:')
print('    Took {:4.2f}s to run with a '.format(end - start))
print('    peak memory usage of {:6.2f}MiB'.format(max_mem))