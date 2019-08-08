import os



# MAIN MENU
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
FPS = 60
EXPOSURE = 5000
BINNING_MODE = 1
WIDTH = 1440
HEIGHT = 1080
RECORDING_DURATION_S = 120
MAX_TRIGGERED_FPS = int(1 / ((EXPOSURE / 1000000) + (1 / FPS)))
print(MAX_TRIGGERED_FPS)
TRIGGER_FREQUENCY_US = ((1 / MAX_TRIGGERED_FPS) * 1000000)
NUM_CAMERAS = 2
MAX_FRAME_BUFFER_SIZE_MB = 8000
MAX_FRAMES_IN_BUFFER = int(MAX_FRAME_BUFFER_SIZE_MB / ((WIDTH * HEIGHT) / 1000000)) + NUM_CAMERAS - 1
DISPLAY_VIDEO_FEEDS = True

# DLC CONFIG
VIDEOS_FOLDER = "C:/Projects/3D-Kinematics/videos"
PROJECTS_FOLDER = "C:/Projects/3D-Kinematics/DLC_PROJECTS"

# DIRECTORY STRUCTURE CHECKS
if not os.path.isdir(PROJECTS_FOLDER + "/../videos"):
    os.mkdir(PROJECTS_FOLDER + "/../videos")

if not os.path.isdir(PROJECTS_FOLDER + "/../DLC_PROJECTS"):
    os.mkdir(PROJECTS_FOLDER + "/../DLC_PROJECTS")
