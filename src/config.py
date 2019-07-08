import os



# MAIN MENU
NUM_OPTIONS = 17
# STRINGS
MENU_MSG = """Select Function:
[1] Record Video
[2] Create Project
[3] Load Project
[4] Extract Frames
[5] Label Frames
[6] Check Labels
[7] Create Training Dataset
[8] Train Network
[9] Evaluate Network
[10] Analyze Videos
[11] Filter Predictions
[12] Create Labeled Videos
[13] Plot Trajectories
[14] Extract Outlier Frames
[15] Refine Labels
[16] Merge Datasets
[17] Exit
Input: """



# ARDUINO CONFIG
SERIAL_PORT_PATH = "COM3"
BAUDRATE = 115200


# CAMERA CONFIG
FPS = 100
EXPOSURE = 2000
WIDTH = 1440
HEIGHT = 1080
PULSE_RATE_MS = 1


# DLC CONFIG
VIDEOS_FOLDER = "C:/Projects/3D-Kinematics/videos"
PROJECTS_FOLDER = "C:/Projects/3D-Kinematics/DLC_PROJECTS"



# DIRECTORY STRUCTURE CHECKS
if not os.path.isdir(PROJECTS_FOLDER + "/../videos"):
    os.mkdir(PROJECTS_FOLDER + "/../videos")

if not os.path.isdir(PROJECTS_FOLDER + "/../DLC_PROJECTS"):
    os.mkdir(PROJECTS_FOLDER + "/../DLC_PROJECTS")
