'''
TITLE:        test_save_outputs.py
TASK_TYPE:    test 
PURPOSE:      check that the function saves dict properly
LAST_UPDATED: 2021-02-19 14:38
'''
#%%
import llgeo.utilities.files as llgeo_fls
import os

# Test output
a = {'a': 1}

# Save
outputs = llgeo_fls.save_outputs('./', 'test.pkl', a, src_name = os.path.basename(__file__))

# Check 
print(outputs)


# %%
