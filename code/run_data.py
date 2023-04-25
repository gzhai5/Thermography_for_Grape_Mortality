import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import sys
from IPython.display import HTML

def update_frame(frame_num, data, ax):
    ax.clear()
    ax.imshow(data[frame_num], cmap='inferno', aspect='auto')
    return ax

filename = "none"
if (len(sys.argv) == 1):
    print("no data fie is given, plz add a argument for datafile (inside the SavedData folder) in the python run argument!")
    print("")
    print("For example:   img_data.npy")
elif (len(sys.argv) == 2):
    filename = "./SavedData/" + sys.argv[1]
    print("-----Going to Play the file: " + filename)
    data = np.load(filename)

    fig,ax = plt.subplots()
    fig.frameon = False
    fig.facecolor = 'none'
    fig.suptitle("Data Video Replay")

    ani = animation.FuncAnimation(fig, update_frame, frames=range(data.shape[0]), interval=50, fargs=(data,ax))
    plt.show()