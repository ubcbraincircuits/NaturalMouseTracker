import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
import cv2
import json
import os
import shutil
import argparse
from MouseTracker import MouseTracker
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
args = vars(ap.parse_args())
dataPath = args.get("name", "_08132019")
darkFile = open("processed" + dataPath + ".json", "r")
darkData = json.loads(darkFile.read())

temp = input("Show overall track?")
if temp[0].lower() == 'y':
    fig = plt.figure()
    img = mpimg.imread("frameData" + dataPath + "/tracking_system" + trialName + "1.png")
    plt.imshow(img)
    plt.axis((0, 640, 0, 480))
    for datum in darkData.values():
        x = list(map(lambda l : int(l[0]*640/608), datum))
        y = list(map(lambda l : int(l[1]*480/608), datum))
        plt.plot(x, y)
    plt.show()
if True:
    fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')  # 'x264' doesn't work
    #video = cv2.VideoWriter('output_pairs08132019.avi',fourcc, 15.0, (640, 480))
    frameCount = 2
    lastFrameDict = {}
    fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')  # 'x264' doesn't work
    videos = {}
    files = {}
    try:
        shutil.rmtree("videos" + dataPath)
    except Exception as e:
        print(str(e))
        pass
    finally:
        os.mkdir("videos" + dataPath)
    for tag in darkData.keys():
        videos.update({tag: cv2.VideoWriter("videos" + dataPath + "/" + tag + ".avi" ,fourcc, 15.0, (640, 480))})
        lastFrameDict.update({tag: 0})
        files.update({tag: open("videos" + dataPath + "/"+ tag + ".txt", "w")})
    while True:
        try:
            frameName = "frameData"+ dataPath + "/tracking_system" + trialName + str(frameCount) + ".png"
            frame_read = cv2.imread(frameName)
            frameCount += 1
            frame_rgb = cv2.cvtColor(frame_read, cv2.COLOR_BGR2RGB)
            print(frameCount)
        except Exception as e:
            print(str(e))
            break
        for (tag, datum) in darkData.items():
            while True:
                if len(datum) <= lastFrameDict[tag]:
                    break
                if datum[lastFrameDict[tag]][3] == frameCount:
                    x, y, w, h = datum[lastFrameDict[tag]][0]*640/608,\
                        datum[lastFrameDict[tag]][1]*480/608,\
                        datum[lastFrameDict[tag]][4]*640/608,\
                        datum[lastFrameDict[tag]][5]*480/608
                    xmin, ymin, xmax, ymax = convertBack(
                        float(x), float(y), float(w), float(h))
                    pt1 = (xmin, ymin)
                    pt2 = (xmax, ymax)
                    blank_image = np.ones((480,640,3), np.uint8)*255
                    blank_image[pt1[1]:pt2[1], pt1[0]:pt2[0]] = frame_rgb[pt1[1]:pt2[1], pt1[0]:pt2[0]]
                    videos[tag].write(blank_image)
                    files[tag].write(str(frameCount) + "\n")
                    # cv2.rectangle(frame_rgb, pt1, pt2, (0, 255, 0), 1)
                    # cv2.putText(frame_rgb,
                    #             str(tag),
                    #             (pt1[0], pt1[1] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    #             [0, 255, 0], 2)
                    break
                elif datum[lastFrameDict[tag]][3] < frameCount:
                    lastFrameDict[tag] += 1
                else:
                    break
        #video.write(frame_rgb)
    cv2.destroyAllWindows()
    for video in videos.values():
        video.release()
    for file in files.values():
        file.close()



cont = 'y'
while cont is not 'n':
    frameCount = input("Input your desired validation frame number")
    if int(frameCount) > -1:
        fig = plt.figure()
        frameName = "frameData_08132019/tracking_system" + trialName + str(frameCount) + ".png"
        img = cv2.imread(frameName)
        for (tag, datum) in darkData.items():
            for position in datum:
                if position[2]==frameName:
                    x, y, w, h = position[0]*640/608,\
                        position[1]*480/608,\
                        position[4]*640/608,\
                        position[5]*480/608
                    xmin, ymin, xmax, ymax = convertBack(
                        float(x), float(y), float(w), float(h))
                    pt1 = (xmin, ymin)
                    pt2 = (xmax, ymax)
                    cv2.rectangle(img, pt1, pt2, (0, 255, 0), 1)
        plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        for (tag, datum) in darkData.items():
            for position in datum:
                if position[2]==frameName:
                    plt.text(position[0]*640/608, position[1]*480/608, tag, color="r")
        plt.show()
    cont = input("Another frame?")
