''' Functions to model simple markov chains

DESCRIPTION:
Functions to model simple markov chains

FUNCTIONS:
This module contains the following (main) functions:
    * fun_name : one_line_description
                 (only add user-facing ones)

'''
import numpy as np
import llgeo.basic_stats.distributions as llgeo_dist
# ------------------------------------------------------------------------------
# Main Functions
# ------------------------------------------------------------------------------
def fit_sim_MC(processes, num_sims, sims_length):
    P, I = fit_MC(processes)
    xs = sim_MC(num_sims, sims_length, P, I)
    return xs

def fit_MC(processes, return_counts = False):
    ''' Fits a markov chain to describe observed processes.
        
    Purpose
    -------
    Given a list of observed "processes", this returns a transition matrix of 
    size (num_states x num_states), in which element Pij represents the 
    probability of transitioning from state i to state j. It also returns the
    probability of starting the process at any given state.
        
    Parameters
    ----------
    processes : list of arrays of ints
        List of observed processes. Each process must be a list / array of 
        integers denoting the state. IT MUST BE ZERO-INDEXED! The processes may 
        be of different total length, however, THEY MUST HAVE CONSISTENT 
        INTERVALS. (for example, each element corresponds to 1 m depth interval)
                
    Returns
    -------
    P : numpy array
        Matrix of size (num_states x num_states) where element P(i,j) is the 
        probability of transitioning from state i to state j.
        
    I : numpy array
        Vector of size (num_states) where element I(i) is the unconditional 
        probability that the process starts at state i. 

    trans, states, initial
        If return_counts = True, it also returns counting matrices before they
        were changed to probabilities (for debugging purposes only).

    Notes
    -----
    * Not the most sophisticated model... ¯|_(ツ)_|¯
    '''

    # Determine number of possible states
    all_states = np.concatenate(processes, axis = 0)
    num_states = len(np.unique(all_states[~np.isnan(all_states)]))

    if np.min(all_states) > 0:
        print('WARNING! States must be zero-indexed.')
    
    # Initialize matrices 
    states = np.zeros(num_states) # uncond. prob of starting trans. at state
    transitions = np.zeros((num_states, num_states)) # transition prob.
    initial = np.zeros(num_states) # prob. of being in state at process[0]

    # Iterate through each observed process
    for process in processes:
        # Get rid of nans and sure that process is int and not float
        mask = ~np.isnan(process)
        process = np.array(process[mask], dtype = int)

        # Update inital state count
        initial[process[0]]+= 1

        # Iterate through subsequent pairs of observations in process
        for previous, nextt in zip(process[:-1], process[1:]):
            states[previous] += 1 
            transitions[previous, nextt] += 1

    # Turn counts to probabilites
    P = transitions / states.reshape(-1, 1)
    I = initial / len(processes)

    # check that transition matrix makes sense
    check = np.sum(P, axis = 0)
    if sum(check.flatten()) != num_states:
        print('Uh oh, something went wrong')
        print('Sum of rows of check is:')
        print(check)
    
    # Prepare outputs and return
    outputs = (P, I)
    if return_counts:
        outputs += (transitions, states, initial)

    return outputs

def sim_MC(num_sims, sims_length, P, I):
    ''' Returns realizations of a random process using a simple Markov Chain.
        
    Purpose
    -------
    Returns "num_sims" simulations of a random process, each with "sims_length"
    elements, based on transition probabilities P and initial probabilities I.
        
    Parameters
    ----------
    num_sims : int
        Number of realizations to return
        
    sims_length : int
        Length of each simulation.

    P : numpy array
        Matrix of size (num_states x num_states) where element P(i,j) is the 
        probability of transitioning from state i to state j.
        
    I : numpy array
        Vector of size (num_states) where element I(i) is the unconditional 
        probability that the process starts at state i.     
        
    Returns
    -------
    sims : list of arrays
        List of size num_sims where each element is a random field realization.
        
    Notes
    -----
    * Not the most sophisticated model... ¯|_(ツ)_|¯
    '''

    xs = [] # List to store all simulated processes
    
    for _ in range(num_sims):
        x = np.empty(sims_length) # Array to store random process

        # Determine the value of the first element 
        x[0] = llgeo_dist.sample_PMF(num_samples = 1, pmf = I)

        # Iterate through the length of the random process
        for i in range(len(x) - 1):

            # Determine probabity mass function based on "previous" state
            trans_pmf = P[int(x[i]), :]

            # Determine the next state
            x[i + 1] = llgeo_dist.sample_PMF(num_samples = 1, pmf = trans_pmf)

        # Add result to outputs
        xs += [x]

    return xs

    




        




# ------------------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------------------