import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
import cv2
import json
import os
import shutil
import argparse
from MouseTracker import MouseTracker
from filterpy.kalman import KalmanFilter
from filterpy.common import Q_discrete_white_noise
from time import sleep

def convertBack(x, y, w, h):
    xmin = int(round(x - (w / 2)))
    xmax = int(round(x + (w / 2)))
    ymin = int(round(y - (h / 2)))
    ymax = int(round(y + (h / 2)))
    return xmin, ymin, xmax, ymax
trialName = "base_tracking"
ap = argparse.ArgumentParser()
ap.add_argument("-n", "--name", help="Name of the frame folder/text file")
ap.add_argument("-d", "--drive", help="Path to data")
ap.add_argument("-f", "--frames", help="Include this argument if you have individual frame files")
args = vars(ap.parse_args())
dataPath = args.get("name")
dataDrive = args.get("drive", "frameData")
frames = False
if args.get("frames", None) is not None:
    frames = True
darkFile = open(dataDrive + dataPath + "/processed.json", "r")
darkData = json.loads(darkFile.read())

temp = input("Show overall track?")
if temp[0].lower() == 'y':
    fig, (ax1, ax2) = plt.subplots(2)
    # plt.imshow(img)
    for datum in darkData.values():
        del_t = 0.1
        f = KalmanFilter(dim_x = 6, dim_z = 2)
        f.x = np.array([datum[0][0], 0., 0., datum[0][1], 0., 0])
        f.F = np.array([[1, del_t, 0.5*del_t**2, 0., 0., 0.],
                            [0., 1, del_t, 0., 0., 0.],
                            [0., 0., 1, 0, 0, 0],
                            [0, 0, 0., 1, del_t, 0.5*del_t**2],
                            [0., 0, 0, 0, 1, del_t],
                            [0, 0., 0, 0, 0, 1]])
        # f.F = np.array([[1, del_t, 0., 0],
        #                     [0., 1,  0., 0.],
        #                     [0., 0., 1, del_t],
        #                     [0., 0., 0., 1]])
        f.H = np.array([[1, 0, 0., 0, 0,0,],
                            [0, 0., 0, 1, 0, 0]])
        # f.H = np.array([[1, 0, 0., 0,],
        #                     [0, 0., 1, 0]])
        f.P = np.array([[350000, 0, 0, 0., 0., 0.],
                            [0., 7000, 0, 0., 0., 0.],
                            [0., 0., 2700000, 0, 0, 0],
                            [0, 0, 0., 250000, 0, 0],
                            [0., 0, 0, 0, 16470, 0],
                            [0, 0., 0, 0, 0, 2000000]])
        # f.P = np.array([[350000, 0, 0, 0],
        #                     [0., 7000, 0, 0.],
        #                     [0., 0, 16470, 0],
        #                     [0, 0., 0, 2000000]])
        f.R = np.array([[330., 52],
                            [52., 231]])
        f.Q = Q_discrete_white_noise(dim=3, dt=0.1, var=300, block_size=2)
        # f.Q = Q_discrete_white_noise(dim=2, dt=0.1, var=10, block_size=2)
        filtered_x = []
        vel_x = []
        filtered_y = []
        vel_y = []
        x = list(map(lambda l : int(l[0]), datum))
        frames = list(map(lambda l : int(l[3]), datum))
        y = list(map(lambda l : int(l[1]), datum))
        for index in range(0, len(frames)):
            z = np.array([[x[index]], [y[index]]])
            f.predict()
            f.update(z)
            filtered_x.append(f.x[0])
            vel_x.append(f.x[1])
            filtered_y.append(f.x[3])
            vel_y.append(f.x[4])
        ax1.set_xlim([0, 1000])
        ax1.plot(frames, x, 'r+')
        ax1.plot(frames, filtered_x)
        ax1.plot(frames, vel_x)
        print(len(frames), len(y))
        ax2.set_xlim([0, 1000])
        ax2.plot(frames, y, 'r+')
        ax2.plot(frames, filtered_y)
        ax2.plot(frames, vel_y)
        break
    plt.show()
fourcc = cv2.VideoWriter_fourcc(*'MJPG')  # 'x264' doesn't work
main = cv2.VideoWriter('output_filtered_' + dataPath + '.avi', fourcc, 15.0, (912, 720))
table = np.array([((i/255.0) ** 0.75)*255 #0.7 to 0.9 seems like a good range.
    for i in np.arange(0, 256)]).astype('uint8')
frameCount = 2
lastFrameDict = {}
# 'x264' doesn't work2018121290,2018121255,801010273,2018121360
videos = {}
files = {}
filters = {}
try:
    shutil.rmtree(dataDrive + dataPath + "/videos")
except Exception as e:
    print(str(e))
    pass
finally:
    os.mkdir(dataDrive + dataPath + "/videos")
