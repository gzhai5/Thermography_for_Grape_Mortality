import numpy as np
import matplotlib.pyplot as plt
import os

filenames = ['./offsets/A1_Value.npy',
            './offsets/A2_Value.npy',
            './offsets/B_Value.npy',
            './offsets/B1_Value.npy',
            './offsets/B2_Value.npy',
            './offsets/F_Value.npy',
            './offsets/J1_Value.npy',
            './offsets/J0_Value.npy',
            './offsets/R_Value.npy',
            './offsets/X_Value.npy']
total_time = 1000

fig,axs = plt.subplots(2,5,figsize=(15,6))
for i,filename in enumerate(filenames):
    row = i //5
    col = i % 5
    data = np.load(filename)
    time_step = total_time/len(data)
    time = np.arange(0,total_time,time_step)    
    axs[row,col].plot(time,data)
    axs[row,col].set_title(os.path.basename(filename))
    ypadding = 0.1*(np.max(data)-np.min(data))
    axs[row,col].set_ylim(np.min(data)-ypadding,np.max(data)+ypadding)
fig.suptitle('offsets plots')
fig.text(0.5,0.04,'Time(s)',ha='center')
fig.text(0.04,0.5,'Vlue',va='center',rotation='vertical')
plt.subplots_adjust(hspace=0.4,wspace=0.4)
plt.show()


# data = np.load(filenames[0])
# print(data)
