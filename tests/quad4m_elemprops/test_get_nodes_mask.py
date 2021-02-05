#%%
import llgeo.quad4m.props_elems as q4m_elems
import llgeo.quad4m.db_utils as q4m_db
import llgeo.quad4m.geometry as q4m_geom

import matplotlib.pyplot as plt
import numpy as np

# Get nodes and elems to play with
dxf_path = './CAD/'
dxf_inf  = 'test_dike.dxf'
nodes, elems = q4m_geom.dxf_to_dfs(dxf_path, dxf_inf, lay_id = 'Soil_')

# Add boundary conditions, acceleration outputs, and initial conditions
acc_locations = [(0, 'all', 'dec'), (1, 'all', 'dec'), (0.5, 'all', 'dec')]
jwater = 3
props_ini = [{'unit_w' : 21000, 'po' : 0.450, 'PI' : 0, 'OCR' : 1},
             {'unit_w' : 19000, 'po' : 0.450, 'PI' :15, 'OCR' : 1}]

nodes = q4m_elems.add_bound_conds('rigidbase_box', nodes)
nodes = q4m_elems.add_acc_outputs(acc_locations, 'X', nodes)
nodes = q4m_elems.add_ini_conds([], [], nodes)

elems = q4m_elems.map_layers(elems, np.zeros(len(elems)))
elems = q4m_elems.add_uniform_props(props_ini, elems)
elems = q4m_elems.add_watertable(jwater, elems)
elems = q4m_elems.elem_stresses(nodes, elems)

#%%
# props = {'unit_w': 21000,
#          'po'    : 0.450,
#          'Gmax'  : 21000/9.81*170**2/1000}
# elems = q4m_elems.add_uniform_props


fig, ax = plt.subplots()
sc = plt.scatter(nodes['x'], nodes['y'], s = 10, c = nodes['BC'])
fig.colorbar(sc)
ax.set_title('Boundary Conditions')

fig, ax = plt.subplots()
sc = plt.scatter(elems['xc'], elems['yc'], s = 10, c = elems['sigma_m'])
fig.colorbar(sc)
ax.set_title('Unit W')


fig, ax = plt.subplots()
sc = plt.scatter(nodes['x'], nodes['y'], s = 10, c = nodes['OUT'])
fig.colorbar(sc)
ax.set_title('Acceleration Outputs')


#%%


# %%
