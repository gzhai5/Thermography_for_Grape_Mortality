import cv2
import numpy as np
import glob

img_array = []
for filname in glob.glob('C:/Users/Alfoul/Desktop/img_to_video/*.png'):
    img = cv2.imread(filname)
    height, width, layers = img.shape
    size = (width,height)
    img_array.append(img)

out = cv2.VideoWriter('project.avi', cv2.VideoWriter_fourcc(*'DIVX'), 15, size)

for i in range (len(img_array)):
    out.write(img_array[i])
out.release()
