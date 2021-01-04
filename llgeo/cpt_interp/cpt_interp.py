''' Interpretation of CPT tests

DESCRIPTION:
These functions help process results of CPT tests based on published studies.
THIS IS A SIMPLE COPY FROM A PREVIOUS PROJECT AND NEEDS CAREFUL REVISION IF IT IS
TO BE USED AGAIN. I WAS LAZY-CODING WHEN I FIRST DID THIS.

FUNCTIONS:
This module contains the following (main) functions:
    * robertson2015_interp
    * robertson2016_type
    * robertson2016_SBTchart
    * robertson2016_structchart

'''
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import rcParams
from matplotlib.ticker import FuncFormatter
rcParams.update({'figure.autolayout': True})
sns.set()
plt.style.use('seaborn-bright')

# ------------------------------------------------------------------------------
# Main Functions
# ------------------------------------------------------------------------------
def robertson2015_interp(d,qc,fs,u2,Pa,Ww,WTD,a,A):
    qt = qc + u2*(1-a)   # Corrected resistance (Pg.22)
    ft = fs - u2*A       # Corrected friction (Pg.23)
    Rf = 100*fs/qt       # Friction ratio (Pg. 36)

    Ws,s_tot,u,s_eff,Ic,n,Fr,qn,Qtn = iter(d,qt,fs,WTD,Ww,Pa) # Iterative calculations (Pg.108)
    Qt = qn/s_eff                                             # Normalized resistance (Pg.29)
    alpha_vs = 10**(0.88*Ic+1.68) 
    Vs = (alpha_vs*qn/Pa)**(0.5)
    Go = Ws/9.81*Vs**2

    results = pd.DataFrame(np.stack([Ws,s_tot,u,s_eff,Ic,n,ft,Rf,Fr,qt,qn,Qt,Qtn,Vs,Go],axis=1),
                           columns=['gamma','s_tot','pore_press','s_eff','Ic','n','ft','Rf','Fr',
                                    'qt','qn','Qt','Qtn','Vs','Go'])
    return(results)


def robertson2016_type(qn,Qtn,Fr,Go):
    ''' Classifies soil according to Robertson's 2016
        SBTn charts'''
    Ig  = Go/qn
    Kgs = (Go/qn)*(Qtn)**(0.75)
    CD  = (Qtn-11)*(1+0.06*Fr)**17
    Ib  = 100*(Qtn+10)/(Qtn*Fr+70)

    stru = np.array(len(Kgs)*['Ideal'],dtype=object)
    beh  = np.array(len(Kgs)*['C'])
    type = np.array(len(Kgs)*['T'])

    stru[Kgs>=330] = 'Struct'     
    beh[CD>70]     = 'D'    
    type[Ib>32]    = 'S'
    type[Ib<22]    = 'C'

    soil = np.array([[t+b] for t,b in zip(type,beh)],dtype=object)
    soil[(Fr<=2)&(Qtn<=10)] = 'CCS'
    soil = soil.flatten()
    
    results = pd.DataFrame(np.stack([Ig,Kgs,stru,soil],axis=1),
                           columns=['Ig','Kgs','Struct','Soil_Type'])
    return(results)


 def robertson2016_SBTchart(fig,ax):
    ''' Plots Robertson's proposed Soil Behavior Type charts.
        Returns figure and axis handles '''

    # Calculate zone boundaries defined by Robertson
    Qtn_CD = lambda Fr,CD: CD/(1+0.06*Fr)**17 + 11
    Fr_Ib  = lambda Qtn,Ib: (1/Qtn)*(100*(Qtn+10)/Ib-70)
    Ib_low  = Fr_Ib(np.logspace(.99,3),22)  # Ib = 22 line
    Ib_high = Fr_Ib(np.logspace(1,3),32)    # Ib = 32 line
    CD  = Qtn_CD(np.logspace(-1,1),70)      # CD = 70 line
    CCS = np.array([[0.1,10],[2,10],[2,1]]) # CCS lines

    # Create figure and establish formatting
    fig.patch.set_facecolor('white')
    ax.set_xscale('log');       ax.set_yscale('log')
    ax.set_xlim([0.1,10]);      ax.set_ylim([1,1000])    
    ax.set_xlabel('$F_r$ (%)'); ax.set_ylabel('$Q_{tn}$ ( - )')
    ax.grid(which='both',color=(0.95,0.95,0.95),linestyle='-') # Add gridlines
    ax.set_axisbelow(True) # Otherwise gridlines plot on top
    ax.tick_params(labelsize=10)
    for axis in [ax.xaxis, ax.yaxis]: # changes scientific to number (stolen from StackOverflow)
        formatter = FuncFormatter(lambda y, _: '{:.16g}'.format(y))
        axis.set_major_formatter(formatter)

    # Plot zone boundaries defined by Robertson
    ax.plot(Ib_low,np.logspace(.99,3),'-k') # Ib = 22 line
    ax.plot(Ib_high,np.logspace(1,3),'-k')  # Ib = 32 line
    ax.plot(np.logspace(-1,1),CD,'-k')      # CD = 70 line
    ax.plot(CCS[:,0],CCS[:,1],'-k')         # CCS lines

    # Add zone labels
    ax.text(5.0e-1,2.2e2,'SD');   ax.text(2.5e-1,2.9e1,'SC')
    ax.text(2.8e+0,7.9e1,'TD');   ax.text(1.3e+0,1.4e1,'TC')
    ax.text(5.0e+0,5.0e1,'CD');   ax.text(4.0e+0,3.0e0,'CC')
    ax.text(3.5e-1,3.0e0,'CCS')

    return(fig,ax)


