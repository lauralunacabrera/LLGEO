# TRANSITION TO OBJECT-ORIENTED PROGRAMMING ... ON PAUSE FOR NOW


import numpy as np


class node:

    def __init__(self, n, i, j, x, y):

        # Node geometry
        self.n = n
        self.i = i
        self.j = j
        self.x = x
        self.y = y

        # Boundary conditions
        self.BC = np.nan

        # 


class elem:

    def __init__(self, n, i, j, xc, yc, N1, N2, N3, N4, shape, soil):
        
        # Element numbering and location
        self.n = n
        self.i = i
        self.j = j
        self.xc = xc
        self.yc = yc

        # Node numbering
        self.N1 = N1
        self.N2 = N2
        self.N3 = N3
        self.N4 = N4

        # Shape (triangular or quadrilateral) and type of soil
        self.shape = shape
        self.soil  = soil

        # Basic descriptions
        self.id   = ''
        self.name = ''
        self.desc = ''

        # Non-linear properties
        self.G_strn = np.emtpy([])
        self.G_mred = np.emtpy([])
        self.D_strn = np.emtpy([])
        self.D_damp = np.emtpy([])

#%%

#%% Import modules

# Import standard pacakges
import numpy as np
import pandas as pd

# Import LLGEO modules
import llgeo.quad4m.geometry as geom
import llgeo.quad4m.genfiles as q4m_files

#%% STEP #1 --------------------------------------------------------------------
#   Obtain model geometry from DXF file
print('Generating geometry')
nodes, elems = geom.dxf_to_dfs('../quad4m_genfiles_q4r/CAD/', '01_01.dxf')  # Read dxf and create dfs


class model():

    def __init__(self, nodes, elems):

        # Initialize node information
        self.nodes = []

        for _, n in nodes.iterrows():
            node(n['node_n'], n['node_i'], n['node_j'], n['node_x'], n['node_y'])

            self.nodes += node(n, i, j, )



#         self.nodes = [node(n, i, j, x, y)]


# %%
