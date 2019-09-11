import config
import FlirController as fc


def main():

    flirController = fc.CameraController()
    menuFunctions = [flirController.synchronous_record, flirController.take_synchronous_calibration_pictures, exit]

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