def robertson2016_structchart(fig,ax):
    ''' Plots Robertson's proposed microstructure chart.
        Returns figure and axis handles '''

    # Calculate zone boundaries defined by Robertson
    Qtn_Kg = lambda Ig,Kg: (Kg/Ig)**(1/0.75)
    Kg_low  = Qtn_Kg(np.logspace(0,3),100)
    Kg_high = Qtn_Kg(np.logspace(0,3),330)
    
    # Create figure and establish formatting
    fig.patch.set_facecolor('white')
    ax.set_xscale('log'); ax.set_yscale('log')
    ax.set_xlim([1,1e3]); ax.set_ylim([1,1e3])    
    ax.set_xlabel('$I_G =G_o/q_n$ ( - )'); ax.set_ylabel('$Q_{tn}$ ( - )')
    ax.grid(which='both',color=(0.95,0.95,0.95),linestyle='-') # Add gridlines
    ax.set_axisbelow(True) # Otherwise gridlines plot on top
    ax.tick_params(labelsize=10)
    for axis in [ax.xaxis, ax.yaxis]: # changes scientific to number (stolen from stackoverfow)
        formatter = FuncFormatter(lambda y, _: '{:.16g}'.format(y))
        axis.set_major_formatter(formatter)

    # Plot zone boundaries defined by Robertson
    ax.plot(np.logspace(0,3),Kg_low,'--k')
    ax.plot(np.logspace(0,3),Kg_high,'-k')

    # Add zone labels
    ax.text(4.7e1,1.2e0,'$K_G^*$=100',fontsize=8,rotation=-66,
            bbox={'facecolor':'white','edgecolor':'none','pad':0,'alpha':1})
    ax.text(1.6e2,1.2e0,'$K_G^*$=330',fontsize=8,rotation=-66,
            bbox={'facecolor':'white','edgecolor':'none','pad':0,'alpha':1})
    ax.text(1.2e0,3.55e2,'Ideal Soils',fontsize=8,rotation=-68,
            bbox={'facecolor':'white','edgecolor':'none','pad':0,'alpha':1})
    ax.text(1.5e1,1e2,'Soils with \n Microstructure',fontsize=8,rotation=0,
            bbox={'facecolor':'white','edgecolor':'none','pad':0,'alpha':1})

    return(fig,ax)


# ------------------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------------------
def iter(d_arr,qt_arr,fs_arr,WTD,Ww,Pa):

    # Initialize empty result arrays
    Ws_arr=np.empty(np.shape(d_arr));   n_arr=np.empty(np.shape(d_arr))
    Ic_arr=np.empty(np.shape(d_arr));   qn_arr=np.empty(np.shape(d_arr))
    u_arr=np.empty(np.shape(d_arr));    Qtn_arr=np.empty(np.shape(d_arr))
    Fr_arr=np.empty(np.shape(d_arr));   s_tot_arr=np.empty(np.shape(d_arr))
    s_eff_arr=np.empty(np.shape(d_arr))

    # Initialize stresses and calc. depth diff
    delta_arr = np.append(d_arr[0],d_arr[1:]-d_arr[:-1])
    s_tot = s_eff = 1e-5

    # Go through each row and do iterative calculations (Pg.108)
    for i,(d,qt,fs,delta) in enumerate(zip(d_arr,qt_arr,fs_arr,delta_arr)):
        n_new = diff = e = 1   # Reset iteration controls
        u = max(0,Ww*(d-WTD))  # Calculate pore pressures
        while(diff>0.01)&(e<5000):
            e     += 1
            n      = n_new
            qn     = max(0.01,qt - s_tot)                                  # Net resistance (Pg.28)
            Fr     = 100*fs/qn                                             # Normalized friction ratio (Pg.29)
            Qtn    = qn/Pa*(Pa/s_eff)**n                                   # Normalized resistance (Pg.108)
            Ic     = ((3.47-np.log(Qtn))**2 + (1.22+np.log(Fr))**2)**0.5   # Soil index (Pg.108)
            n_new  = max(0,min(1,0.381*Ic+0.05*(s_eff/Pa)-0.15))           # Norm exponent (Pg.108)
            Ws     = Ws_lookup(Ic)
            s_temp = s_tot + delta*Ws
            s_eff  = s_temp - u
            diff   = np.abs(n-n_new)
        s_tot = s_temp         # Update total stress
        Ws_arr[i]=Ws; s_tot_arr[i]=s_tot; u_arr[i]=u
        s_eff_arr[i]=s_eff; Ic_arr[i]=Ic; n_arr[i]=n
        Fr_arr[i]=Fr; qn_arr[i]=qn; Qtn_arr[i]=Qtn

    return(Ws_arr,s_tot_arr,u_arr,s_eff_arr,Ic_arr,n_arr,Fr_arr,qn_arr,Qtn_arr)


def Ws_lookup(Ic):
    ''' Assumed soil unit weight
        based on calculated Ic'''
    Ws = 19
    if np.isnan(Ic):  Ws = 19
    if 0.00<Ic<=1.31: Ws = 20
    if 1.31<Ic<=2.05: Ws = 19
    if 2.04<Ic<=2.30: Ws = 18.5
    if 2.30<Ic<=2.60: Ws = 18.0
    if 2.60<Ic<=2.95: Ws = 17.5
    if 2.95<Ic<=3.60: Ws = 16.6
    if 3.60<Ic<=6.00: Ws = 11.0
    return(Ws)