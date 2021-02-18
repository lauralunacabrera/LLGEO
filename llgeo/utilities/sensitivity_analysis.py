''' Utilities to carry out sensitivty analysis

DESCRIPTION:
These are pretty simple functions that help carry out sensitivity analyses
for geotechnical analyses. 

'''
import numpy as np
import pandas as pd

# ------------------------------------------------------------------------------
# Main Functions
# ------------------------------------------------------------------------------
def generate_scenarios(variables):
    ''' Generates list of scenarios given variables with different possible vals
        
    Purpose
    -------
    This is a very simple function used to generate possible scenarios based on
    a list of variables. Each variable has a single "base case" and a list of
    possible "scenarios".

    First, a "base-case" scenario is completed by adding the base-case of all 
    provided variables. Then, the different options are iterated through for
    each variable, while keeping all others at the base-case.
        
    Parameters
    ----------
    variables : list of dict
        List of dictionaries where each dict corresponds to a variable. Each
        dict must have keys: 'name', 'base_case', and 'scenarios'.
        
    Returns
    -------
    scenarios : dataframe
        Dataframe with different combinations of variables, where each variable
        scenario is considered against the base-case scenario of others.
        It's hard to explain... see example.

        a = {'name': 'apples',   'base_case': 2, 'scenarios': [1, 3, 4]}
        b = {'name': 'bannanas', 'base_case': 5, 'scenarios': [6, 7]}

        would yield a dataframe:

      | id | main_var  | apples | bannanas | (header based on 'name')
      |----|-----------|--------|----------|
      | 1  | base-case |    2   |     5    | (base case for all variables)
      | 2  | apples    |    1   |     5    | (vary "apples"; others base case)
      | 3  | apples    |    3   |     5    | (vary "apples"; others base case)
      | 4  | apples    |    4   |     5    | (vary "apples"; others base case)  
      | 5  | bannana   |    2   |     6    | (vary "bannanas"; others base case)
      | 6  | bannana   |    2   |     7    | (vary "bannanas"; others base case)

    Notes
    -----
    * This is so that I can examine the sensitivity to different parameters 
      while not blowing up the number of simulations to complete to an
      unfeasible number.
    '''

    # First, add the scenario where all values = base_case
    base_case = ['base_case'] + [v['base_case'] for v in variables]

    # Start "scenarios" list, which will include results
    scenarios = [base_case]

    # Iterate through the provided variables
    for i, var in enumerate(variables):

        # Iterate through the 'scenarios' provided for this variable
        for new_val in var['scenarios']:
            
            # Come up with parameters of the new "scenario"
            new_scenario = base_case.copy() # Start with base-case
            new_scenario[0] = var['name'] # Change label to currrent variable
            new_scenario[i+1] = new_val # Update to new value for given variable

            # Append to outputs
            scenarios += [new_scenario]

    # Transform list to dataframe so that it includes clear headings
    cols = ['main_var'] + [v['name'] for v in variables]
    scenarios = pd.DataFrame(scenarios, columns = cols )

    # Add "id" (one-indexed)
    scenarios['id'] =  1 + np.arange(len(scenarios)) 

    return scenarios

# ------------------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------------------