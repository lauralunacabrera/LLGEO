#%% Import modules
import numpy as np
import pandas as pd

# LLGEO Modules
import llgeo.quad4m.elemprops as q4m_props


#%%
z = np.array([[1, 2, 3], [4, 5, 6]])
elems = pd.DataFrame([])
q4m_props.map_rf(elems, 'test_prop', z)


# %%
-+
39