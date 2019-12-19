# Kinarena

Kinarena is a system for performing 3D kinematic analysis on rodents. The 3D reconstruction is marker-less, fully automatic, covers 360° around the animal at all times and is highly accurate. 

The system is an "end-to-end solution". This means that we provide:

* Arena optimized for rodent kinematics.
* Hardware synchronized camera system optimized for rodent kinematics.
* I.R lighting for even and diffuse lighting in "night" or "day" conditions.
* Hardware for securely mounting the cameras and lights to the arena.
* Software for automatic 3D reconstruction with 360° coverage at all times.
* Analysis software for generating meaningful conclusions from the data.
* Trained network and camera  calibration files. (If you're using our hardware there is no need to train your own network or perform your own camera calibration)

The goal of this project is to provide a system that generates meaningful "graph-ready" behavioral data at the push of a button. 

# Table of Contents
* [Installation](#installation)
* [Usage](#usage)
* [Contributing](#contributing)
* [Credits](#credits)
* [License](#license)


# Installation

**Hardware:**<br/>
[Parts List](https://docs.google.com/spreadsheets/d/18pRoh0PZBaclofkvuCLl1aGt24ObCIeX1hrV7fQlwLQ/edit?usp=sharing)


**Dependencies**

Name | Version
------------ | -------------
[Windows 10](https://www.microsoft.com/en-ca/windows/get-windows-10) | Latest Version
[Anaconda](https://www.anaconda.com/) | Latest Version
Python | 3.6.9
[Spinnaker SDK](https://drive.google.com/file/d/1ekqroxbpQbD4XAP_PvaEMywXw5San4l4/view?usp=sharing) | 1.20.0.15
[Spinnaker Python](https://drive.google.com/drive/folders/1aErW7o_pc7jhp2hj4MuVE-I-7R72fGmS?usp=sharing) | 1.20.0.15
[Arduino IDE](https://www.arduino.cc/en/main/OldSoftwareReleases) | 1.6.9
OpenCV | 4.1.1.26
[FFmpeg](https://www.ffmpeg.org/download.html#releases) | 4.2.1
PySerial | 3.4
[DeepLabCut](https://github.com/AlexEMG/DeepLabCut) | 2.0.9
[anipose](https://github.com/lambdaloop/anipose) | 0.6.3

**Installation Step-By-Step**

1. Download and install the most recent version of Anaconda from [here](https://www.anaconda.com/).
2. Download and install the Arduino IDE from [here](https://www.arduino.cc/en/main/OldSoftwareReleases).
3. Follow the installation instructions [here](https://github.com/AlexEMG/DeepLabCut/blob/master/docs/installation.md) to get DeepLabCut installed inside a virtual environment. You should call this virtual environment ``dlc-windowsgpu``.
4. Follow the installation instructions [here](https://github.com/lambdaloop/anipose) to get anipose installed in the same virtual environment as DeepLabCut.
5. Install the Spinnaker SDK using the executable installer provided [here](https://drive.google.com/file/d/1ekqroxbpQbD4XAP_PvaEMywXw5San4l4/view?usp=sharing). **Note:** If you don't want to trust this binary, you can email Flir and request the installer from them. Ask for the version specified in the dependencies table above.
6. Use Anaconda to create a second virtual environment called ``flir-env`` with python version ``3.6.5``.
7. Install the Spinnaker Python API inside ``flir-env`` by downloading [this]() folder and following the instructions in the README.txt contained within. 
8. Down and install FFmpeg from [here](https://www.ffmpeg.org/download.html#releases) and add the bin folder to your Windows system path.
9. Clone this repository.

# Usage

1. Open a terminal and type ``conda activate flir-env``
2. Type ``python kinarena.py``
3. Select ``[2] New Trial`` to record a trial. For every trial a folder will be generated under ``~/anipose/experiments/<trial_name>``. 
4. At any time, you can select ``[3] Analyze Trials`` to automatically analyze all trials that have not yet been analyzed. Analysis takes a long time so don't do this until you're done recording and ready to walk away for the day.

# Contributing
Not ready for outside contribution.
# Credits
* [DeepLabCut authors](http://www.mousemotorlab.org/deeplabcut)
* [anipose authors](https://github.com/lambdaloop)
* [Boyang Wang](jwang149@gmail.com)
* [Bergeron Lab](jwang149@gmail.com)
* [Julian Pitney](www.julianpitney.com)

# License
Legal stuff

