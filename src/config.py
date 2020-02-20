import os


# ARDUINO CONFIG
SERIAL_PORT_PATH = "COM3"
BAUDRATE = 115200


# CAMERA CONFIG
CAMERA_0_ID = '19276766'
CAMERA_1_ID = '19194610'
CAMERA_2_ID = '19276765'
CAMERA_3_ID = '18474728'

# RECORDING CONFIG
FPS = 60
EXPOSURE = 1000
GAIN = 17
BINNING_MODE = 2
WIDTH = 720
HEIGHT = 540
RECORDING_DURATION_S = 20
MAX_TRIGGERED_FPS = int(1 / ((EXPOSURE / 1000000) + (1 / FPS)))
TRIGGER_FREQUENCY_US = ((1 / MAX_TRIGGERED_FPS) * 1000000)
NUM_CAMERAS = 4
MAX_FRAME_BUFFER_SIZE_MB = 30000
MAX_FRAMES_IN_BUFFER = int(MAX_FRAME_BUFFER_SIZE_MB / ((WIDTH * HEIGHT) / 1000000)) + NUM_CAMERAS - 1
DISPLAY_VIDEO_FEEDS = True
RECORD_VIDEO = False
PREVIEW_WINDOW_FRAME_WIDTH = 720.0


VIDEOS_FOLDER = "C:\\Projects\\3D-Kinematics\\anipose\\experiment0"
PROJECTS_FOLDER = "C:\\Projects\\3D-Kinematics\\DLC_PROJECTS"
