import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

def update_figure(i, data, ax):
    ax.clear()
    ax.imshow(data[i], cmap='gray')  # the cmap makes the video become greyscale instead of some yellow green color
    return ax

data = np.load('./SavedData/img_data.npy')

fig, ax = plt.subplots()
fig.frameon = False
fig.facecolor = 'none'
fig.suptitle("Data File Replay")

ani = animation.FuncAnimation(fig, update_figure, frames=range(data.shape[0]), fargs=(data, ax))
plt.show()