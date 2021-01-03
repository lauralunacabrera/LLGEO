#%%
import llgeo.quad4m.elemprops as q4m_props
import llgeo.quad4m.db_utils as q4m_db
import llgeo.quad4m.geometry as q4m_geom

import matplotlib.pyplot as plt

#%%

# Get nodes and elems to play with
dxf_path = './CAD/'
dxf_inf  = 'test_dike.dxf'
nodes, elems = q4m_geom.dxf_to_dfs(dxf_path, dxf_inf, lay_id = 'Soil_')


# Add boundary conditions, acceleration outputs, and initial conditions
acc_locations = [(0, 'all'), (1, 'all'), (0.5, 'all')]

nodes = q4m_props.add_bound_conds('rigidbase_box', nodes)
nodes = q4m_props.add_acc_outputs(acc_locations, 'X', nodes)
nodes = q4m_props.add_ini_conds([], [], nodes)

props = {'unit_w': 21000,
         'po'    : 0.450,
         'Gmax'  : 21000/9.81*170**2/1000}
elems = q4m_props.add_uniform_props


fig, ax = plt.subplots()
sc = plt.scatter(nodes['x'], nodes['y'], s = 10, c = nodes['BC'])
fig.colorbar(sc)
ax.set_title('Boundary Conditions')


fig, ax = plt.subplots()
sc = plt.scatter(nodes['x'], nodes['y'], s = 10, c = nodes['OUT'])
fig.colorbar(sc)
ax.set_title('Acceleration Outputs')


#%%


# %%
