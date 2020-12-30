'''
TITLE:     
TASK_TYPE: 
PURPOSE:              
LAST_UPDATED: 15 December 2020
STATUS: 
TO_DO:
'''
#%% Import modules

# Import standard pacakges
import numpy as np
import pandas as pd
import scipy.stats as stats
import matplotlib.pyplot as plt

# Import LLGEO modules
import llgeo.quad4m.geometry as q4m_geom
import llgeo.quad4m.genfiles as q4m_files
import llgeo.quad4m.elemprops as q4m_props
import llgeo.randfields.LAS as sim_LAS

#%% Check function "elem_stresses"

# Information on CAD Files
dxf_path = './CAD/'
dxf_inf  = 'test_dike.dxf'
dxf_outf = dxf_inf.replace('.dxf', '_out.dxf')

# Obtain model geometry from DXF file
nodes, elems = q4m_geom.dxf_to_dfs(dxf_path, dxf_inf, lay_id = 'Soil_')

# Now, create a test random field. As noted in docs, the random field should be
# indexed as follows:
#       Z(1, 1) - low left corner
#       Z(1, 2) - next element in n2 direction, i.e., directly above
#       Z(2, 1) - next element in n1 direction, i.e., directly to the right
# I will create a random field where the random value is equal to the element
# number so that it makes it easy to test the mapping.
Z = np.arange(0, 40).reshape(8, 5, order = 'F')
Z = Z + np.ones(np.shape(Z)) # 1-indexed fix

# Now, map this random field to the elems table
elems = q4m_props.map_rf(elems, 'mapZ', Z)

# Output the results to a DXF, including the new mapped column, to check that
# everything makes sense.
q4m_geom.dfs_to_dxf(dxf_path, dxf_outf, nodes, elems, elems_add_col = 'mapZ')

#%%
# Get stresses 
elems = q4m_props.elem_stresses(nodes, elems)

# Quick plotting checks
fig, ax = plt.subplots(1,1)
sc = ax.scatter(elems['xc'], elems['yc'], s = 10, c = elems['unit_w'])
fig.colorbar(sc)

fig, ax = plt.subplots(1,1)
sc = ax.scatter(elems['xc'], elems['yc'], s = 10, c = elems['sigma_v'])
fig.colorbar(sc)


fig, ax = plt.subplots(1,1)
sc = ax.scatter(elems['xc'], elems['yc'], s = 10, c = elems['sigma_m'])
fig.colorbar(sc)

#%% Check function "LAS_to_elems"
prop_name = 'Vs'

xcs = np.sort(np.unique(elems['xc']))
ycs = np.sort(np.unique(elems['yc']))

n1_real = len(xcs)
n2_real = len(ycs)

xl = np.max(xcs) - np.min(xcs)
yl = np.max(ycs) - np.min(ycs)

dx, countx = stats.mode(xcs[1:] - xcs[:-1])
dy, county = stats.mode(ycs[1:] - ycs[:-1])

dx = float(dx); countx = float(countx)
dy = float(dy); county = float(county)

k1 = 25
k2 = 8
m = 2
n1_gen = k1*2**m
n2_gen = k2*2**m

zm = 0
zv = 1
thx = 10*xl/n1_gen
thy = yl/n2_gen
fnc = 'dlavx2'
nsim = 3
seed = np.random.randint(0, 20)
pa = zv
pb = 0

if countx < len(xcs) - 1:
    print('Warning: unevenly spaced elements in x direction')
    print('         using dx = {:3.2f}'.format(dx))

if county < len(ycs) - 1:
    print('Warning: unevenly spaced elements in y direction')
    print('         using dy = {:3.2f}'.format(dy))

if n1_real > n1_gen:
    print('Warning: real n1 is larger than generated n1.')

if n2_real > n2_gen:
    print('Warning: real n2 is larger than generated n2.')

#%%
k1 = 2
k2 = 4
m = 2
n1_gen = k1*2**m
n2_gen = k2*2**m

xl = 10
yl = 10

zm = 0
zv = 1
thx = 10*xl/n1_gen
thy = yl/n2_gen
fnc = 'dlavx2'
nsim = 3
seed = np.random.randint(0, 20)
pa = zv
pb = 0

# TODO: these tests are broken... fix!
# # RFs = sim_LAS.sim2d(n1_gen, n2_gen, xl, yl, zm, zv, thx, thy,
#                 #    fnc, pa, pb, nsim, seed)

# # RFs = [rf[0:n1_real, 0:n2_real] for rf in RFs]

# for rf in RFs:
#     plt.figure()
#     plt.imshow(rf.T)

# #%%
# # number elements
# rf = RFs[-1]
# ids = np.zeros(np.shape(rf))
# n = 0

# for i in range(n1_real):
#     for j in range(n2_real):
#         n += 1
#         ids[i,j] = n

# rff = rf.flatten()

# elems = elems.sort_index()
# elems['rand'] = rf.flatten()

# plt.figure()
# plt.scatter(elems['xc'], elems['yc'], s = 5, c = elems['rand'])
# plt.ylim([30, 0])

# # %%
# diffs = []
# for i in ids.flatten():
#     from_rf = rf[ids==i]
#     from_df = float(elems.loc[elems['n']==i, 'rand'])
#     diffs.append(from_rf - from_df)

# plt.plot(diffs)

