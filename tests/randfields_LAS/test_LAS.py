'''
TITLE:     test_LAS.py
TASK_TYPE: test
PURPOSE:   Carries out workflow for generating random field simulations from
           python using wrapped F77 functions from Dr. Fenton. 
           Pretty straightforward.
           
LAST_UPDATED: 06 December 2020
STATUS: WIP
TO_DO:
    * Code works but it's quite UGLY... could use some cleaning up
       and proper editing of the plots
'''

#%% Import modules
# Standard Python modules
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Import LLGEO modules
import llgeo.randfields.LAS as LAS


#%% Example of 2D simulations

# Start off with simple one
k1  = 4
k2  = 2
m   = 1
n1  = k1*2**m
n2  = k2*2**m
xl  = n1
yl  = n2
thx = xl
thy = yl/n2
zm  = 10
zv  = 5**2
fnc = 'dlavx2'
pa  = zv
pb  = 0
sms = 7
sed = 5
out = 'sim.stats' 

Zs = LAS.sim2d(n1, n2, xl, yl, zm, zv, thx, thy, fnc, pa, pb, sms, out, sed)


plt.plot(Zs[0], '-ok')
# plt.plot(Zs[0][0:n1*n2], '-r')

z = Zs[0]
for j in range(n2):
    x = np.arange(n1*j, n1*(j+1))
    plt.plot(x, z[n1*j:n1*(j+1)], ':')










#%%
# Let's start off with a  simple simulation:

# 

help(LAS.sim2d)

m  = 3
k1 = 15
k2 = 10
n1 = k1*2**m
n2 = k2*2**m

xl = 100  # Physical size of the process in x direction
yl = 100  # Physical size of the process in y direction

zm  = 0       # Mean of the process
zv  = 1       # Point variance of the process
thx = 1000    # Correlation length (x direction)
thy = 10      # correlation length (y direction)

fncnam = 'dlavx2' # Correlation function
pa = zv           # First parameter for correlation function 
pb = 0            # Second parameter for correlation function (unused)

nsims = 1
kseed = 66
iout  = 6

Zs = LAS.sim2d(n1, n2, xl, yl, zm, zv, 1, 1, fncnam, pa, pb, nsims, kseed, iout)
z = Zs[0]
plt.figure()
plt.imshow(z.T, origin = 'lower')


Zs = LAS.sim2d(n1, n2, xl, yl, zm, zv, 10, 10, fncnam, pa, pb, nsims, kseed, iout)
z = Zs[0]
plt.figure()
plt.imshow(z.T, origin = 'lower')

Zs = LAS.sim2d(n1, n2, xl, yl, zm, zv, 1, 10, fncnam, pa, pb, nsims, kseed, iout)
z = Zs[0]
plt.figure()
plt.imshow(z.T, origin = 'lower')

Zs = LAS.sim2d(n1, n2, xl, yl, zm, zv, 10, 1, fncnam, pa, pb, nsims, kseed, iout)
z = Zs[0]
plt.figure()
plt.imshow(z.T, origin = 'lower')

# %%





































# -- Example of 1D simulations
help(LAS.sim1d)

n  = 100 # Number of cells
xl = 50  # Physical size of the process
zm = 10  # Mean of the process
zv = 2   # Point variance of the process
thx = 10 # Correlation length (x directon)

fncnam = 'dlavx1' # Correlation function
pa = zv           # First parameter for correlation function 
pb = 0            # Second parameter for correlation function (unused)

nsims = 50
kseed = 33
iout  = 2

Zs = LAS.sim1d(n, xl, zm, zv, thx, fncnam, pa, pb, nsims, kseed, iout)

plt.figure()
[plt.plot(np.linspace(0, xl, n), z) for z in Zs]

plt.figure()
[sns.distplot(z, hist = False) for z in Zs]


# check what a smaller correlation length looks like
thx2 = 1 # Correlation length (x directon)
Zs2 = LAS.sim1d(n, xl, zm, zv, thx2, fncnam, pa, pb, nsims, kseed, iout)

plt.figure()
[plt.plot(np.linspace(0, xl, n), z) for z in Zs2]

plt.figure()
[sns.distplot(z, hist = False) for z in Zs2]
