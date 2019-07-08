import config
import FlirController as fc
import DLC2Wrapper as dlc



def main():

    dlcw = dlc.DLC2Wrapper()
    flirController = fc.CameraController()

    menuFunctions = [flirController.synchronous_record, dlcw.create_proj, dlcw.load_proj, dlcw.extract_frames,
                     dlcw.label_frames, dlcw.check_labels, dlcw.create_training_dataset,
                     dlcw.train_network, dlcw.evaluate_network, dlcw.analyze_videos,
                     dlcw.filter_predictions, dlcw.create_labeled_video,
                     dlcw.plot_trajectories, dlcw.extract_outlier_frames,
                     dlcw.refine_labels, dlcw.merge_datasets, exit]



    while True:

        menuSelection = input(config.MENU_MSG)
        try:
           menuSelection = int(menuSelection)
        except ValueError:
            print("Invalid selection, try again.")
            continue

        if config.NUM_OPTIONS >= menuSelection >= 1:
            menuFunctions[menuSelection - 1]()
        else:
            print("Invalid selection, try again.")
            continue


if __name__ == '__main__':
	main()


