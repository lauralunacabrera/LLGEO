#%%
 
 
import llgeo.basic_stats.distributions as llgeo_dist
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Make up an arbitrary probability mass function
pmf = [0.1, 0.2, 0.7] # probability mass function
x   = np.arange(len(pmf))

# Sample from distribution many times
sim = llgeo_dist.sample_PMF(5000, x, pmf)
sim_x, sim_pmf = np.unique(sim, return_counts = True)
sim_pmf = sim_pmf / len(sim)

# Ensure the PMF is recovered
fig, ax = plt.subplots()
ax.bar(x, pmf, label = 'original') #
ax.bar(sim_x, sim_pmf, color= 'r', label = 'simulated', alpha = 0.4)
ax.legend()


# %%
