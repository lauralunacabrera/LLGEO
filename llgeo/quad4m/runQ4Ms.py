''' Automate running QUAD4M in a Linux system

DESCRIPTION:
This module contains functions that run the executable QUAD4MU.exe automatically
for a given set of QUAD4M input files.

'''
from memory_profiler import memory_usage
import llgeo.utilities.files as llgeo_fls
import llgeo.quad4m.post_process as q4m_post
from threading import Thread
import subprocess as sub
import os
import numpy as np
import time

# ------------------------------------------------------------------------------
# Running QUAD4M stages
# ------------------------------------------------------------------------------

def runQ4M_stages(stages, dir_q4m, nthreads, del_exist = False, post = False,
                  del_txt = False):
    ''' This runs a QUAD4M stage ASSUMING A VERY SPECIFIC FILE STRUCTURE
        
    Purpose
    -------
    This automates running several stages of QUAD4M analyses, where each stage
    constitutes a group of QUAD4M models that share some properties.
    THIS ASSUMES A VERY SPECIFIC FILE STRUCTURE:
    
        dir_q4m (contains .EXE file) 
        |
        |--> Quad4MU.exe
        |
        |--> stages[0] --> contains inputs for stage 0; will contain all outputs
        |
        |--> stages[1] --> contains inputs for stage 1; will contain all outputs
        :
        |--> stages[-1]--> contains inputs for stage N; will contain all outputs

    
    Parameters
    ----------
    stages : list of str
        Each element is the name of a subdirector in dir_q4m that contains input
        files for analyses within this stage.
        Each stage subdirectory must contain .q4r and .dat files for each model
        and output files (.out .bug .acc and/or .str) will be saved there.
        
    dir_q4m : str
        relative or absolute directory to where .EXE file is saved and where
        stage subdirectories are located.

    nthreads : int
        Number of threads to use when running analyses (make sure to leave one
        or two open for the OS)

    del_exist : bool (optional)
        If true, will delete all output files that already exist in stages
        subdirectories. Defaults to false.

    post : bool (optional)
        If true, each model will be post-processed as the simulations occurr, 
        saving a single .pkl file for each model with the analysis results.
        Defaults to false.

    del_txt : bool (optional)
        If true (and post = true), the text files for QUAD4M analyses will all
        be deleted. Defaults to false. Note that the files will only be deleted
        if the model was deemed to finish succcessfully, so that errors can be
        properly debugged.
    '''

    # Change working directory to where EXE file is saved
    ini_path = os.getcwd()
    os.chdir(dir_q4m)
    dir_q4m = './'
        
    # Get a list of inputs for all models to be run
    dq4ms, dwrks, douts = [], [], [] 
    fq4rs, fdats, fouts, fbugs = [], [], [], []

    for stage in stages:
        files = [f for f in sorted(os.listdir(stage+'/'))if f.endswith('.q4r')]
        fq4rs += files
        fdats += [f.replace('.q4r', '.dat') for f in files]
        fouts += [f.replace('.q4r', '.out') for f in files]
        fbugs += [f.replace('.q4r', '.bug') for f in files]
        dq4ms += len(files) * [ './' ]
        dwrks += len(files) * [ stage + '/' ]
        douts += len(files) * [ stage + '/' ]
    
        # Careful here! Will delete all existing outputs if true
        if del_exist:

            # Delete standard output files
            llgeo_fls.delete_contents(stage + '/', ['out', 'bug', 'acc', 'str'])

            # Delete pickle outputs
            outpkls = [f for f in os.listdir(stage + '/')
                               if f.endswith('_outputs.pkl')]
            [os.remove(stage + '/' + f) for f in outpkls]

    # Run in parallel
    runQ4Ms_parallel(dq4ms, dwrks, douts, fq4rs, fdats, fouts, fbugs, nthreads,
                     post, del_txt)

    # Return back to original working directory
    os.chdir(ini_path)

    return True


# ------------------------------------------------------------------------------
# Running a single QUAD4M file
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
    dir_out : str
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


