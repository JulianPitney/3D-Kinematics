import config
import deeplabcut as dlc
import os
import shutil
from time import sleep
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

        dlc.calibrate_cameras(config.DLC_3D_PAIR_0_1_CONFIG_PATH, config.CALIBRATION_CHECKERBOARD_ROWS,
                              config.CALIBRATION_CHECKERBOARD_COLS, calibrate=False, alpha=0.9)
        dlc.calibrate_cameras(config.DLC_3D_PAIR_1_2_CONFIG_PATH, config.CALIBRATION_CHECKERBOARD_ROWS,
                              config.CALIBRATION_CHECKERBOARD_COLS, calibrate=False, alpha=0.9)
        dlc.calibrate_cameras(config.DLC_3D_PAIR_2_3_CONFIG_PATH, config.CALIBRATION_CHECKERBOARD_ROWS,
                              config.CALIBRATION_CHECKERBOARD_COLS, calibrate=False, alpha=0.9)
        dlc.calibrate_cameras(config.DLC_3D_PAIR_3_0_CONFIG_PATH, config.CALIBRATION_CHECKERBOARD_ROWS,
                              config.CALIBRATION_CHECKERBOARD_COLS, calibrate=False, alpha=0.9)


    def calibrate_camera_pairs(self):

        dlc.calibrate_cameras(config.DLC_3D_PAIR_0_1_CONFIG_PATH, config.CALIBRATION_CHECKERBOARD_ROWS,
                              config.CALIBRATION_CHECKERBOARD_COLS, calibrate=True, alpha=0.9)
        dlc.calibrate_cameras(config.DLC_3D_PAIR_1_2_CONFIG_PATH, config.CALIBRATION_CHECKERBOARD_ROWS,
                              config.CALIBRATION_CHECKERBOARD_COLS, calibrate=True, alpha=0.9)
        dlc.calibrate_cameras(config.DLC_3D_PAIR_2_3_CONFIG_PATH, config.CALIBRATION_CHECKERBOARD_ROWS,
                              config.CALIBRATION_CHECKERBOARD_COLS, calibrate=True, alpha=0.9)
        dlc.calibrate_cameras(config.DLC_3D_PAIR_3_0_CONFIG_PATH, config.CALIBRATION_CHECKERBOARD_ROWS,
                              config.CALIBRATION_CHECKERBOARD_COLS, calibrate=True, alpha=0.9)


    def check_undistortion(self):

        dlc.check_undistortion(config.DLC_3D_PAIR_0_1_CONFIG_PATH, config.CALIBRATION_CHECKERBOARD_ROWS,
                               config.CALIBRATION_CHECKERBOARD_COLS)
        dlc.check_undistortion(config.DLC_3D_PAIR_1_2_CONFIG_PATH, config.CALIBRATION_CHECKERBOARD_ROWS,
                               config.CALIBRATION_CHECKERBOARD_COLS)
        dlc.check_undistortion(config.DLC_3D_PAIR_2_3_CONFIG_PATH, config.CALIBRATION_CHECKERBOARD_ROWS,
                               config.CALIBRATION_CHECKERBOARD_COLS)
        dlc.check_undistortion(config.DLC_3D_PAIR_3_0_CONFIG_PATH, config.CALIBRATION_CHECKERBOARD_ROWS,
                               config.CALIBRATION_CHECKERBOARD_COLS)


    def analyze_videos(self):


        for i in range(0, config.NUM_CAMERAS):
            os.system('ffmpeg -f rawvideo -pix_fmt gray -video_size ' + str(config.WIDTH) + 'x' + str(
                config.HEIGHT) + ' -framerate ' +
                      str(config.MAX_TRIGGERED_FPS) + ' -i ' + config.VIDEOS_FOLDER + '/output' + str(
                i) + '.yuv -c:v libx265 -crf 10 -preset ultrafast '
                      + config.VIDEOS_FOLDER + '/output' + str(i) + '.mp4')


        os.mkdir(config.VIDEOS_FOLDER + "\\pair0-1")
        shutil.copyfile(config.VIDEOS_FOLDER + "\\output0.mp4", config.VIDEOS_FOLDER + "\\pair0-1\\camera-0-output.mp4")
        shutil.copyfile(config.VIDEOS_FOLDER + "\\output1.mp4", config.VIDEOS_FOLDER + "\\pair0-1\\camera-1-output.mp4")

        os.mkdir(config.VIDEOS_FOLDER + "\\pair1-2")
        shutil.copyfile(config.VIDEOS_FOLDER + "\\output1.mp4", config.VIDEOS_FOLDER + "\\pair1-2\\camera-1-output.mp4")
        shutil.copyfile(config.VIDEOS_FOLDER + "\\output2.mp4", config.VIDEOS_FOLDER + "\\pair1-2\\camera-2-output.mp4")

        os.mkdir(config.VIDEOS_FOLDER + "\\pair2-3")
        shutil.copyfile(config.VIDEOS_FOLDER + "\\output2.mp4", config.VIDEOS_FOLDER + "\\pair2-3\\camera-2-output.mp4")
        shutil.copyfile(config.VIDEOS_FOLDER + "\\output3.mp4", config.VIDEOS_FOLDER + "\\pair2-3\\camera-3-output.mp4")

        os.mkdir(config.VIDEOS_FOLDER + "\\pair3-0")
        shutil.copyfile(config.VIDEOS_FOLDER + "\\output3.mp4", config.VIDEOS_FOLDER + "\\pair3-0\\camera-3-output.mp4")
        shutil.copyfile(config.VIDEOS_FOLDER + "\\output0.mp4", config.VIDEOS_FOLDER + "\\pair3-0\\camera-0-output.mp4")


        dlc.triangulate(config.DLC_3D_PAIR_0_1_CONFIG_PATH, config.VIDEOS_FOLDER + "\\pair0-1", videotype='.mp4', filterpredictions=True, filtertype='arima', save_as_csv=True)
        dlc.triangulate(config.DLC_3D_PAIR_1_2_CONFIG_PATH, config.VIDEOS_FOLDER + "\\pair1-2", videotype='.mp4', filterpredictions=True, filtertype='arima', save_as_csv=True)
        dlc.triangulate(config.DLC_3D_PAIR_2_3_CONFIG_PATH, config.VIDEOS_FOLDER + "\\pair2-3", videotype='.mp4', filterpredictions=True, filtertype='arima', save_as_csv=True)
        dlc.triangulate(config.DLC_3D_PAIR_3_0_CONFIG_PATH, config.VIDEOS_FOLDER + "\\pair3-0", videotype='.mp4', filterpredictions=True, filtertype='arima', save_as_csv=True)




def main():

    dlc = DLC2Wrapper()
    menuFunctions = [ dlc.detect_calibration_patterns, dlc.calibrate_camera_pairs,
                     dlc.check_undistortion, dlc.analyze_videos, exit]

    while True:

        menuSelection = input(config.DLC_MENU_MSG)
        try:
           menuSelection = int(menuSelection)
        except ValueError:
            print("Invalid selection, try again.")
            continue

        if len(menuFunctions) >= menuSelection >= 1:
            menuFunctions[menuSelection - 1]()
        else:
            print("Invalid selection, try again.")
            continue

if __name__ == '__main__':
	main()

