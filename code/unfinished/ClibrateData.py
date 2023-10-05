import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import sys

data_high = np.load("./SavedData/high_em.npy")
data_low = np.load("./SavedData/alplate.npy")
data_raw = np.load("./SavedData/img_data.npy")

data_cal = np.zeros_like(data_raw)
mask = (data_high-data_low) > 0
data_cal[mask] = (data_raw[mask]-data_low[mask])/(data_high[mask]-data_low[mask])
data_cal[mask] = data_raw[mask]

output_file = "./SavedData/calibrated_data_withalplate.npy"
np.save(output_file,data_cal)
