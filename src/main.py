import config
import DLC2Wrapper as dlc
import FlirController as fc


def main():

    dlcWrapper = dlc.DLC2Wrapper()
    flirController = fc.CameraController()
    menuFunctions = [flirController.synchronous_record, flirController.take_synchronous_calibration_pictures, dlcWrapper.detect_calibration_patterns, dlcWrapper.calibrate_camera_pairs,
                     dlcWrapper.check_undistortion, exit]

    while True:

        menuSelection = input(config.MENU_MSG)
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


