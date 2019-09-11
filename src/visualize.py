import os
import re
import pandas
import cv2
import numpy as np
from threading import Thread
import matplotlib
matplotlib.use('TkAgg')
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
from collections import deque
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Button, Slider
import time

def find_tiple_files(root_dir):
    """
    Generate a dictionary object holding all the data given by deeplabcut.
    :param root_dir:
    :return:
    """
    csv_list = [os.path.join(root_dir, candidate) for candidate in os.listdir(root_dir) if candidate.endswith('.csv')]
    video_list = [os.path.join(root_dir, candidate) for candidate in os.listdir(root_dir) if candidate.endswith('.mp4')]
    pattern = 'output'
    prog = re.compile(pattern)

    file_dict = {}
    for csv_file in csv_list:
        match_list = prog.findall(csv_file)
        if len(match_list) > 0:
            if match_list[0] not in file_dict.keys():
                file_dict[match_list[0]] = {}
            if 'camera-3' in csv_file:
                file_dict[match_list[0]]['camera-1'] = {"csv": csv_file}
            elif 'camera-4' in csv_file:
                file_dict[match_list[0]]['camera-2'] = {"csv": csv_file}
            else:
                file_dict[match_list[0]]['3d'] = {"csv": csv_file}

    for video_file in video_list:
        match_list = prog.findall(video_file)
        if len(match_list) > 0:
            if match_list[0] in file_dict.keys():
                if 'camera-3' in video_file:
                    file_dict[match_list[0]]['camera-1']["video"] = video_file
                elif 'camera-4' in video_file:
                    file_dict[match_list[0]]['camera-2']["video"] = video_file
                else:
                    file_dict[match_list[0]]['3d']["video"] = video_file

    return file_dict

def load_csv(file_path):
    """
    Load a csv file predicted by deeplabcut and transfer it into a pure dictionary.
    :param file_path:
    :return:
    """
    df = pandas.read_csv(file_path, skiprows=1)
    df = df.drop(df.columns[[0]], axis=1)
    data = df.to_dict()
    data_dict = {}
    for key in data.keys():
        name = key.split('.')[0]
        if name not in data_dict.keys():
            data_dict[name] = {}
        if data[key][0] not in data_dict[name].keys():
            data_dict[name][data[key][0]] = [float(v) for v in [v for v in data[key].values()][1:]]
    return data_dict

current_frame = 0

def visualize_both(path_video_1, path_csv_1, path_video_2, path_csv_2):

    global current_frame
    FLAG_PAUSE = False
    stop_frame = current_frame
    data_1 = load_csv(path_csv_1)
    data_2 = load_csv(path_csv_2)
    stream_1 = cv2.VideoCapture(path_video_1)
    stream_2 = cv2.VideoCapture(path_video_2)

    assert int(stream_1.get(cv2.CAP_PROP_FRAME_COUNT)) == int(stream_2.get(cv2.CAP_PROP_FRAME_COUNT))
    max_frame_count = int(stream_1.get(cv2.CAP_PROP_FRAME_COUNT))

    window_name = os.path.basename(path_video_1)
    cv2.startWindowThread()

    cv2.namedWindow(window_name)
    print(path_video_1)

    def onTrackbarSlide(frame):
        global current_frame
        global stop_frame
        current_frame = frame
        stop_frame = current_frame
        stream_1.set(cv2.CAP_PROP_POS_FRAMES, frame)
        stream_2.set(cv2.CAP_PROP_POS_FRAMES, frame)


    if stream_1.isOpened() and stream_2.isOpened():

        cv2.createTrackbar('Slider', window_name, 0, max_frame_count, onTrackbarSlide)

        while True:
            grab_1, frame_1 = stream_1.read()
            grab_2, frame_2 = stream_2.read()
            if grab_1 and grab_2:
                if not FLAG_PAUSE:
                    current_frame = int(stream_1.get(cv2.CAP_PROP_POS_FRAMES))
                else:
                    stream_1.set(cv2.CAP_PROP_POS_FRAMES, stop_frame)
                    stream_2.set(cv2.CAP_PROP_POS_FRAMES, stop_frame)

                if current_frame >= max_frame_count - 1:
                    current_frame = 0
                for key in data_1.keys():
                    # print("length:", len(data_1[key]['x']))
                    likelihood = data_1[key]['likelihood'][current_frame - 1]
                    if likelihood > 0.75:
                        x = int(data_1[key]['x'][current_frame])
                        y = int(data_1[key]['y'][current_frame])
                        cv2.circle(frame_1, (x, y), 5, (255, 0, 0), 3, 8)
                padding_frame = np.zeros(frame_1.shape, dtype=np.uint8)
                padding_frame[:frame_2.shape[0], :frame_2.shape[1], :] = frame_2
                frame_2 = padding_frame
                for key in data_2.keys():
                    likelihood = data_2[key]['likelihood'][current_frame]
                    if likelihood > 0.75:
                        x = int(data_2[key]['x'][current_frame])
                        y = int(data_2[key]['y'][current_frame])
                        cv2.circle(frame_2, (x, y), 5, (255, 0, 0), 3, 8)

                frame_show = np.concatenate([frame_1, frame_2], axis=1)
                cv2.imshow(window_name, frame_show)
                cv2.setTrackbarPos('Slider', window_name, current_frame)
                key = cv2.waitKey(1)
                if key & 0xFF == ord('q'):
                    cv2.waitKey(1)
                    stream_1.release()
                    cv2.waitKey(1)
                    stream_2.release()
                    cv2.waitKey(1)
                    cv2.destroyAllWindows()
                    cv2.waitKey(1)
                    break
                elif key & 0xFF == ord(' '):
                    if FLAG_PAUSE:
                        FLAG_PAUSE = False
                        current_frame = stop_frame
                    else:
                        FLAG_PAUSE = True
                        stop_frame = current_frame
            else:
                break



