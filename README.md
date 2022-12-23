# Project Title: Thermography_for_Grape_Mortality

Our technology aims to prevent significant financial losses caused by accidentally cutting off healthy grape buds in the Northeast US during winter and early spring. We used a thermal camera (FLIR a700) to capture thousands of thermal images of the grape buds and used controllable heating to differentiate between live and dead buds based on temperature changes. By analyzing the image data with computer vision and machine learning, we developed a successful identification model with an accuracy of around 90%. In the project, I acquired data from the thermal camera, used computer vision to isolate the grape buds, and trained the model to detect dead buds. A successful outcome of the project would be a trained model that can accurately identify dead buds among a group of grape buds, reducing economic losses in the field.

## Getting Started

### Hardwares Needed

* Thermal Camera (FLIR a700)

* Switching Power Supply

* Two Cables (one is a ethernet cable; another is a white cable that is in the camera packaging box, one port is ethernet port, another is a data/power port to the camera)

* A Computer (Windows OS prefererred) with ethernet port

<figure style="text-align:center">
  <img src="/readme_files/two_cables_needed_and_switching_power_supply.JPG" alt="ERROR">
  <figcaption style="display:inline-block; font-size:24px; color:red">Figure 1: Left to Right: Ethernet Cable, Switching Power Supply, Cable between Switching Power Supply and Camera</figcaption>
</figure>

### Softwares Needed

The major softwares needed for this project is :

* SpinView (A pre-developed Spinnaker Full SDK that can easily get access to the camera and used)
* Python (edition 3.8, if using Windows OS, using Anaconda to have a good edition of python is strongly recomended)
* Python Dependecies (will be further discussed in the "Prerequisites" section).

## Hardware Connections

<figure style="text-align:center">
  <img src="/readme_files/switching_power_supply_connections.JPG" alt="ERROR">
  <figcaption style="display:inline-block; font-size:24px; color:red">Figure 2: Cable Connections on the Switching Power Supply<br>(be aware of the differnt IN/OUT ports)</figcaption>
</figure>
<br>
<figure style="text-align:center">
  <img src="/readme_files/camera_cable_connection.JPG" alt="ERROR">
  <figcaption style="display:inline-block; font-size:24px; color:red">Figure 3: Camera Port<br>(the cable should be connected to the ETH/PoE port, and when connecting camera successfully, two signal lights hould be on)</figcaption>
</figure>

## Prerequisites

Below is the dependencies needed for running the GUI.py code:

* Installing the PySpin dependency can be complicated if the environment is not the same as the one used on the official website to download the wheel. We strongly recommend using an environment with Python lower than 3.8 and Windows OS with the same architecture. Mac OS and Linux OS have been tried before, but both of them have issues that may require additional troubleshooting. In our experience, it is much more convenient to use Windows OS. Detailed installation instructions can be found in the README file located at /reference/spinnaker_python-2.7.0.128-cp38-cp38-win_amd64/."
* cv2
* numpy, PIL, matplotlib
* PyQt5
* serial

## File Explaination

### GUI.py

This code is the main code for using the camera. It creates a simple GUI with different threads for the usage of camera: camera streaming, a NULL thread, and data acquisition. The code requires successful connections to the thermal camera and the switch, otherwise it will display error messages and no image. The purpose of this code is to more easily control the thermal camera using software coding (here we use Python), preparing for collecting data for further computer vision and machine learning studies.

* Camera Streaming Thread:<br>
This part of the code, called "VideoThread," is a class in our Python code. Most of the code is based on the Example code from Spinnaker (/reference/spinnaker_python-2.7.0.128-cp38-cp38-win_amd64/Examples/Python3/Acquisition.py) and an open source project (https://gist.github.com/docPhil99/ca4da12c9d6f29b9cea137b617c7b8b1). It initializes the camera and retrieves the image data (as a nd numpy array), which is then emitted to the PyQt screen. The thread is entered when the user clicks the "Connect" button in the PyQt interface. The "Connect" and "Cut" buttons control whether the streaming thread is active or not.

* NULL Thread:<br>
This part of the code, called "disconnect_thread," is a class in our Python code. It was created based on instructions from ChatGPT and follows the same format as other threads. However, the internal code is simple: it draws a white background and prints some text on it. This image is continuously emitted to the PyQt screen while the thread is running. This thread is the default when starting the code and can be accessed by clicking the "Cut" button.

* Data Aquisition Thread:<br>
This part of the code, called "VideoThread_timed," is a class in our Python code. The code writing is based on the streaming thread but with the added feature of being a timed function. The running time is controlled by the value of t2 (which can be changed from the PyQt interface). During the running time, the switch is controlled on and off according to the values of t0 and t1 (which have similar settings as t2). When the timed data acquisition process is finished, the image data is saved into a 3D numpy array and locally as a .npy file. This file is important for further analysis and is large in size due to the uncompressed image data. The thread also includes focus adjustment buttons, which are linked to the camera focusing: a button to choose the focus method, an auto focus button, a focus plus button, a focus minus button, and a focus step text edit place. The logic for the focus adjustment was inspired by this online article (https://www.flir.com/support-center/iis/machine-vision/application-note/spinnaker-nodes/), which explains how to locate a function in SpinView.

### run_data.py
This code uses the matplotlib package to display the images stored in a .npy file as a video animation. Its purpose is to facilitate the inspection and verification of the saved camera image data by allowing the user to replay them.

### unfinished (folder)
This folder contains many code files that were created during the development process. Most of them are test code for testing individual features and some may contain bugs. They were saved to document the development process, as we did not use github to track changes before. They may also be useful if we decide to revisit a discarded feature in the future.

## Contributing

* Prof. Yu Jiang
* Graduate Student Guangxun Zhai
* Graduate Student Lanyue Fang

## Date Updated

12/22/2022
