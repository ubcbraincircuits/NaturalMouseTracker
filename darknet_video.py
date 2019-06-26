"""
Final processing file. Copy into the darknet folder to run.
Adapted from https://github.com/AlexeyAB/darknet
"""

from ctypes import *
import math
import random
import os
import cv2
import numpy as np
import time
import darknet
import json
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
from MouseTracker import MouseTracker

def convertBack(x, y, w, h):
    xmin = int(round(x - (w / 2)))
    xmax = int(round(x + (w / 2)))
    ymin = int(round(y - (h / 2)))
    ymax = int(round(y + (h / 2)))
    return xmin, ymin, xmax, ymax


def cvDrawBoxes(detections, img):
    for detection in detections:
        x, y, w, h = detection[2][0],\
            detection[2][1],\
            detection[2][2],\
            detection[2][3]
        xmin, ymin, xmax, ymax = convertBack(
            float(x), float(y), float(w), float(h))
        pt1 = (xmin, ymin)
        pt2 = (xmax, ymax)
        cv2.rectangle(img, pt1, pt2, (0, 255, 0), 1)
        cv2.putText(img,
                    str(detection[0]) +
                    " [" + str(round(detection[1] * 100, 2)) + "]",
                    (pt1[0], pt1[1] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    [0, 255, 0], 2)
    return img


netMain = None
metaMain = None
altNames = None


def YOLO(trialName, mice, RFID):
    miceNum = len(mice)

    global metaMain, netMain, altNames
    configPath = "./yolo-obj.cfg"
    weightPath = "./yolo-obj_last.weights"
    metaPath = "./data/obj.data"
    if not os.path.exists(configPath):
        raise ValueError("Invalid config path `" +
                         os.path.abspath(configPath)+"`")
    if not os.path.exists(weightPath):
        raise ValueError("Invalid weight path `" +
                         os.path.abspath(weightPath)+"`")
    if not os.path.exists(metaPath):
        raise ValueError("Invalid data file path `" +
                         os.path.abspath(metaPath)+"`")
    if netMain is None:
        netMain = darknet.load_net_custom(configPath.encode(
            "ascii"), weightPath.encode("ascii"), 0, 1)  # batch size = 1
    if metaMain is None:
        metaMain = darknet.load_meta(metaPath.encode("ascii"))
    if altNames is None:
        try:
            with open(metaPath) as metaFH:
                metaContents = metaFH.read()
                import re
                match = re.search("names *= *(.*)$", metaContents,
                                  re.IGNORECASE | re.MULTILINE)
                if match:
                    result = match.group(1)
                else:
                    result = None
                try:
                    if os.path.exists(result):
                        with open(result) as namesFH:
                            namesList = namesFH.read().strip().split("\n")
                            altNames = [x.strip() for x in namesList]
                except TypeError:
                    pass
        except Exception:
            pass
    #cap = cv2.VideoCapture(0)
    # cap = cv2.VideoCapture("mice4.mp4")
    # cap.set(3, 1280)
    # cap.set(4, 720)
    out = cv2.VideoWriter(
        "output.avi", cv2.VideoWriter_fourcc(*"MJPG"), 10.0,
        (darknet.network_width(netMain), darknet.network_height(netMain)))
    print("Starting the YOLO loop...")

    # Create an image we reuse for each detect
    darknet_image = darknet.make_image(darknet.network_width(netMain),
                                    darknet.network_height(netMain),3)
    frameCount = 0
    lostTrackers = []
    error = False
    dummyTag = 0
    while True:
        try:
            prev_time = time.time()
            frameName = "frameData/tracking_system" + trialName + str(frameCount) + ".png"
            frame_read = cv2.imread(frameName)
            frameCount += 1
            frame_rgb = cv2.cvtColor(frame_read, cv2.COLOR_BGR2RGB)
            frame_resized = cv2.resize(frame_rgb,
                                       (darknet.network_width(netMain),
                                        darknet.network_height(netMain)),
                                       interpolation=cv2.INTER_LINEAR)
        except Exception as e:
            #no more frames
            break
        darknet.copy_image_from_bytes(darknet_image,frame_resized.tobytes())

        detections = darknet.detect_image(netMain, metaMain, darknet_image, thresh=0.3)

        # print(1/(time.time()-prev_time))
        updatedTags = []
        if frameCount == 1:
            for mouse in mouseTrackers:
                lostTrackers.append(mouse)
            mice = []
            for detection in detections:
                mice.append(MouseTracker([detection[2][0], detection[2][1]], dummyTag, frameName))
                dummyTag += 1
                error = True
            continue
        if len(detections) > len(mice):
            #Sort by the likelihood that it is a mouse, remove the least likely ones
            sortedDetections = sorted(detections, key=lambda l: l[1])
            while len(sortedDetections) >len(mice):
                sortedDetections.remove(sortedDetections[0])
            detections = sortedDetections
        cleanedDetections = []
        for detection in detections:
            #Update trackers by Euclidean distance
            x = detection[2][0]
            y = detection[2][1]
            nearestTracker = sorted(list(filter(lambda x: x.tag() not in updatedTags, mice)), key= lambda l: l.distanceFromPos((x,y)))[0]
            updatedTags.append(nearestTracker.tag())
            nearestTracker.updatePosition([x, y], frameName)
            detection = list(detection)
            detection[0] = nearestTracker.tag()
            cleanedDetections.append(detection)
        image = cvDrawBoxes(cleanedDetections, frame_resized)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        if len(detections) < len(mice) and error is False:
            #Mice have been lost this frame!
            error = True
            for tracker in filter(lambda x: x.tag() not in updatedTags, mice):
                if tracker.tag() > 9999:
                    #This is not a dummy tracker
                    lostTrackers.append(tracker)
                    mice.remove(tracker)
                    mice.append(MouseTracker(tracker.getPosition(), dummyTag, frameName))
                    dummyTag += 1
                else:
                    #This is a dummy tracker
                    mice.remove(tracker)
        elif error == True:
            #Check if we can match up a dummy mouse with a tag
            anonymousTrackers = list(filter(lambda x: x.tag() < 9999, mice))
            for line in RFID:
                ln = line.split(';')
                if "frameData/" + ln[2].strip('\n') == frameName:
                    for tracker in lostTrackers:
                        if int(ln[0]) == tracker.tag():
                            #Match!
                            position = list(int(item) for item in ln[1].strip('()\n').split(','))
                            nearestAnon = sorted(anonymousTrackers, key= lambda x: x.distanceFromPos(position))[0]
                            tracker.recordedPositions.extend(nearestAnon.recordedPositions)
                            lostTrackers.remove(tracker)
                            mice.remove(nearestAnon)
                            mice.append(tracker)
                    break
            if len(lostTrackers) == 1:
                #Only one lost mouse = only one possibility
                missingMouse = list(filter(lambda x: x.tag() < 9999, mice))[0]
                lostTrackers[0].recordedPositions.extend(missingMouse.recordedPositions)
                mice.append(lostTrackers[0])
                lostTrackers = []
                mice.remove(missingMouse)
                error = False
            if len(lostTrackers) == 0:
                error = False
        cv2.imshow('Demo', image)
        cv2.waitKey(3)
    out.release()
    mouseDict = {}
    for mouse in mouseTrackers:
        mouseDict.update({mouse.tag(): mouse.recordedPositions})
    with open("processed.json", "w") as outfile:
        json.dump(mouseDict, outfile, ensure_ascii=False)

if __name__ == "__main__":
    mouseTrackers = []
    tags = tuple(int(x.strip()) for x in input("Please input the mouse tags, separated by commas").split(','))
    print(tags)
    for tag in tags:
        mouseTrackers.append(MouseTracker([0,0], tag))
    RFIDResponses = []
    dataFileName = "RTS_test.txt"
    file = open(dataFileName, "r")
    RFIDResponses = file.readlines()
    YOLO("base_tracking", mouseTrackers, RFIDResponses)
