import numpy as np
import matplotlib.pyplot as plt
import sys

filename = "none"
if (len(sys.argv) == 1):
    print("no data fie is given, plz add a argument for datafile (inside the SavedData folder) in the python run argument!")
    print("")
    print("For example:   img_data.npy")
elif (len(sys.argv) == 2):
    filename = "./SavedData/" + sys.argv[1]

data = np.load(filename)
mean = np.mean(data, axis=(0,1))
std = np.std(data, axis=(0,1))

fig,ax = plt.subplots()
ax.plot(mean, label="Mean")
ax.plot(std, label="Standard Deviation")
ax.set_xlabel('Frame number')
ax.set_ylabel('Value')
ax.set_title('Mean and STD of the data')
ax.legend()
plt.show()