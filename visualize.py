import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
import cv2
import json
from MouseTracker import MouseTracker
from time import sleep

def convertBack(x, y, w, h):
    xmin = int(round(x - (w / 2)))
    xmax = int(round(x + (w / 2)))
    ymin = int(round(y - (h / 2)))
    ymax = int(round(y + (h / 2)))
    return xmin, ymin, xmax, ymax
trialName = "verify"
darkFile = open("processed.json", "r")
darkData = json.loads(darkFile.read())

temp = input("Show overall track?")
if temp[0].lower() == 'y':
    fig = plt.figure()
    img = mpimg.imread("frameData_4mice/tracking_system" + trialName + "1.png")
    plt.imshow(img)
    plt.axis((0, 640, 0, 480))
    for datum in darkData.values():
        x = list(map(lambda l : int(l[0]*640/608), datum))
        y = list(map(lambda l : int(l[1]*480/608), datum))
        plt.plot(x, y)
    plt.show()
if True:
    fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')  # 'x264' doesn't work
    video = cv2.VideoWriter('output_pairs4mice.avi',fourcc, 20.0, (640, 480))
    frameCount = 2
    while True:
        try:
            frameName = "frameData_4mice/tracking_system" + trialName + str(frameCount) + ".png"
            frame_read = cv2.imread(frameName)
            frameCount += 1
            frame_rgb = cv2.cvtColor(frame_read, cv2.COLOR_BGR2RGB)
            print(frameCount)
        except Exception as e:
            print(str(e))
            break
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
                    cv2.rectangle(frame_rgb, pt1, pt2, (0, 255, 0), 1)
                    cv2.putText(frame_rgb,
                                str(tag),
                                (pt1[0], pt1[1] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                                [0, 255, 0], 2)
        video.write(frame_rgb)
    cv2.destroyAllWindows()
    video.release()



cont = 'y'
while cont is not 'n':
    frameCount = input("Input your desired validation frame number")
    if int(frameCount) > -1:
        fig = plt.figure()
        frameName = "frameData_4mice/tracking_system" + trialName + str(frameCount) + ".png"
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
