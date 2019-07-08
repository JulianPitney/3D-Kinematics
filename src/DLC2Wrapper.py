import deeplabcut
import config
import os
from tkinter import filedialog


class DLC2Wrapper(object):

    currentConfigPath = ""

    def __init__(self):
        pass

    def create_proj(self):

        projectName = input("Project Name: ")
        experimenterName = input("Experimenter Name: ")
        videoPaths = []
        self.currentConfigPath = deeplabcut.create_new_project(projectName, experimenterName, videoPaths, config.PROJECTS_FOLDER, copy_videos=False)


    def load_proj(self):

        projDirectory = filedialog.askdirectory(initialdir=config.PROJECTS_FOLDER)
        configPath = projDirectory + "/config.yaml"
        if os.path.isfile(configPath):
            self.currentConfigPath = configPath
        else:
            print("Project has no config.yaml file.")


    def extract_frames(self):
        deeplabcut.extract_frames(self.currentConfigPath, "automatic", "uniform", crop=True)

    def label_frames(self):
        deeplabcut.label_frames(self.currentConfigPath)

    def check_labels(self):
        deeplabcut.check_labels(self.currentConfigPath)

    def create_training_dataset(self):
        deeplabcut.create_training_dataset(self.currentConfigPath, num_shuffles=1)

    def train_network(self):
        deeplabcut.train_network(self.currentConfigPath, shuffle=1)

    def evaluate_network(self):
        deeplabcut.evaluate_network(self.currentConfigPath, plotting=True)

    def analyze_videos(self):
            deeplabcut.analyze_videos(self.currentConfigPath, config.VIDEOS_FOLDER, videoType=".avi", save_as_csv=True)

    def filter_predictions(self):
        deeplabcut.filterpredictions(self.currentConfigPath, "", shuffle=1)

    def create_labeled_video(self):
            deeplabcut.create_labeled_video(self.configPath, config.VIDEOS_FOLDER, filtered=True)

    def plot_trajectories(self):
            deeplabcut.plot_trajectories(self.currentConfigPath, config.VIDEOS_FOLDER, filtered=True)

    def extract_outlier_frames(self):
            deeplabcut.extract_outlier_frames(self.currentConfigPath, config.VIDEOS_FOLDER)

    def refine_labels(self):
        deeplabcut.refine_labels(self.currentConfigPath)

    def merge_datasets(self):
        deeplabcut.merge_datasets(self.currentConfigPath)
