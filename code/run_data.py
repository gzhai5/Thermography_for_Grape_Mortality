import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import sys

def update_figure(i, data, ax):
    ax.clear()
    ax.imshow(data[i], cmap='gray')  # the cmap makes the video become greyscale instead of some yellow green color
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

    fig, ax = plt.subplots()
    fig.frameon = False
    fig.facecolor = 'none'
    fig.suptitle("Data File Replay")

    ani = animation.FuncAnimation(fig, update_figure, frames=range(data.shape[0]), fargs=(data, ax))
    plt.show()