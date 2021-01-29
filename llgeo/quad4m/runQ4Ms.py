''' Automate running QUAD4M in a Linux system

DESCRIPTION:
This module contains functions that run the executable QUAD4MU.exe automatically
for a given set of QUAD4M input files.

MAIN FUNCTIONS:
This module contains the following functions:
    * run_QUAD4M: runs one instance of QUAD4MU, given all input files and dirs

'''
from memory_profiler import memory_usage
from threading import Thread
import subprocess as sub
import os
import numpy as np
import math
import time

# ------------------------------------------------------------------------------
# Main functions
# ------------------------------------------------------------------------------

def runQ4M(dir_q4m, dir_wrk, dir_out, file_q4r, file_dat, file_out, file_bug):
    ''' Runs a single simulation of QUAD4MU, given all input files and dirs.
    
    Purpose
    -------
    Given a QUAD4M input file, a soil reduction file, and output locations, this
    function runs the QUAD4M excecutable using WINE and prints the standard out-
    put and error to a file.
    
    A few important notes:
        1) This code will only work on a Linux operating system.
        2) Windows emulator WINE must be installed to run the ".exe" file.
        3) Inside the .q4r file, the path to the earthquake motion is specified.
           User must make sure that path exists, this function can't check that.
        4) The working directory is changed to dir_q4m at the start of the fun-
           ction and then reverted. So, all paths must either be absolute, or
           relative to dir_q4m.
        5) All paths must end in "/" !!!
    
    Parameters
    ----------
    dir_q4m : str
        path containing the file 'Quad4MU.exe'. Note that the current
        directory will be changed to this location while running this function. 
    dir_wrk : str
        path to working directory, where .q4r and .dat files are stored
         for this simulation. Must be either relative to dir_q4m, or absolute.
    dir_out: str
        path to output directory, where QUAD4M outputs will be stored.
        Must be either relative to dir_q4m, or absolute.
    file_q4r : str
        name of input file, usually with extension ".q4r"
    file_dat : str
        name of file with modulus reduction and damping curves, usually with
        extension ".dat" 
    file_out : str
        name of file to store outputs, usually with extension ".out"
    file_bug : str
        name of file to store dump from QUAD4M (just progress on itertions), 
        usually with extension ".bug"
        
    Returns
    -------
    Nothing is returned driectly - simply creates output files. Returns False
    if an error is caught, true if QUAD4MU is run (maybe succesfully, maybe not)
        
    References
    ---------- 
    (1) Hudson, M., Idriss, I. M., & Beikae, M. (1994). User’s Manual for
        QUAD4M. National Science Foundation.
    '''
    # Change current directory to wherever Quad4M file is saved
    dir_ini = os.getcwd()
    os.chdir(dir_q4m)

    # Check that all files exist, and return if anything is missing.
    err_flag = 0
    paths = ['Quad4MU.exe', dir_wrk+file_q4r, dir_wrk+file_dat, dir_out]
    err_msgs = ['Missing Quad4MU.exe file', 'Missing .q4r input file',
                'Missing .dat soil reduction file', 'Output path doesnt exist']   
    
    # Check that files end in /
    for path in [dir_out, dir_q4m, dir_wrk]:
        if path[-1] != '/':
            print('Add final / to path: ' + path)
            err_flag += 1
    
    # Check that paths exist
    for path, err_msg in zip(paths, err_msgs):
        if not os.path.exists(path):
            print(err_msg + '\n Cannot run simulation.')
            print('Revise path: '+ path)
            print('wrk, dat, and out paths must be relative to dir_q4m')
            err_flag += 1

    # Escape if an error was found
    if err_flag > 0:
        return False

    # Make sure that slashes are made for a windows system
    dir_wrk_win = dir_wrk.replace('/', '\\')
    dir_out_win = dir_out.replace('/', '\\')

    # Open the subprocess with pipelines for inputs and errors
    p = sub.Popen(['wine', 'Quad4MU.exe'],
                    stdin  = sub.PIPE,
                    stdout = sub.PIPE,
                    stderr = sub.PIPE,
                    shell  = False,
                    universal_newlines = True)

    # Write Quad4MU inputs to standard input
    p.stdin.write(dir_wrk_win + file_q4r + '\n')
    p.stdin.write(dir_wrk_win + file_dat + '\n')
    p.stdin.write(dir_out_win + '\n')
    p.stdin.write(file_out + '\n')

    # Run!
    stdout, stderr = p.communicate()

    # Print standard output and standard error to debug file
    with open(dir_q4m + dir_out + file_bug, 'w+') as f:
        f.write('STANDARD OUTPUT\n---------------')
        f.write(stdout)
        f.write('\n\n\n')
        f.write('STANDARD ERROR\n--------------')
        f.write(stderr)
        f.close()

    # Change directory back to wharever it was initially
    os.chdir(dir_ini)

    return True


def runQ4Ms_series(dq4ms, dwrks, douts, fq4rs, fdats, fouts, fbugs):

    for i, args in enumerate(zip(dq4ms, dwrks, douts, fq4rs, fdats, fouts, fbugs)):
        _ = runQ4M(*args)
        print('Processed file no. ' + str(i+1))

    return True


def runQ4Ms_parallel(dq4ms, dwrks, douts, fq4rs, fdats, fouts, fbugs, max_workers):

    all_args = [a for a in zip(dq4ms, dwrks, douts, fq4rs, fdats, fouts, fbugs)]
    num_groups = math.ceil( len(all_args)/max_workers)
    print('Starting {:d} Threads to Process {:d} Groups'.format(max_workers, num_groups))
    
    grouped_args = []
    for n in range(num_groups):
        ifrom = max_workers * n
        ito   = max_workers * (n + 1)   
        grouped_args += [ all_args[ifrom : ito] ]

    for n, group in enumerate(grouped_args):
        ts = [Thread(target = runQ4M, args = args) for args in group] 
        [t.start() for t in ts]
        [t.join() for t in ts]
        print('Concluded with group: '+str(n+1))

    return True


def run_QUAD4Ms_series_mem(dq4ms, dwrks, douts, fq4rs, fdats, fouts, fbugs, max_workers = None):

    args = (dq4ms, dwrks, douts, fq4rs, fdats, fouts, fbugs)
    mem = memory_usage(proc = (runQ4Ms_series, args), interval = 0.5, 
                                timeout = 2, include_children = True)
    return np.max(mem)


def run_QUAD4Ms_parallel_mem(dq4ms, dwrks, douts, fq4rs, fdats, fouts, fbugs, max_workers):

    args = (dq4ms, dwrks, douts, fq4rs, fdats, fouts, fbugs, max_workers)
    mem = memory_usage(proc = (runQ4Ms_parallel, args), interval = 0.5, 
                                timeout = 2, include_children = True)

    return np.max(mem)