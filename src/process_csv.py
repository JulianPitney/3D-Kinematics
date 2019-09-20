import csv
import sys
import os.path
from mpl_toolkits.mplot3d import axes3d #unused import is actually used by mpl...idk why but don't remove
import matplotlib.pyplot as plt
import numpy as np
import cv2
import open3d as o3d
import copy

csvPath_1 = None
csvPath_2 = None
csvPath_3 = None
csvPath_4 = None

videoPath = None
dirPath = None

if len(sys.argv) == 5:
    csvPath_1 = sys.argv[1]
    csvPath_2 = sys.argv[2]
    csvPath_3 = sys.argv[3]
    csvPath_4 = sys.argv[4]
    dirPath = os.path.dirname(csvPath_1)
elif len(sys.argv) == 6:
    csvPath_1 = sys.argv[1]
    csvPath_2 = sys.argv[2]
    csvPath_3 = sys.argv[3]
    csvPath_4 = sys.argv[4]
    dirPath = os.path.dirname(csvPath_1)
    videoPath = sys.argv[5]
else:
    print("Usage: python process_csv.py <csv_path_1> <csv_path_2> <csv_path_3> <csv_path_4> <video_path>")
    exit()

def filter_dlc_3d_csv(csvPath):

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



# Gets the DLC 3D output csv xyz coordinates and put them into a list of lists.
# The indices of the outer list represent frame number, while the inner list index
# represent 0=x, 1=y and 2=z)
def get_xyz_vals(csvPath):

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


# Plotting is specific to the points being tracked and should be rewritten accordingly.
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



def gen_pcd(frame_vals, output_file_name):


    # Build ,pcd header
    pcd_header = """# .PCD v.7 - Point Cloud Data file format
VERSION .7
FIELDS x y z
SIZE 8 8 8
TYPE F F F
COUNT 1 1 1
WIDTH """ + str(len(frame_vals[0][0])) + """\nHEIGHT 1
VIEWPOINT 0 0 0 1 0 0 0
POINTS """ + str(len(frame_vals[0][0])) + "\nDATA ascii\n"



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

        with open(output_file_name + '.pcd', 'w') as pcd_file:

            pcd_file.write(pcd_header)


            for point in frame_points[3000]:
                pcd_file.write(str(point[0]) + " " + str(point[1]) + " " + str(point[2]) + "\n")

        # Each frame gets it's own .pcd file containing all the points for that frame.
        # We don't want to generate thousands of files right now so exit after 1 frame.
        break



def draw_registration_result(source, target, transformation):
    source_temp = copy.deepcopy(source)
    target_temp = copy.deepcopy(target)
    source_temp.paint_uniform_color([1, 0.706, 0])
    target_temp.paint_uniform_color([0, 0.651, 0.929])
    source_temp.transform(transformation)
    o3d.visualization.draw_geometries([source_temp, target_temp])



frame_vals_1 = get_xyz_vals(csvPath_1)
frame_vals_2 = get_xyz_vals(csvPath_2)
frame_vals_3 = get_xyz_vals(csvPath_3)
frame_vals_4 = get_xyz_vals(csvPath_4)

gen_pcd(frame_vals_1, "1")
gen_pcd(frame_vals_2, "2")
gen_pcd(frame_vals_3, "3")
gen_pcd(frame_vals_4, "4")

source = o3d.io.read_point_cloud('1.pcd')
target = o3d.io.read_point_cloud('2.pcd')
threshold = 0.02

# perform initial alignment
trans_init = np.asarray([[0.862, 0.011, -0.507, 0.5],
                         [-0.139, 0.967, -0.215, 0.7],
                         [0.487, 0.255, 0.835, -1.4], [0.0, 0.0, 0.0, 1.0]])
draw_registration_result(source, target, trans_init)


# ICP Registration
reg_p2p = o3d.registration.registration_icp(
    source, target, threshold, trans_init,
    o3d.registration.TransformationEstimationPointToPoint())
draw_registration_result(source, target, reg_p2p.transformation)

