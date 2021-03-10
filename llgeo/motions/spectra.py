''' Functions related to response spectra

Great reference source:
    https://tinyurl.com/54j3dwmh
    
'''

import numpy as np
import numpy as np
import scipy as sp
import scipy.linalg

# ------------------------------------------------------------------------------
# Main Functions to get Response Spectra
# ------------------------------------------------------------------------------

def resp_spectra_arduino(a, time, nstep, periods = np.logspace(-3, 1, 100) ):
    ''' Response spectra from acceleration time history.

    TODO - Figure out what is happening with this function.
    DO NOT USE THIS.
    IT DOES NOT WORK PROPERLY.
    Compared it to El Centro data and it doesn't make any sense.
    Not sure what's going on here....
    DO NOT USE THIS.
        
    Purpose
    -------
    This function builds a response spectra from acceleration time history. 
    I DID NOT WRITE THIS. I stole it from Dr. Arduino, Dr. Ghofrani and Dr. Chen
    from DesignSafe data depot: https://tinyurl.com/r8wnhjk9
        
    Parameters
    ----------
    a : numpy array
        Acceleration time history
        
    time : integer
        Time step of the time history
    
    nstep : integer
        Number of steps in the time history

    periods : numpy array
        Vector of periods for which to compute the response. It defualts to a 
        logspace between 10^(-3) and 10, with 100 data points in between.
        
    Returns
    -------
    output_name : output_data_type
        Description of the parameter.
        Include assumptions, defaults, and limitations!
        
    output_name : output_data_type
        Description of the parameter.
        Include assumptions, defaults, and limitations!
        
    Notes
    -----
    * Again: not mine. Came from UW Computational Mechanics Group
    
    ''' 

    # Add initial zero value to acceleration and change units
    a = np.insert(a, 0, 0)

    # Incremental circular frequency
    dw = 2 * np.pi / time

    # Vector of circular frequency
    w = np.arange(0, (nstep + 1)*dw, dw)

    # Fast Fourier Form of Acceleration
    afft = np.fft.fft(a)

    # Arbitrary stiffness value 
    k = 1000

    # Damping ratio
    damp = 0.05

    # Initalize response vectors
    umax, vmax, amax = (np.zeros(len(periods)) for i in range(3))

    # Loop to compute spectral values at each period
    for j, p in enumerate(periods):

        # Compute mass and dashpot coefficient to produce desired periods
        m = ( p / (2 * np.pi))**2 * k
        c = 2 * damp * (k * m)**0.5
        h = np.zeros(nstep + 2, dtype = complex)

        # Compute the transfer function
        for L in range(int(nstep/2 + 1)):
            h[L] = 1 / (-m * w[L]**2 + 1j * c * w[L] + k)

            # Mirror image of Her function
            h[nstep+1-L] = np.conj(h[L])
        
        # Compute displacement in frequency domain using Her function
        qfft = -m * afft
        u = np.zeros(nstep + 1, dtype = complex)

        for L in range(nstep+1):
            u[L] = h[L] * qfft[L]

        # Compute displcement in time domain (ignore imaginary part)
        utime = np.real(np.fft.ifft(u))

        # Spectral displacement, velocity, and acceleration
        umax[j] = np.max(np.abs(utime))
        vmax[j] = (2*np.pi/p) * umax[j]
        amax[j] = (2*np.pi/p) * vmax[j]

    return umax, vmax, amax


def resp_spectra_wang(acc, dt, periods, zeta = 0.05):
    ''' Determines the peak response of a linear SDOF
        
    Purpose
    -------
    This script calculates the peak response of an SDOF subject to acc.
    It is a direct translation from the Matlab code included in Wang 1996.
    It take no credit whatsover... and don't really understand all the math.

    Parameters
    ----------
    acc : numpy array
        Acceleration time history with time-step dt
        
    dt : float
        Time step

    periods : numpy array
        Natural periods of vibration of the SDOF

    zeta : float (optional)
        Critical damping ratio to be used in calculations.
        Input as fractional number. Defaults to 0.05 (5% damping)     
        
    Returns
    -------
    SD : numpy array
        Relative displacement response spectrum
        
    PSV : numpy array
        Pseudo-relative-velocity
        
    PSA : numpy array
        Pseudo-absolute-acceleration
        
    SA : numpy array
        Absolute-acceleration
        
    SV : numpy array
        Relative-velocity
        
    ED : numpy array
        Spectra of energy dissipation per unit mass
        
    Notes
    -----
    * I DID NOT WRITE THIS CODE. Just translated it and checked that it works.
        
    Refs
    ----
    * https://tinyurl.com/343pewus
    * TODO - add a proper citation here

    '''

    # Outputs
    SD, PSV, PSA, SV, SA, ED = (np.ones(len(periods)) for i in range(6))

    for i, T in enumerate(periods):

        # Properties of the SDOF
        wn = (2 * np.pi) / T # Circular natural frequency
        c  = 2 * zeta * wn   # Damping (assumes m = 1)
        K  = wn ** 2         # Stiffness (assumes m = 1)

        # Calculations
        y = np.zeros([2, len(acc)])
        A = np.array([[0, 1], [-K, -c]])
        Ae = sp.linalg.expm(A * dt)
        AeB = np.matmul(np.linalg.solve(A, (Ae - np.identity(2))),
                        np.array([0, 1]).reshape(-1, 1))

        # Iterate through acceleration time history
        for k in range(1, len(acc)):
            y[:, k] = (np.matmul(Ae, y[:, k-1].reshape(-1, 1)) + AeB * acc[k]).\
                       reshape(-1, )

        # Determine peak responses
        sd = np.max(np.abs(y[0, :]))
        SD[i]  = sd
        PSV[i] = sd * wn
        PSA[i] = sd * wn**2
        SV[i]  = np.max(np.abs(y[1, :]))
        SA[i]  = np.max(np.abs([K * y[0, :] + c * y[1, :]]))
        ED[i]  = c * dt * np.sum(y[1, :] ** 2)

    return SD, PSV, PSA, SA, SV, ED


