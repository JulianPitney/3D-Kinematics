import deeplabcut as dlc
import config
import os
from tkinter import filedialog


class DLC2Wrapper(object):

    def __init__(self):
        pass


    def load_proj(self):

        projDirectory = filedialog.askdirectory(initialdir=config.PROJECTS_FOLDER)
        configPath = projDirectory + "/config.yaml"
        if os.path.isfile(configPath):
            print(configPath)
            return configPath
        else:
            print("Project has no config.yaml file.")

    def detect_calibration_patterns(self):
        dlc.calibrate_cameras(config.DLC_3D_PAIR_1_2_CONFIG_PATH, config.CALIBRATION_CHECKERBOARD_ROWS, config.CALIBRATION_CHECKERBOARD_COLS, calibrate=False, alpha=0.9)
        dlc.calibrate_cameras(config.DLC_3D_PAIR_2_3_CONFIG_PATH, config.CALIBRATION_CHECKERBOARD_ROWS, config.CALIBRATION_CHECKERBOARD_COLS, calibrate=False, alpha=0.9)
        dlc.calibrate_cameras(config.DLC_3D_PAIR_3_4_CONFIG_PATH, config.CALIBRATION_CHECKERBOARD_ROWS, config.CALIBRATION_CHECKERBOARD_COLS, calibrate=False, alpha=0.9)
        dlc.calibrate_cameras(config.DLC_3D_PAIR_4_1_CONFIG_PATH, config.CALIBRATION_CHECKERBOARD_ROWS, config.CALIBRATION_CHECKERBOARD_COLS, calibrate=False, alpha=0.9)

    def calibrate_camera_pairs(self):
        dlc.calibrate_cameras(config.DLC_3D_PAIR_1_2_CONFIG_PATH, config.CALIBRATION_CHECKERBOARD_ROWS, config.CALIBRATION_CHECKERBOARD_COLS, calibrate=True, alpha=0.9)
        dlc.calibrate_cameras(config.DLC_3D_PAIR_2_3_CONFIG_PATH, config.CALIBRATION_CHECKERBOARD_ROWS, config.CALIBRATION_CHECKERBOARD_COLS, calibrate=True, alpha=0.9)
        dlc.calibrate_cameras(config.DLC_3D_PAIR_3_4_CONFIG_PATH, config.CALIBRATION_CHECKERBOARD_ROWS, config.CALIBRATION_CHECKERBOARD_COLS, calibrate=True, alpha=0.9)
        dlc.calibrate_cameras(config.DLC_3D_PAIR_4_1_CONFIG_PATH, config.CALIBRATION_CHECKERBOARD_ROWS, config.CALIBRATION_CHECKERBOARD_COLS, calibrate=True, alpha=0.9)

    def check_undistortion(self):

        dlc.check_undistortion(config.DLC_3D_PAIR_1_2_CONFIG_PATH, config.CALIBRATION_CHECKERBOARD_ROWS, config.CALIBRATION_CHECKERBOARD_COLS)
        dlc.check_undistortion(config.DLC_3D_PAIR_2_3_CONFIG_PATH, config.CALIBRATION_CHECKERBOARD_ROWS, config.CALIBRATION_CHECKERBOARD_COLS)
        dlc.check_undistortion(config.DLC_3D_PAIR_3_4_CONFIG_PATH, config.CALIBRATION_CHECKERBOARD_ROWS, config.CALIBRATION_CHECKERBOARD_COLS)
        dlc.check_undistortion(config.DLC_3D_PAIR_4_1_CONFIG_PATH, config.CALIBRATION_CHECKERBOARD_ROWS, config.CALIBRATION_CHECKERBOARD_COLS)