"""
Final processing file. Copy into the darknet folder to run.
"""

from ctypes import *
import math
import random
import os
import cv2
import numpy as np
import time
import darknet

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
                    detection[0].decode() +
                    " [" + str(round(detection[1] * 100, 2)) + "]",
                    (pt1[0], pt1[1] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    [0, 255, 0], 2)
    return img


netMain = None
metaMain = None
altNames = None


def YOLO(trialName, mice, RFID):

    global metaMain, netMain, altNames
    configPath = "./yolov3-tiny-obj.cfg"
    weightPath = "./yolov3-tiny-obj_final.weights"
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
    while True:
        prev_time = time.time()
        frameName = "tracking_system" + trialName + str(frameCount) + ".png"
        frame_read = cv2.imread(frameName)
        frameCount += 1
        frame_rgb = cv2.cvtColor(frame_read, cv2.COLOR_BGR2RGB)
        frame_resized = cv2.resize(frame_rgb,
                                   (darknet.network_width(netMain),
                                    darknet.network_height(netMain)),
                                   interpolation=cv2.INTER_LINEAR)

        darknet.copy_image_from_bytes(darknet_image,frame_resized.tobytes())

        detections = darknet.detect_image(netMain, metaMain, darknet_image, thresh=0.25)
        image = cvDrawBoxes(detections, frame_resized)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        # print(1/(time.time()-prev_time))
        updatedTrackers = []
        for detection in detections:

            x = detection[2][0]
            y = detection[2][1]
            nearestTracker = sorted(list(filter(lambda x: x not in updatedTrackers, mice)), key= lambda x: x.distanceFromPos((x,y)))[0]
            updatedTrackers.append(nearestTracker)
            nearestTracker.updatePosition(position)
        if len(detections) < len(mice):
            error = True
            for tracker in filter(lambda x: x not in updatedTrackers, mice):
                lostTrackers.append(tracker)
                mice.remove(tracker)
                mice.append(MouseTracker(tracker.getPosition(), None))
        if error == True:
            anonymousTrackers = list(filter(lambda x: x.tag() is None, mice))
            for line in RFID:
                ln = line.split(';')
                if ln[2] is frameName:
                    for tracker in lostTrackers:
                        if ln[0] is tracker.tag():
                            nearestTracker = sorted(anonymousTrackers, key= lambda x: x.distanceFromPos((item for item in ln[1].strip('()\n').split(','))))[0]
                            tracker.recordedPositions.extend(nearestTracker.recordedPositions)
                            lostTrackers.remove(tracker)
                            anonymousTrackers.remove(nearestTracker)
            if len(lostTrackers) == 0:
                error = False
        cv2.imshow('Demo', image)
        cv2.waitKey(3)
    cap.release()
    out.release()

if __name__ == "__main__":
    mouseTrackers = []
    #temp
    mouseTrackers.append(MouseTracker((341, 266), 1))
    mouseTrackers.append(MouseTracker((210, 166), 2))
    mouseTrackers.append(MouseTracker((172, 82), 3))
    fileName = "test.txt"
    file = open(fileName, "r")
    RFIDResponses = file.readlines()
    for response in RFIDResponses:
        ln = line.split(";")
        if ln[2] is not "None":
            mouseTrackers.append((item for item in ln[1].strip('()\n').split(',')), int(ln[0]))
            break
    YOLO("trial", mouseTrackers, RFIDResponses)
