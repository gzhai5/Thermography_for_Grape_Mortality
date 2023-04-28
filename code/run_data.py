import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import keyboard
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

    for i in range(data.shape[0]):
        
        if i > 0:
            cur_frame = np.squeeze(data[i,:,:])
            previous_frame = np.squeeze(data[i-1,:,:])
            frame_diff = cur_frame - previous_frame
            # print('per frame: {0}, cross frame: {1}'.format(max(cur_frame)-min(cur_frame), max(frame_diff)))
        # cur_frame = np.squeeze(data[i,:,:])
        # cur_frame = (30 - cur_frame) / 10
            # plt.imshow(cur_frame)
            plt.hist(frame_diff.reshape(640*480,1),range=(-500,500),bins=[-500,-300,-50,50,300,500])
            plt.pause(0.05)
            plt.clf()

        if keyboard.is_pressed('ENTER'):
            plt.close('all')
            break
    plt.show()

    # fig,ax = plt.subplots()
    # fig.frameon = False
    # fig.facecolor = 'none'
    # fig.suptitle("Data Video Replay")

    # ani = animation.FuncAnimation(fig, update_frame, frames=range(data.shape[0]), interval=33, fargs=(data,ax))
    # plt.show()