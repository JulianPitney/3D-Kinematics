import deeplabcut
import config
from tkinter import filedialog


menuMsg = """Select Function:
[1] Create Project
[2] Load Project
[3] Extract Frames
[4] Label Frames
[5] Check Labels
[6] Create Training Dataset
[7] Train Network
[8] Evaluate Network
[9] Analyze Videos
[10] Filter Predictions
[11] Create Labeled Videos
[12] Plot Trajectories
[13] Extract Outlier Frames
[14] Refine Labels
[15] Merge Datasets
[16] Exit
Input: """




def create_proj():

    projectName = input("Project Name: ")
    experimenterName = input("Experimenter Name: ")
    videoFolderPath = input("Video Folder Path: ")
    videoPaths = ['../videos/output1.avi', '../videos/output2.avi']
    configPath = deeplabcut.create_new_project(projectName, experimenterName, videoPaths, config.PROJECTS_FOLDER, copy_videos=False)
    return configPath


def load_proj():

    projDirectory = filedialog.askdirectory()
    configPath = projDirectory + "/config.yaml"
    if os.path.isfile(configPath):
        return configPath
    else:
        print("Project has no config.yaml file.")


main():

    configPath = ""

    while(1):

        menuSelection = input(menuMsg)
        try:
           menuSelection = int(menuSelection)
        except ValueError:
            print("Invalid selection, try again.")
            continue

        if menuSelection == 1:
            configPath = create_proj()

        elif menuSelection == 2:
            configPath = load_proj()

        elif menuSelection == 3:
            deeplabcut.extract_frames(configPath, "automatic", "uniform", crop=True)

        elif menuSelection == 4:
            deeplabcut.label_frames(configPath)

        elif menuSelection == 5:
            deeplabcut.check_labels(configPath)

        elif menuSelection == 6:
            deeplabcut.create_training_dataset(configPath, num_shuffles=1)

        elif menuSelection == 7:
            deeplabcut.train_network(configPath, shuffle=1)

        elif menuSelection == 8:
            deeplabcut.evaluate_network(configPath, shuffle=[1], plotting=True)

        elif menuSelection == 9:
        deeplabcut.analyze_videos(configPath, videoFolderPath, videoType=".avi", save_as_csv=True)

        elif menuSelection == 10:
            deeplabcut.filterpredictions(configPath, videoPath, shuffle=1)

        elif menuSelection == 11:
            deeplabcut.create_labeled_video(configPath, videoFolderPath, filtered=True)

        elif menuSelection == 12:
            deeplabcut.plot_trajectories(configPath, videoFolderPath, filtered=True)

        elif menuSelection == 13:
            deeplabcut.extract_outlier_frames(configPath, videoFolderPath)

        elif menuSelection == 14:
            deeplabcut.refine_labels(configPath)

        elif menuSelection == 15:
            deeplabcut.merge_datasets(configPath)

        elif menuSelection == 16:
            exit()

        else:
            "Invalid selection, try again."



if __name__ == '__main__':
	main()
