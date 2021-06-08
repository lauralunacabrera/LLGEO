#%%
import numpy as np
import matplotlib.pyplot as plt
import llgeo.rand_fields.LAS as llgeo_rf


# Normal parameters
mean = 1
stdv = 0.24

# Random field input parameters
n      = 30
xl     = 30 
zv     = np.log(1 + (stdv / mean) ** 2)  # Lognormal parameter
zm     = np.log(mean) - 0.5 *zv # Lognormal parameter
fncnam = 'dlavx1' 
pa     = np.log(1 + (stdv / mean) ** 2)  # Lognormal parameter
pb     = 0
nsims  = 1000
kseed  = 514


# Plot Inputs
fig, axes = plt.subplots(1, 3, figsize = (7, 4))
axes[0].plot([1, 1], [0, xl], color = 'k')
axes[1].plot([zv, zv], [0, xl], color = 'k')
axes[2].plot([zv**0.5, zv**0.5], [0, xl], color = 'k', label = 'Input')


# Iterate through different correlation lengths
for thx in [1, 2, 5, 10, 50, 100, 500]:

    # Generate random fields
    Zs = llgeo_rf.sim1d(n, xl, zm, zv, thx, fncnam, pa, pb, nsims, kseed)

    # Concatenate random fields into one array of size (nsims, xl)
    all_rf  = [np.exp(z.reshape(1, -1)) for z in Zs]
    all_rf  = np.concatenate(all_rf, axis = 0)

    # Get mean and standard deviation
    rf_mean = np.mean(all_rf, axis = 0)
    rf_stdv = np.std(all_rf, axis = 0, ddof = 1)
    rf_var  = rf_stdv ** 2

    # Plot Estimated from Simulations
    axes[0].plot(rf_mean, range(len(rf_mean)))
    axes[1].plot(rf_var,  range(len(rf_var)) )
    axes[2].plot(rf_stdv, range(len(rf_stdv)), label = thx)

    # Customize
    [ax.set_ylim([30, 0]) for ax in axes]
    axes[0].set_title('Mean')
    axes[1].set_title('Variance')
    axes[2].set_title('Standard Devation')

    axes[0].set_xlim([0.95, 1.05])
    axes[1].set_xlim([0.00, 0.10])
    axes[2].set_xlim([0.00, 0.50])

axes[-1].legend(loc = 6, bbox_to_anchor = (1, 0.5), edgecolor = 'None')

#%%
