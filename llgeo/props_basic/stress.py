import numpy as np

def vert_to_mean_stress(v_stress, k = 0.5):
    mean_stress = np.average(v_stress, k*v_stress, k*v_stress)
    return(mean_stress)





