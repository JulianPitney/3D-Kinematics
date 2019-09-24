import csv
import sys
import os.path
from mpl_toolkits.mplot3d import axes3d #unused import is actually used by mpl...idk why but don't remove
import matplotlib.pyplot as plt
import numpy as np
import cv2
import open3d as o3d
import copy
from open3d.open3d.geometry import estimate_normals


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






def prepare_dataset(voxel_size, source, target):
    print(":: Load two point clouds and disturb initial pose.")
    trans_init = np.asarray([[0.0, 0.0, 1.0, 0.0], [1.0, 0.0, 0.0, 0.0],
                             [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 0.0, 1.0]])
    source.transform(trans_init)
    draw_registration_result(source, target, np.identity(4))


    source_down, source_fpfh = preprocess_point_cloud(source, voxel_size)
    target_down, target_fpfh = preprocess_point_cloud(target, voxel_size)
    return source, target, source_down, target_down, source_fpfh, target_fpfh



def preprocess_point_cloud(pcd, voxel_size):

    # TODO: Failing here
    radius_normal = voxel_size * 2
    print(":: Estimate normal with search radius %.3f." % radius_normal)
    estimate_normals(pcd, o3d.geometry.KDTreeSearchParamHybrid(radius=radius_normal, max_nn=30))

    radius_feature = voxel_size * 5
    print(":: Compute FPFH feature with search radius %.3f." % radius_feature)
    pcd_fpfh = o3d.registration.compute_fpfh_feature(
        pcd,
        o3d.geometry.KDTreeSearchParamHybrid(radius=radius_feature, max_nn=100))
    return pcd, pcd_fpfh



def execute_global_registration(source_down, target_down, source_fpfh,
                                target_fpfh, voxel_size):
    distance_threshold = voxel_size * 1.5
    print(":: RANSAC registration on downsampled point clouds.")
    print("   Since the downsampling voxel size is %.3f," % voxel_size)
    print("   we use a liberal distance threshold %.3f." % distance_threshold)
    result = o3d.registration.registration_ransac_based_on_feature_matching(
        source_down, target_down, source_fpfh, target_fpfh, distance_threshold,
        o3d.registration.TransformationEstimationPointToPoint(False), 4, [
            o3d.registration.CorrespondenceCheckerBasedOnEdgeLength(0.9),
            o3d.registration.CorrespondenceCheckerBasedOnDistance(
                distance_threshold)
        ], o3d.registration.RANSACConvergenceCriteria(4000000, 500))
    return result



def refine_registration(source, target, source_fpfh, target_fpfh, voxel_size):
    distance_threshold = voxel_size * 0.4
    print(":: Point-to-plane ICP registration is applied on original point")
    print("   clouds to refine the alignment. This time we use a strict")
    print("   distance threshold %.3f." % distance_threshold)
    result = o3d.registration.registration_icp(
        source, target, distance_threshold, result_ransac.transformation,
        o3d.registration.TransformationEstimationPointToPoint())
    return result





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


voxel_size = 0.4
source, target, source_down, target_down, source_fpfh, target_fpfh = \
    prepare_dataset(voxel_size)

result_ransac = execute_global_registration(source_down, target_down,
                                                source_fpfh, target_fpfh,
                                                voxel_size)
print(result_ransac)
draw_registration_result(source_down, target_down, result_ransac.transformation)

result_icp = refine_registration(source, target, source_fpfh, target_fpfh,
                                 voxel_size)
print(result_icp)
draw_registration_result(source, target, result_icp.transformation)