def plot_3d_test(data_3d):
    global current_frame
    data_list = []
    min_x, max_x, min_y, max_y, min_z, max_z = [None for i in range(6)]
    length = 0
    for key in data_3d.keys():
        x = data_3d[key]['x']
        x, x_min_candidate, x_max_candidate = filter_nan(x)
        if len(x) > 0:
            length = len(x)
            if min_x == None or x_min_candidate < min_x:
                min_x = x_min_candidate
            if max_x == None or x_max_candidate > max_x:
                max_x = x_max_candidate

        y = data_3d[key]['z']
        y, y_min_candidate, y_max_candidate = filter_nan(y)
        if len(y) > 0:
            if min_y == None or y_min_candidate < min_y:
                min_y = y_min_candidate
            if max_y == None or y_max_candidate > max_y:
                max_y = y_max_candidate

        z = data_3d[key]['y']
        z, z_min_candidate, z_max_candidate = filter_nan(z)
        if len(z) > 0:
            if min_z == None or z_min_candidate < min_z:
                min_z = z_min_candidate
            if max_z == None or z_max_candidate > max_z:
                max_z = z_max_candidate
        data_list.append({'x': x, 'y': y, 'z': z})

    for i in range(len(data_list)):
        if len(data_list[i]['x']) == 0:
            data_list[i]['x'] = [min_x - 1000 for i in range(length)]
        if len(data_list[i]['y']) == 0:
            data_list[i]['y'] = [min_y - 1000 for i in range(length)]
        if len(data_list[i]['z']) == 0:
            data_list[i]['z'] = [min_z - 1000 for i in range(length)]

    fps = 10  # Frame per sec

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    marker_list = ['o', 'v', 's', '*', 'o', 'v', 's', '*', 'o', 'v']
    sct_list = []
    for marker in marker_list:
        sct_list.append(ax.plot([], [], [], marker, markersize=5)[0])

    def update_points(ifrm, data_list):
        for i in range(len(sct_list)):
            sct = sct_list[i]
            sct.set_data(data_list[i]['x'][current_frame], data_list[i]['y'][current_frame])
            sct.set_3d_properties(data_list[i]['z'][current_frame])



    ax.set_xlim(min_x - 2, max_x + 2)
    ax.set_ylim(min_y - 2, max_y + 2)
    ax.set_zlim(min_z - 2, max_z + 2)
    ani = animation.FuncAnimation(fig, update_points, length, fargs=([data_list]), interval=1000 / fps)
    plt.show()

def filter_nan(x, inverse=False):

    x_value_list = [i for i in x if str(i) != 'nan']
    x_filtered = []
    x_min_candidate, x_max_candidate = None, None
    if len(x_value_list) > 0:
        x_min_candidate = min(x_value_list)
        x_max_candidate = max(x_value_list)

        for item in x:
            if str(item) == 'nan':
                x_filtered.append(x_min_candidate - 1000)
            else:
                x_filtered.append(item)
    return x_filtered, x_min_candidate, x_max_candidate

def main(root_dir, which_video):
    """
    Notice this directory contains videos for both cameras, analysed files generated by two deeplabcut projects, 3d reconstruction file from deeplabcut.
    :param root_dir:
    :return:
    """
    file_dict = find_tiple_files(root_dir)
    keys = list(file_dict.keys())
    key = keys[which_video]

    print("We are watching %s" % key)
    path_video_1 = file_dict[key]['camera-1']['video']
    path_csv_1 = file_dict[key]['camera-1']['csv']
    path_video_2 = file_dict[key]['camera-2']['video']
    path_csv_2 = file_dict[key]['camera-2']['csv']

    thread_1 = Thread(target=visualize_both, args=[path_video_1, path_csv_1, path_video_2, path_csv_2])
    thread_1.start()

    path_csv_3d = file_dict[key]['3d']['csv']
    data_3d = load_csv(path_csv_3d)
    plot_3d_test(data_3d)
    thread_1.join()


if __name__ == '__main__':

    root_dir = r"C:\Projects\3D-Kinematics\videos\pair3-4"
    print(find_tiple_files(root_dir))
    which_video = 0

    main(root_dir, which_video)


