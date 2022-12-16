import numpy as np
import cv2

data = np.load("img_data.npy")
cap = cv2.VideoCapture(data)

if not cap.isOpened():
    print("Error opening video fiel!")

while cap.isOpened():
    ret, frame = cap.read()
    if ret:
        cv2.imshow("Video", frame)
        if cv2.waitKey(25) & 0xFF == ord("q"):
            break
    else:
        break
cap.realease()