# Project Title: Thermography_for_Grape_Mortality

Our technology aims to mitigate the significant financial losses caused by mistakenly cutting off healthy grape buds in the Northeast US during winter and early spring. We used a thermal camera (FLIR a700) to capture thousands of thermal images of the grape buds and used controllable heating to differentiate between live and dead buds based on temperature changes. By analyzing the image data with computer vision and machine learning, we were able to develop a successful identification model with an accuracy of around 90%. My role in the project involved acquiring data from the thermal camera, using computer vision to isolate the grape buds, and training the model to detect dead buds. A successful outcome of the project would be a trained model that can accurately identify dead buds among a group of grape buds, thereby reducing economic losses in the field.

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

* PySpin (the installation of PySpin dependency is complicated if the installing environment is not the same envrionment for the offical website downloaded wheel, so users are strongly recommended to make the envrionment: python lower than 3.8; Windows OS, same Architecture. Mac OS and Linux OS have been tried before, but both of them have issues that needed to be figured out through google, and from my experience, it is much more conveninet to use Windows OS. The detailed installation tutorial has been recorded in /reference/spinnaker_python-2.7.0.128-cp38-cp38-win_amd64/README.txt)
* cv2
* numpy, PIL, matplotlib
* PyQt5
* serial

## File Explaination

### GUI.py

This code is the major code for using the camera so far. It creates a simple GUI that have different threads for camera streaming, NULL thread, and Data
Aquistion. The running of the code requires the successful connections to the thermal camera and the switch, otherwise it will have no image and error messages. The purpose of this code is to more easily control the usage of the thermal camera on a software coding base (here is Python) so as to make preparation of collecting the data for further CV/ML studies.

* Camera Streaming Thread:<br>
This part is called "VideoThread" in the python code class. Most of the code is referenced by the Example code from Spinnaker (/reference/spinnaker_python-2.7.0.128-cp38-cp38-win_amd64/Examples/Python3/Acquisition.py) and an open source (https://gist.github.com/docPhil99/ca4da12c9d6f29b9cea137b617c7b8b1). More specificly, it initilze the camera and get the image data (which is a nd numpy array), and emit each of it to the PyQt screen. The entering of this thread is realated to a PyQt button named "Connect". The "Connect" and "Cut" button will simply help the program determine whether to use this streaming thread or stop it.

* NULL Thread:<br>
This part is called "disconnect_thread" in the python code class. The code is instructed by ChatGPT. It is the same format of other threads. But the internal code is simple: Drawing a white background and print some texts on it. This image will be emitted to the PyQt screen always during this thread running. This thread is the default thread when starting the code, and could be access when hitting the "Cut" button.

* Data Aquisition Thread:<br>
This part is called "VideoThread_timed" in the python code class. The code writing is based on the streaming thread but making the streaming become a timed function with some other small features. The running time is controlled by the value of t2 (which has a default value, but can be changed from the PyQt screen). And during the running time, the switch will be controlled on and off according to the value of t0 and t1 (which has similiar settings as t2). Also, when finished this timed data aquisition process, the image data will be saved into a 3d numpy array and will be saved locally to .npy file. This file is important for the further analysis process, and has a big size since the image data has not been compressed. Some other features about the thread is the focus adjustment buttons. There are five main buttons linked with the camera focusing: Choose the focus method, auto focus, foucs plus, focus minus, and focus step. The logic for writing this focusing is get hinted by this online article (https://www.flir.com/support-center/iis/machine-vision/application-note/spinnaker-nodes/). This article states the way of writing code to locate a function which can be found in SpinView.

### run_data.py

### unfinished (folder)

## Contributing

* Prof. Yu Jiang
* Graduate Student Guangxun Zhai
* Graduate Student Lanyue Fang

## Date Updated

12/20/2022
