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
import itertools
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
        vx = detection[3][0]
        vy = detection[3][1]
        xmin, ymin, xmax, ymax = convertBack(
            float(x), float(y), float(w), float(h))
        pt1 = (xmin, ymin)
        pt2 = (xmax, ymax)
        cv2.rectangle(img, pt1, pt2, (0, 255, 0), 1)
        cv2.circle(img, (int(x),int(y)), 5, [0,0,255])
        cv2.circle(img, (int(525*416/640),int(310*416/480)), 5, [0,255,0])
        cv2.circle(img, (int(103*416/640),int(170*416/480)), 5, [0,255,0])
        cv2.arrowedLine(img, (int(x - vx/2),int(y - vy/2)), (int(x + vx/2),int(y + vy/2)), [0,0,255])
        cv2.putText(img,
                    str(detection[0]) +
                    " [" + str(round(detection[1] * 100, 2)) + "]",
                    (pt1[0], pt1[1] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    [0, 255, 0], 2)
    return img


netMain = None
metaMain = None
altNames = None
maxSwapDistance = 50

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
    """
    Problem: Mice disappear and then reappear while others are unidentified. They should be instantly identified but are not.
    Essentially, need secondary handling before moving into "officially lost"
    So, we need "partially lost" and "officially lost".
    Partially lost mice can be found again as soon as the detection reappears.
    Officially lost mice need the RFID tags to verify them.
    """

    lostTrackers = []
    partialLostTrackers = []
    error = False
    dummyTag = 0
    while True:
        try:
            prev_time = time.time()
            frameName = "frameData/tracking_system" + trialName + str(frameCount) + ".png"
            frame_read = cv2.imread(frameName)
            print(frameCount)
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
        if len(detections) > miceNum:
            #Sort by the likelihood that it is a mouse, remove the least likely ones
            sortedDetections = sorted(detections, key=lambda l: l[1])
            while len(sortedDetections) >len(mice):
                sortedDetections.remove(sortedDetections[0])
            detections = sortedDetections
        cleanedDetections = []
        #Adjustment: First assign the recently known mice, then the recently lost.
        """
        Approach 1: Assign each detection to its nearest mouse.
        Problem: When a mouse reappears, the detection is closer to a mouse that has been tracked throughout than the mouse.
        Approach 2: Assign each mouse to its nearest detection.
        Problem: When a mouse disappears, it can be assigned to a detection even if it was supposed to be gone.
        Approach 3: Sort pairs of detection and mouse by distance. Assign in order, until we run out of detections or mice.
        """
        # TODO: Incorporate velocity
        pairs = itertools.product(list(filter(lambda x: x.lastFrameCount == frameCount -1, mice)), detections)
        pairs = sorted(pairs, key = lambda l: l[0].distanceFromPos((l[1][2][0], l[1][2][1])))
        lostPairs = itertools.product(list(filter(lambda x: x.lastFrameCount != frameCount -1, mice)), detections)
        lostPairs = sorted(lostPairs, key = lambda l: l[0].distanceFromPos((l[1][2][0], l[1][2][1])))
        for lpair in lostPairs:
            pairs.append(lpair)
        for pair in pairs:
            mouse = pair[0]
            detection = pair[1]
            x = detection[2][0]
            y = detection[2][1]
            if mouse.tag() not in updatedTags and detection in detections:
                updatedTags.append(mouse.tag())
                mouse.updatePosition([x, y], frameName, frameCount)
                updatedDetection = list(detection)
                updatedDetection[0] = mouse.tag()
                updatedDetection.append(mouse.velocity)
                detections.remove(detection)
                cleanedDetections.append(updatedDetection)
                if len(partialLostTrackers) == 1 and mouse.tag() == partialLostTrackers[0].tag():
                    partialLostTrackers = []
        image = cvDrawBoxes(cleanedDetections, frame_resized)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        if len(cleanedDetections) < miceNum:
            #Mice have been lost this frame!
            error = True
            for tracker in filter(lambda x: x.tag() not in updatedTags and x not in partialLostTrackers, mice):
                partialLostTrackers.append(tracker)
                nearest = sorted(list(filter(lambda x: x.tag() in updatedTags, mice)), key= lambda l: l.distanceFromPos(tracker.getPosition()))[0]
                if nearest.distanceFromPos(tracker.getPosition()) < maxSwapDistance and nearest not in partialLostTrackers:
                    partialLostTrackers.append(nearest)
        if len(partialLostTrackers) > 1:
            #Lost more than one? Then once it reappears we cannot know which it is.
            #We now require the RFID.
            print(list(map(lambda x: x.tag(), partialLostTrackers)))
            print(list(map(lambda x: x.tag(), mice)))
            for track in partialLostTrackers:
                if track.tag() > 99999:
                    #This is not a dummy tracker, we can find it again
                    lostTrackers.append(track)
                mice.remove(track)
                mice.append(MouseTracker(nearest.getPosition(), dummyTag, frameName))
                dummyTag += 1
            partialLostTrackers = []

        elif error == True and len(cleanedDetections) == miceNum:
            #Check if we can match up a dummy mouse with a tag
            anonymousTrackers = list(filter(lambda x: x.tag() < 99999, mice))
            for line in RFID:
                ln = line.split(';')
                if "frameData/" + ln[2].strip('\n') == frameName:
                    for tracker in lostTrackers:
                        if int(ln[0]) == tracker.tag():
                            #Match!
                            position = list(int(item) for item in ln[1].strip('()\n').split(','))
                            print(tracker.tag())
                            print(position)
                            position[0] *= 416/640
                            position[1] *= 416/480
                            nearestAnons = sorted(anonymousTrackers, key= lambda x: x.distanceFromPos(position))
                            if abs(nearestAnons[0].distanceFromPos(position) - nearestAnons[1].distanceFromPos(position)) < maxSwapDistance:
                                #We cannot be certain which one is over the reader
                                break
                            nearestAnon = nearestAnons[0]
                            print((nearestAnon.getPosition()[0]*640/416, nearestAnon.getPosition()[1]*480/416))
                            tracker.recordedPositions.extend(nearestAnon.recordedPositions)
                            tracker.updatePosition([nearestAnon.getPosition()[0], nearestAnon.getPosition()[1]], frameName)
                            lostTrackers.remove(tracker)
                            mice.remove(nearestAnon)
                            mice.append(tracker)
                    break
            if len(lostTrackers) == 1:
                print("one")
                #Only one lost mouse = only one possibility
                missingMouse = list(filter(lambda x: x.tag() < 99999, mice))[0]
                lostTrackers[0].updatePosition([missingMouse.getPosition()[0], missingMouse.getPosition()[1]], frameName)
                lostTrackers[0].recordedPositions.extend(missingMouse.recordedPositions)
                mice.append(lostTrackers[0])
                lostTrackers = []
                mice.remove(missingMouse)
                error = False
                print(list(map(lambda mouse: (mouse.tag(), mouse.getPosition()), mice)))
            if len(lostTrackers) == 0:
                error = False
        cv2.imshow('Demo', image)
        # input("next")
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