def runpostQ4M(dir_q4m, dir_wrk, dir_out, file_q4r, file_dat, file_out,
               file_bug, del_txt = False):
    '''Runs a QUAD4M analysis and immediately post-processes the outputs.
        
    Purpose
    -------
    This is a wrapper function for "runQ4M" (this module) and "postprocessQ4M"
    (in "post_process.py" module).
    
    When a large amount of models are being run, the large input/output files
    required for the QUAD4M analyses can take up too much space. To avoid this,
    one can run the analyses then immediately extract the needed outputs to a
    python-friendly format, then delete the text files to save memory.  

    IMPORTANT: I ALWAYS ASSUME THAT ALL THE FILES HAVE THE SAME NAME FOR A GIVEN
    MODEL, AND THAT THE EXTENSION ARE: .q4r, .dat, .shk, .out, .bug, .acc, .str
    
    NOTE: See the documentation in the functions "runQ4M" and "postprocessQ4M"
          for detailed explanation on how these functions work. 

    Parameters
    ----------
    dir_q4m : str
        path containing the file 'Quad4MU.exe'. Note that the current
        directory will be changed to this location while running this function. 
    
    dir_wrk : str
        path to working directory, where .q4r and .dat files are stored
         for this simulation. MUST BE relative to dir_q4m.
    
    dir_out : str
        path to output directory, where QUAD4M outputs will be stored.
        MUST BE relative to dir_q4m.
    
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

    del_txt : bool (optional)
        if true, all quad4M input and output files for this analysis will be
        deleted. Defaults to false. Note that the files will only be deleted
        if the model was deemed to finish succcessfully, so that errors can be
        properly debugged.

    Returns
    -------
    outputs : dict
        (Direct output from "postprocessQ4M") 
        Dictionary of outputs from the model, where the contents depend on the
        provided flags.
        If no flags are given, dictionary will include:
            ['model', 'run_success', 'peak_str', 'peak_acc', 'eq_props', 'Ts',
            'acc_hist', 'str_hist']
    '''

    # Run the analysis
    ran_check = runQ4M(dir_q4m, dir_wrk, dir_out, file_q4r, file_dat, file_out,
                       file_bug)

    # Post-process (Note that dir_out should always be relative to dir_q4m, 
    # which is why I combine them when calling this function.)
    # I ASSUME ALL FILES HAVE THE SAME NAME!!!!!! ¯|_(ツ)_|¯
    model = file_out.replace('.out', '')
    if ran_check:
        output = q4m_post.postprocessQ4M(model_path = dir_q4m + dir_out,
                                         model_name = model,
                                         out_path   = dir_q4m + dir_out,
                                         out_file   = model + '_out.pkl',
                                         del_txt    = del_txt)
    else: 
        output = False
               
    # return :)
    return output


# ------------------------------------------------------------------------------
# Running many QUAD4M files
# ------------------------------------------------------------------------------

def runQ4Ms_series(dq4ms, dwrks, douts, fq4rs, fdats, fouts, fbugs,
                   t = False, post = False, del_txt = False):
    '''Given a list of runQ4M inputs, this runs the models in series
       If t = True, it will print progress
       If post = True, it will do the post processing along the way
       if del_txt = True (and post = True), it will delete text files.'''

    inputs = zip(dq4ms, dwrks, douts, fq4rs, fdats, fouts, fbugs)

    for i, args in enumerate(inputs):

        if post:
            args += (del_txt, )
            _ = runpostQ4M(*args)
        else:
            _ = runQ4M(*args)
        
        if t:
            print('Thread {:d} processed model: '.format(t) +\
                   fq4rs[i].replace('.q4r', ''), flush = True)

    return True


