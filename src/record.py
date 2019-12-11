import config
import os
import FlirController as fc

def main():

    flirController = fc.CameraController()

    while 1:

        print("\n[1] Exit")
        print("[2] New Trial")
        print("[3] Analyze Trials")
        menuIndex = input("Input: ")

        if menuIndex == '1':
            break
        elif menuIndex == '2':

            trialName = input("Enter trial name: ")
            path = config.VIDEOS_FOLDER + "\\" + str(trialName)

            try:
                os.mkdir(path)
            except OSError:
                print("Creation of the directory %s failed" % path)
                print("Try again!")
            else:
                print("Successfully created the directory %s " % path)
                flirController.synchronous_record(path)

        elif menuIndex == '3':

            trialFolders = os.listdir(config.VIDEOS_FOLDER)
            if 'calibration' in trialFolders: trialFolders.remove('calibration')
            if 'config.toml' in trialFolders: trialFolders.remove('config.toml')


            unanalyzedTrialsExist = False

            for trial in trialFolders:

                # Check if analysis was already done for this trial
                if os.path.isdir(config.VIDEOS_FOLDER + "\\" + str(trial) + "\\" + "videos-raw"):
                    continue
                else:
                    unanalyzedTrialsExist = True

                # Encode all the raw videos and delete the raw versions after
                os.chdir(config.VIDEOS_FOLDER + "\\" + str(trial))
                os.mkdir("videos-raw")
                os.system("batch_encode")

                for camIndex in range(0, config.NUM_CAMERAS):
                    os.rename("camera" + str(camIndex) + ".mp4", "videos-raw\\camera" + str(camIndex) + "-" + str(trial) + ".avi")

            if unanalyzedTrialsExist:
                # Run anipose
                os.chdir(config.VIDEOS_FOLDER)
                os.system("conda activate dlc-windowsGPU && anipose analyze")
                os.system("conda activate dlc-windowsGPU && anipose filter")
                os.system("conda activate dlc-windowsGPU && anipose triangulate")
                os.system("conda activate dlc-windowsGPU && anipose label-combined")





        else:
            print("Invalid selection! Try again.")

if __name__ == '__main__':
	main()