def resp_spectra_newmark(acc, dt, periods, zeta = 0.05, method = 'average'):
    ''' TODO - code this as an excecise, even though it'll probably be way too
               slow to use in production
    ''' 
    pass


# ------------------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------------------

def newmark_linear_SDOF(acc, dt, T, zeta = 0.05, method = 'average'):
    ''' Newmark method to solve a linear SDOF subject to an acc time history

    DO NOT USE IT. IT HAS NOT BEEN CHECKED AND I CODED IT HALF ASLEEP.
        
    Purpose
    -------
    This function takes in an acceleration time history "acc" and time-step "dt"
    to return the response of a single degree of freedom system with natural
    period of vibration "T". This function assumes that the initial conditions 
    of the system (initial force, acceleration, velocity, and displacement) are 
    all equal to zero.
        
    Parameters
    ----------
    acc : numpy array
        Acceleration time history with time-step dt
        
    dt : float
        Time step

    T : float
        Natural period of vibration of the SDOF

    zeta : float (optional)
        Critical damping ratio to be used in calculations.
        Input as fractional number (0.05 would be 5% damping)

    method : str (optional)
        Indicates the type of newmark method to be used, and determines the 
        values of gamma and beta. Must be one of: 'average' or 'linear' and
        defaults to 'average'.
        
    Returns
    -------
    dis : numpy array
        Displcement time history of the SDOF
        
    vel : numpy array
        Velocity time history of the SDOF

    acc : numpy array
        Acceleration time history of the SDOF

    Refs
    ----
    * Chopra(1995) Dynamics of Structures: Theory and Applications to Earthquake
        Engineering. See Page 167 Table 5.4.2: NEWMARK'S METHOD: LINEAR SYSTEMS

    TODO - CHECK THIS! Pretty sure it will fail. 
    '''

    # Catch stability error
    if (dt / T <= 0.551) and (method == 'linear'):
        mssg  = 'Error in newmark_linear_SDOF: dt / T = {:4.3f}'.format(dt/T)
        mssg += '\nLinear acceleration metod is only stable if dt / T < 0.551'
        raise Exception(mssg)
    
    # Establish gamma and beta bsaed on Newmark method
    if method == 'average': # Special case 1
        gamma = 1/2
        beta  = 1/4
    elif method == 'linear': # Special case 2
        gamma = 1/2
        beta  = 1/6
    else: # Not implemented
        mssg = 'Error in newmark_linear_SDOF: method must be average or linear'
        raise Exception(mssg)

    # Determine properties of the SDOF
    wn = (2 * np.pi) / T        # Circular natural frequency
    k = 1000                    # Arbitrary stiffness
    m = k / (wn ** 2)           # Back-calculate mass
    c = 2 * zeta * (k * m)**0.5 # Damping

    # Initial Calculations
    k_hat = k + gamma / (beta * dt) * c + 1 / (beta * dt**2) * m  # (1.3)
    a = 1 / (beta * dt) * m + gamma / beta * c                    # (1.4)
    b = 1 / (2 * beta) * m + dt * (gamma / (2 * beta) - 1) * c    # (1.4)

    # Assume initial conditions are zero
    acc = np.apppend([0], acc)

    # Initalize outputs
    vel = np.zeros(len(acc))
    dis = np.zeros(len(acc))

    # Step through time
    for i in range(0, len(acc) - 1):

        # Incremental calculations for each time step
        d_p   = a * vel[i] + b * acc[i]    # (2.1)
        d_dis = d_p / k_hat                # (2.2)
        d_vel = gamma / (beta * dt) * d_dis - (gamma / beta) * vel[i] + \
                dt * (1 - gamma / (2 * beta)) * acc[i]    # (2.3)
        d_acc = (1 / (beta * dt**2)) * d_dis - (1 / (beta * dt)) * vel[i] - \
                1 / (2 * beta) * acc[i]    # (2.4)

        # Populate next time step (2.5)
        dis[i + 1] = dis[i] + d_dis
        vel[i + 1] = vel[i] + d_vel
        acc[i + 1] = acc[i] + d_acc

    return dis, vel, acc
