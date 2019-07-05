import deeplabcut

menuMsg = """Select Function: 
[1] Create Project 
[2] Extract Frames
[3] Label Frames 
[4] Check Labels 
[5] Create Training Dataset 
[6] Train Network 
[7] Evaluate Network 
[8] Analyze Videos 
[9] Filter Predictions 
[10] Create Labeled Videos 
[11] Plot Trajectories 
[12] Refine Network 
[13] Exit
Input: """

CONFIG_PATH = ""
VIDEO_FOLDER_PATH = ""




def create_proj():

    global CONFIG_PATH, VIDEO_FOLDER_PATH

    PROJECT_NAME = input("Project Name: ")
    EXPERIMENTER_NAME = input("Experimenter Name: ")
    VIDEO_FOLDER_PATH = input("Video Folder Path: ")
    VIDEO_PATHS = ['../videos/output1.avi', '../videos/output2.avi']
    FULL_PATH_WORKING_DIRECTORY = 'C:/Projects/3D-Kinematics/dlc_projects/'
    CONFIG_PATH = deeplabcut.create_new_project(PROJECT_NAME, EXPERIMENTER_NAME, VIDEO_PATHS, FULL_PATH_WORKING_DIRECTORY, copy_videos=False)



def extract_frames():

    global CONFIG_PATH

    EXTRACTION_MODES = ['automatic', 'manual']
    AUTO_EXTRACTION_METHOD = ['uniform', 'kmeans']
    FRAME_EXTRACTION_MODE = EXTRACTION_MODES[0]
    AUTO_EXTRACTION_MODE = AUTO_EXTRACTION_METHOD[0]
    deeplabcut.extract_frames(CONFIG_PATH, FRAME_EXTRACTION_MODE, AUTO_EXTRACTION_MODE, crop=True)

def label_frames():

    global CONFIG_PATH
    deeplabcut.label_frames(CONFIG_PATH)

def check_labels():

    global CONFIG_PATH
    deeplabcut.check_labels(CONFIG_PATH)

def create_training_dataset():

    global CONFIG_PATH
    deeplabcut.create_training_dataset(CONFIG_PATH, num_shuffles=1)

def train_network():

    global CONFIG_PATH
    deeplabcut.train_network(CONFIG_PATH, shuffle=1)

def evaluate_network():

    global CONFIG_PATH
    deeplabcut.evaluate_network(CONFIG_PATH, shuffle=[1], plotting=True)

def analyze_videos():

    global CONFIG_PATH, VIDEO_FOLDER_PATH
    VIDEO_TYPE = '.avi'
    deeplabcut.analyze_videos(CONFIG_PATH, VIDEO_FOLDER_PATH, VIDEO_TYPE, save_as_csv=True)

def filter_predictions():

    global CONFIG_PATH
    VIDEO_PATH = input("Video Path: ")
    deeplabcut.filterpredictions(CONFIG_PATH, VIDEO_PATH, shuffle=1)

def create_labeled_videos():

    global CONFIG_PATH, VIDEO_FOLDER_PATH
    deeplabcut.create_labeled_video(CONFIG_PATH, VIDEO_FOLDER_PATH, filtered=True)

def plot_trajectories():

    global CONFIG_PATH, VIDEO_FOLDER_PATH
    deeplabcut.plot_trajectories(CONFIG_PATH, VIDEO_FOLDER_PATH, filtered=True)

def refine_network():

    global CONFIG_PATH, VIDEO_FOLDER_PATH
    deeplabcut.extract_outlier_frames(CONFIG_PATH, VIDEO_FOLDER_PATH)
    deeplabcut.refine_labels(CONFIG_PATH)
    deeplabcut.merge_datasets(CONFIG_PATH)





while(1):

    menuSelection = input(menuMsg)
    try:
       menuSelection = int(menuSelection)
    except ValueError:
        print("Invalid selection, try again.")
        continue

    if menuSelection == 1:
        create_proj()
    elif menuSelection == 2:
        extract_frames()
    elif menuSelection == 3:
        label_frames()
    elif menuSelection == 4:
        check_labels()
    elif menuSelection == 5:
        create_training_dataset()
    elif menuSelection == 6:
        train_network()
    elif menuSelection == 7:
        evaluate_network()
    elif menuSelection == 8:
        analyze_videos()
    elif menuSelection == 9:
        filter_predictions()
    elif menuSelection == 10:
        create_labeled_videos()
    elif menuSelection == 11:
        plot_trajectories()
    elif menuSelection == 12:
        refine_network()
    elif menuSelection == 13:
        exit()
    else:
        "Invalid selection, try again."




