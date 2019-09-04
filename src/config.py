import os



# MAIN MENU
# STRINGS
MENU_MSG = """Select Function:
[1] Record Video
[2] Take Calibration Pictures
[3] Detect Calibration Patterns
[4] Calibrate Camera Pairs
[5] Check Undistortion
[6] Exit
Input: """



# ARDUINO CONFIG
SERIAL_PORT_PATH = "COM3"
BAUDRATE = 115200


# CAMERA CONFIG
CAMERA_1_ID = '19276766'
CAMERA_2_ID = '19194610'
CAMERA_3_ID = '19276765'
CAMERA_4_ID = '18474728'
CALIBRATION_CHECKERBOARD_ROWS = 10
CALIBRATION_CHECKERBOARD_COLS = 12


FPS = 50
EXPOSURE = 1000
GAIN = 17
BINNING_MODE = 2
WIDTH = 720
HEIGHT = 540
RECORDING_DURATION_S = 20
MAX_TRIGGERED_FPS = int(1 / ((EXPOSURE / 1000000) + (1 / FPS)))
TRIGGER_FREQUENCY_US = ((1 / MAX_TRIGGERED_FPS) * 1000000)
NUM_CAMERAS = 4
MAX_FRAME_BUFFER_SIZE_MB = 8000
MAX_FRAMES_IN_BUFFER = int(MAX_FRAME_BUFFER_SIZE_MB / ((WIDTH * HEIGHT) / 1000000)) + NUM_CAMERAS - 1
DISPLAY_VIDEO_FEEDS = True





# DLC CONFIG
DLC_3D_PAIR_1_2_CONFIG_PATH = "C:/Projects/3D-Kinematics/DLC_PROJECTS/openfield-julian-2019-08-21-3d_pair1-2/config.yaml"
DLC_3D_PAIR_2_3_CONFIG_PATH = "C:/Projects/3D-Kinematics/DLC_PROJECTS/openfield-julian-2019-08-21-3d_pair2-3/config.yaml"
DLC_3D_PAIR_3_4_CONFIG_PATH = "C:/Projects/3D-Kinematics/DLC_PROJECTS/openfield-julian-2019-08-21-3d_pair3-4/config.yaml"
DLC_3D_PAIR_4_1_CONFIG_PATH = "C:/Projects/3D-Kinematics/DLC_PROJECTS/openfield-julian-2019-08-21-3d_pair4-1/config.yaml"
CALIBRATION_IMAGES_FOLDER_PAIR_1_2 = "C:/Projects/3D-Kinematics/DLC_PROJECTS/openfield-julian-2019-08-21-3d_pair1-2/calibration_images"
CALIBRATION_IMAGES_FOLDER_PAIR_2_3 = "C:/Projects/3D-Kinematics/DLC_PROJECTS/openfield-julian-2019-08-21-3d_pair2-3/calibration_images"
CALIBRATION_IMAGES_FOLDER_PAIR_3_4 = "C:/Projects/3D-Kinematics/DLC_PROJECTS/openfield-julian-2019-08-21-3d_pair3-4/calibration_images"
CALIBRATION_IMAGES_FOLDER_PAIR_4_1 = "C:/Projects/3D-Kinematics/DLC_PROJECTS/openfield-julian-2019-08-21-3d_pair4-1/calibration_images"
VIDEOS_FOLDER = "C:/Projects/3D-Kinematics/videos"
PROJECTS_FOLDER = "C:/Projects/3D-Kinematics/DLC_PROJECTS"

# DIRECTORY STRUCTURE CHECKS
if not os.path.isdir(PROJECTS_FOLDER + "/../videos"):
    os.mkdir(PROJECTS_FOLDER + "/../videos")

if not os.path.isdir(PROJECTS_FOLDER + "/../DLC_PROJECTS"):
    os.mkdir(PROJECTS_FOLDER + "/../DLC_PROJECTS")
