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

## Prerequisites

Below is the dependencies needed for running the GUI.py code:

* PySpin (the installation of PySpin dependency is complicated if the installing environment is not the same envrionment for the offical website downloaded wheel, so users are strongly recommended to make the envrionment: python lower than 3.8; Windows OS, same Architecture. The detailed installation tutorial has been recorded in /reference/spinnaker_python-2.7.0.128-cp38-cp38-win_amd64/README.txt)
* cv2
* numpy, PIL, matplotlib
* PyQt5
* serial

## File Explaination

### GUI.py

### run_data.py

### unfinished (folder)

## Contributing

* Prof. Yu Jiang
* Graduate Student Guangxun Zhai
* Graduate Student Lanyue Fang

## Date Updated

12/20/2022