def runQ4Ms_parallel(dq4ms, dwrks, douts, fq4rs, fdats, fouts, fbugs, nthreads,
                     post = False, del_txt = False):
    ''' Given a list of runQ4M inputs, this runs the models in parallel

    Steps:
        1) Split models to run in n groups (n = "num_workers") of roughly the 
           same size.
        2) Initialize a thread for each group, where the target is running the
           models within that group in series.
        3) Start each thread, then join right after.

    Structure:

               ____ thread 1 ____ thread 1 __...__ thread 1 ____
              |      sim 1         sim 2             sim n      |
              |                                                 |
              |                                                 |
              |____ thread 2 ____ thread 2 __...__ thread 2 ____|
    start ----|      sim 1          sim 2            sim n      | ---- join
              |                                                 |
              |                                                 | 
              .                                                 .
              |____ thread m ____ thread m __...__ thread m ____|
                     sim 1            sim 2         sim n

    
       If post = True, it will do the post processing along the way
       if del_txt = True (and post = True), it will delete text files.

    '''

    # Make sure that the lists of inputs are the same size
    arg_keys = ['dq4ms', 'dwrks', 'douts', 'fq4rs', 'fdats', 'fouts', 'fbugs']
    arg_vals = [  dq4ms,   dwrks,   douts,   fq4rs,   fdats,   fouts,  fbugs]

    lengths = [len(i) for i in arg_vals]
    if len(np.unique(lengths)) > 1:
        mssg  = 'Error in running QUAD4M in parallel\n'
        mssg += 'All arguments must be of the same length'
        raise Exception(mssg)

    # Split arguments into n groups (n = "nthreads") of approx. same size 
    #   See: tinyurl.com/8knf90ek 
    #   Grouped arguments are turned into dictionary so that they may be passed
    #   as keyword arguments to the series runner 
    stop = 0
    grouped_args = []
    q, r = divmod(len(dq4ms), nthreads)

    for i in range(1, nthreads + 1):
        start = stop
        stop += q + 1 if i <= r else q
        grouped_args +=[{k : v[start:stop] for k, v in zip(arg_keys, arg_vals)}]

    # Print starting confirmation
    print('\nStarting {:d} Threads to Process {:d} Simulations'.\
           format(nthreads, len(dq4ms)))
    print('\t(~{:d} Simulations per Thread)'.format(q))
    if post:
        print('\tFiles will be post-processed along the way.')
    if post & del_txt:
        print('\tText files will be deleted')
        print('\tA pickle per model will be saved\n')
    
    # Create a thread for each group
    ts = []
    for i, ga in enumerate(grouped_args):
        print('\nThread {:d} will run:'.format(i + 1))
        print([f.replace('.q4r', '') for f in ga['fq4rs']])
        ga.update({'t': i + 1, 'del_txt': del_txt, 'post': post})
        t = Thread(target = runQ4Ms_series, kwargs = ga)
        ts.append(t)

    # Run and time :)
    start = time.time()
    [t.start() for t in ts]
    [t.join() for t in ts]
    end = time.time()

    # Print ending confirmation and return
    print('Concluded all sims in '+ str(int(end-start)) +' sec')

    
# ------------------------------------------------------------------------------
# To keep track of memory
# ------------------------------------------------------------------------------
# Just used these once to check that memory use wasn't crazy when initializing
# many instances of wine. Didn't end up being much of a problem.

def run_QUAD4Ms_series_mem(dq4ms, dwrks, douts, fq4rs, fdats, fouts, fbugs,
                           nthreads = None):
    ''' Wrapper for run_QUAD4Ms_series that also tracks memory usage '''

    args = (dq4ms, dwrks, douts, fq4rs, fdats, fouts, fbugs)
    mem = memory_usage(proc = (runQ4Ms_series, args), interval = 0.5, 
                                timeout = 2, include_children = True)
    return np.max(mem)


def run_QUAD4Ms_parallel_mem(dq4ms, dwrks, douts, fq4rs, fdats, fouts, fbugs,
                           nthreads):
    ''' Wrapper for run_QUAD4Ms_parallel that also tracks memory usage '''

    args = (dq4ms, dwrks, douts, fq4rs, fdats, fouts, fbugs, nthreads)
    mem = memory_usage(proc = (runQ4Ms_parallel, args), interval = 0.5, 
                                timeout = 2, include_children = True)

    return np.max(mem)