for tag, datum in darkData.items():
    if len(datum) < 1:
        break
    videos.update({tag: cv2.VideoWriter(dataDrive + dataPath + "/videos/" + tag + ".avi" ,fourcc, 15.0, (912, 720))})
    lastFrameDict.update({tag: 0})
    files.update({tag: open(dataDrive + dataPath + "/videos/" + tag + ".txt", "w")})
    del_t = 0.1
    f = KalmanFilter(dim_x = 6, dim_z = 2)
    f.x = np.array([darkData[tag][0][0], 0., 0., darkData[tag][0][1], 0., 0])
    f.F = np.array([[1, del_t, 0.5*del_t**2, 0., 0., 0.],
                        [0., 1, del_t, 0., 0., 0.],
                        [0., 0., 1, 0, 0, 0],
                        [0, 0, 0., 1, del_t, 0.5*del_t**2],
                        [0., 0, 0, 0, 1, del_t],
                        [0, 0., 0, 0, 0, 1]])
    # f.F = np.array([[1, del_t, 0., 0],
    #                     [0., 1,  0., 0.],
    #                     [0., 0., 1, del_t],
    #                     [0., 0., 0., 1]])
    f.H = np.array([[1, 0, 0., 0, 0,0,],
                        [0, 0., 0, 1, 0, 0]])
    # f.H = np.array([[1, 0, 0., 0,],
    #                     [0, 0., 1, 0]])
    f.P = np.array([[350000, 0, 0, 0., 0., 0.],
                        [0., 7000, 0, 0., 0., 0.],
                        [0., 0., 2700000, 0, 0, 0],
                        [0, 0, 0., 250000, 0, 0],
                        [0., 0, 0, 0, 16470, 0],
                        [0, 0., 0, 0, 0, 2000000]])
    # f.P = np.array([[350000, 0, 0, 0],
    #                     [0., 7000, 0, 0.],
    #                     [0., 0, 16470, 0],
    #                     [0, 0., 0, 2000000]])
    f.R = np.array([[330., 52],
                        [52., 231]])
    f.Q = Q_discrete_white_noise(dim=3, dt=0.1, var=300, block_size=2)
    # f.Q = Q_discrete_white_noise(dim=2, dt=0.1, var=10, block_size=2)
    filters.update({tag: f})
if not frames:
    cap = cv2.VideoCapture(dataDrive + dataPath + "/tracking_system" + trialName + ".h264")
while True:
    try:
        frameName = dataDrive + dataPath + "/tracking_system" + trialName + str(frameCount) + ".jpg"
        if frames:
            frame_read = cv2.imread(frameName)
        else:
            success, frame_read = cap.read()
            if not success:
                break
        frameCount += 1
        frame_read = cv2.LUT(frame_read, table)
        frame_rgb = cv2.cvtColor(frame_read, cv2.COLOR_BGR2GRAY)
        frame_rgb_c = cv2.cvtColor(frame_read, cv2.COLOR_BGR2GRAY)
        frame_rgb = cv2.cvtColor(frame_rgb, cv2.COLOR_GRAY2RGB)
        frame_rgb_c = cv2.cvtColor(frame_rgb_c, cv2.COLOR_GRAY2RGB)
        print(frameCount)
    except Exception as e:
        print(str(e), 'er')
        break
    for (tag, datum) in darkData.items():
        if len(datum) < 1:
            break
        del_t = 0.1
        while True:
            if len(datum) <= lastFrameDict[tag]:
                break
            if datum[lastFrameDict[tag]][3] == frameCount -1:
                w, h = datum[lastFrameDict[tag]][4]*912/640,\
                    datum[lastFrameDict[tag]][5]*720/640
                z = np.array([[datum[lastFrameDict[tag]][0]], [datum[lastFrameDict[tag]][1]]])
                filters[tag].predict()
                filters[tag].update(z)
                #x, vel_x, y, vel_y = filters[tag].x[0]*640/640, filters[tag].x[1]*640/640, filters[tag].x[3]*480/640, filters[tag].x[4]*480/640
                x, y = z[0]*912/640, z[1]*720/640
                xmin, ymin, xmax, ymax = convertBack(
                    float(x), float(y), float(w), float(h))
                pt1 = (xmin, ymin)
                pt2 = (xmax, ymax)
                blank_image = np.ones((720,912,3), np.uint8)*255
                blank_image[pt1[1]:pt2[1], pt1[0]:pt2[0]] = frame_rgb[pt1[1]:pt2[1], pt1[0]:pt2[0]]
                videos[tag].write(blank_image)
                files[tag].write(str(frameCount -1) + "\n")
                cv2.rectangle(frame_rgb_c, pt1, pt2, (0, 255, 0), 1)
                cv2.circle(frame_rgb_c, (int(x), int(y)), 5,  [0, 255, 0])
                #cv2.arrowedLine(frame_rgb_c, (int(x - vel_x), int(y - vel_y)), (int(x + vel_x), int(y + vel_y)), [0, 0, 255])
                cv2.putText(frame_rgb_c,
                            str(tag),
                            (pt1[0], pt1[1] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                            [0, 255, 0], 2)
                break

            elif datum[lastFrameDict[tag]][3] < frameCount -1:
                lastFrameDict[tag] += 1
            else:
                break
    main.write(frame_rgb_c)
cv2.destroyAllWindows()
for video in videos.values():
    video.release()
main.release()
for file in files.values():
    file.close()
