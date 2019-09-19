import csv
import sys
import os.path
from mpl_toolkits.mplot3d import axes3d
import matplotlib.pyplot as plt
import numpy as np
import cv2
from time import sleep
import pclpy

csvPath = None
dirPath = None
videoPath = None


if len(sys.argv) < 2:
    print("Not enough args...")
else:
    csvPath = sys.argv[1]
    dirPath = os.path.dirname(csvPath)
    videoPath = sys.argv[2]


def filter_dlc_3d_csv():

    rows = []
    upper_filter_bound = 70
    lower_filter_bound = -70


    with open(csvPath, 'r') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')

        line_count = 0
        for row in csv_reader:
            if line_count <= 2:
                # skip the first 3 rows since they are header info in dlc 3d csv's
                line_count += 1
            else:
                # skip the first column in each row since it is an index value
                for col_index in range(1, len(row)):
                    if row[col_index] != "":
                        if lower_filter_bound >= float(row[col_index]) >= upper_filter_bound:
                            row[col_index] = ""
                line_count += 1
            rows.append(row)

    with open(dirPath + '/filtered.csv', 'w') as writeFile:
        writer = csv.writer(writeFile)
        writer.writerows(rows)



# Gets the DLC 3D output csv xyz coordinates and puts them into a list of lists.
# The indices of the outer list represent frame number, while the inner list index
# represent 0=x, 1=y and 2=z)
def get_xyz_vals():

    frame_vals = []

    with open(csvPath, 'r') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')

        line_count = 0
        for row in csv_reader:
            if line_count <= 2:
                # skip the first 3 rows since they are header info in dlc 3d csv's
                line_count += 1
            else:

                x_vals = []
                y_vals = []
                z_vals = []

                # skip the first column in each row since it is an index value
                for col_index in range(1, len(row), 3):

                    if row[col_index] != "":
                        x_vals.append(float(row[col_index]))
                    else:
                        x_vals.append(np.nan)

                    if row[col_index + 1] != "":
                        y_vals.append(float(row[col_index + 1]))
                    else:
                        y_vals.append(np.nan)

                    if row[col_index + 2] != "":
                        z_vals.append(float(row[col_index + 2]))
                    else:
                        z_vals.append(np.nan)

                frame_vals.append([x_vals, y_vals, z_vals])
                line_count += 1

    return frame_vals

def plot_dlc_3d(frame_vals):


    cap = cv2.VideoCapture(videoPath)
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    framenum = 1
    for frame in frame_vals:

        plt.cla()
        ax.set_xlim3d(-10, 40)
        ax.set_ylim3d(-40,30)
        ax.set_zlim3d(-30,40)
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.scatter(frame[0][0], frame[1][0], frame[2][0], marker="*")
        ax.scatter(frame[0][1:3], frame[1][1:3], frame[2][1:3], marker="v",)
        ax.scatter(frame[0][3:5], frame[1][3:5], frame[2][3:5], marker="o",)
        ax.scatter(frame[0][5:], frame[1][5:], frame[2][5:], marker="_")
        plt.pause(0.001)
        ret, frame = cap.read()
        cv2.imshow('vid',frame)
        cv2.waitKey(1)
        print(str(framenum))
        framenum += 1



def convert_dlc3d_csv_to_pcd(frame_vals):

    pcd_header = """# .PCD v.7 - Point Cloud Data file format
VERSION .7
FIELDS x y z
SIZE 8 8 8
TYPE F F F
COUNT 1 1 1
WIDTH 19
HEIGHT 1
VIEWPOINT 0 0 0 1 0 0 0
POINTS 19
DATA ascii
"""

    # Outer list represents frames, while inner list contains all 19 points for that frame.
    # Each point has an x,y and z value.
    frame_points = []
    points = []

    for frame in frame_vals:

        for i in range(0, len(frame[0])):

            x = frame[0][i]
            y = frame[1][i]
            z = frame[2][i]
            points.append((x,y,z))

        frame_points.append(points)
        points = []

    for frame in frame_points:

        with open('test.pcd', 'w') as pcd_file:

            pcd_file.write(pcd_header)

            for point in frame:
                pcd_file.write(str(point[0]) + " " + str(point[1]) + " " + str(point[2]) + "\n")

        # Each frame gets it's own .pcd file containing all the points for that frame.
        # We don't want to generate thousands of files so exit after 1 frame.
        exit()





frame_vals = get_xyz_vals()
#plot_dlc_3d(frame_vals)
convert_dlc3d_csv_to_pcd(frame_vals)
