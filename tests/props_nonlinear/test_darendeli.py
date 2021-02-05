#%%
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

import llgeo.props_nonlinear.darendeli_2011 as daren

#
G_img = mpimg.imread('G_norm_check.JPG')
D_img = mpimg.imread('D_mas_check.JPG')

PI = 60      # Plastic Index (%)
OCR = 4      # Overconsolidation Ratio ( - )
sigma_o = 4  # In-situ mean effective stress
N = 10       # Number of loading cycles ( - )
frq = 10      # Loading frequency

gam = np.logspace(-4, 0, 100)
G_red, D_adjs, a, b, D_min, sstrn_r = daren.curves(gam, PI, OCR, sigma_o, N, frq, type = 'mean')

#

fig, axes = plt.subplots(2, 1, figsize = (4.4, 5))

ax_Gfig = axes[0].twinx().twiny()
ax_Gfig.imshow(G_img)

axes[0].plot(gam, G_red, '--r')
axes[0].set_zorder(ax_Gfig.get_zorder()+1) # put ax in front of ax2
axes[0].patch.set_visible(False) # hide the 'canvas'
ax_Gfig.set_xticks([])
ax_Gfig.set_yticks([])

ax_Dfig = axes[1].twinx().twiny()
ax_Dfig.imshow(D_img)
axes[1].plot(gam, D_adjs, '--g')
axes[1].set_zorder(ax_Dfig.get_zorder()+1) # put ax in front of ax2
axes[1].patch.set_visible(False) # hide the 'canvas'
ax_Dfig.set_xticks([])
ax_Dfig.set_yticks([])


[ax.set_xscale('log') for ax in axes]
[ax.set_xlim(10**-4, 19**0) for ax in axes]
axes[0].set_ylim(0, 1.2)
axes[1].set_ylim(0, 25)
# %%
