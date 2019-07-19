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
from munkres import Munkres
from shutil import copyfile
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
        cv2.circle(img, (int(103*416/640),int(120*416/480)), 5, [0,255,0])
        cv2.circle(img, (int(x),int(y)), maxSwapDistance, [255,0,0])
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
maxSwapDistance = 40
minSwapVelocity = 3

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
    frameCount = 1
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
    badFrameCount = 0
    RFIDIndex = -1
    pairFinder = Munkres()
    while True:
        try:
            validationFrame = False
            prev_time = time.time()
            frameName = "frameData/tracking_system" + trialName + str(frameCount) + ".png"
            if "frameData/" + RFID[RFIDIndex + 1].split(';')[2].strip('\n') == frameName:
                validationFrame = True
                RFIDIndex += 1
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

        detections = darknet.detect_image(netMain, metaMain, darknet_image, thresh=0.5)

        # print(1/(time.time()-prev_time))
        updatedTags = []
        if frameCount == 2 or (len(mice) == 0 and len(detections) == miceNum):
            for mouse in mouseTrackers:
                lostTrackers.append(mouse)
            mice = []
            for detection in detections:
                mice.append(MouseTracker([detection[2][0], detection[2][1]], dummyTag, frameName))
                dummyTag += 1
                error = True
            continue
        elif len(mice) == 0:
            #Problem starting up
            continue
        if len(detections) > miceNum:
            #Sort by the likelihood that it is a mouse, remove the least likely ones
            sortedDetections = sorted(detections, key=lambda l: l[1])
            while len(sortedDetections) > miceNum:
                sortedDetections.remove(sortedDetections[0])
            detections = sortedDetections
        cleanedDetections = []
        if len(detections) < miceNum:
            #Temp
            # print("bad frame")
            if badFrameCount < 1:
                badFrameCount += 1
                continue
        if len(detections) == miceNum:
            badFrameCount = 0
        #Adjustment: First assign the recently known mice, then the recently lost.
        """
        Approach 1: Assign each detection to its nearest mouse.
        Problem: When a mouse reappears, the detection is closer to a mouse that has been tracked throughout than the mouse.
        Approach 2: Assign each mouse to its nearest detection.
        Problem: When a mouse disappears, it can be assigned to a detection even if it was supposed to be gone.
        Approach 3: Sort pairs of detection and mouse by distance. Assign in order, until we run out of detections or mice.
        Problem: Some inaccuracies. Adding lost pairs after the fact caused issues.
        Approach 4: Munkres' Algorithm
        """
        # TODO: Incorporate velocity
        # pairs = itertools.product(list(filter(lambda x: x.lastFrameCount == frameCount -1, mice)), detections)
        pairs = itertools.product(mice, detections)
        pairs = sorted(pairs, key = lambda l: l[0].distanceFromPos((l[1][2][0], l[1][2][1])))
        matrix = []
        for i in range(0, len(mice)):
            row = []
            for x in range (0, len(mice)):
                if x >= len(detections):
                    row.append(0)
                else:
                    d = detections[x]
                    row.append(mice[i].distanceFromPos((d[2][0], d[2][1])))
            matrix.append(row)

        pairIndices = pairFinder.compute(matrix)
        # print(list(map(lambda x: x.tag(), mice)))
        # print(pairIndices)
        # lostPairs = itertools.product(list(filter(lambda x: x.lastFrameCount != frameCount -1, mice)), detections)
        # lostPairs = sorted(lostPairs, key = lambda l: l[0].distanceFromPos((l[1][2][0], l[1][2][1])))
        # for lpair in lostPairs:
        #     pairs.append(lpair)
        for row, column in pairIndices:
            if column >= len(detections):
                continue
            mouse = mice[row]
            detection = detections[column]
            x = detection[2][0]
            y = detection[2][1]
            if mouse.tag() not in updatedTags and detection in detections:
                updatedTags.append(mouse.tag())
                mouse.updatePosition([x, y], frameName, frameCount)
                updatedDetection = list(detection)
                updatedDetection[0] = mouse.tag()
                updatedDetection.append(mouse.velocity)
                cleanedDetections.append(updatedDetection)
                if len(partialLostTrackers) == 1 and mouse.tag() == partialLostTrackers[0].tag():
                    partialLostTrackers = []
        image = cvDrawBoxes(cleanedDetections, frame_resized)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        cv2.imshow('Demo', image)
        cv2.waitKey(3)
        if len(cleanedDetections) < miceNum:
            #Mice have been lost this frame!
            error = True
            for tracker in filter(lambda x: x.tag() not in updatedTags and x not in partialLostTrackers, mice):
                partialLostTrackers.append(tracker)
                nearest = sorted(list(filter(lambda x: x.tag() in updatedTags, mice)), key= lambda l: l.distanceFromPos(tracker.getPosition()))
                if len(nearest) > 0:
                    nearest = nearest[0]
                else:
                    break
                if nearest.distanceFromPos(tracker.getPosition()) < maxSwapDistance and nearest not in partialLostTrackers:
                    #This checks if there is a mouse nearby to the one that just disappeared.
                    #We also check if this mouse has an abrupt change in velocity
                    #This indicates that we may get identity swaps.
                    print(nearest.velocity)
                    print(tracker.tag(), tracker.getPosition())
                    print(nearest.tag(), nearest.getPosition())
                    if (nearest.velocity[0]**2 + nearest.velocity[1]**2) < minSwapVelocity**2:
                        continue
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
                try:
                    mice.remove(track)
                    mice.append(MouseTracker(track.getPosition(), dummyTag, frameName))
                except ValueError:
                    #for safety idk
                    pass
                dummyTag += 1
            partialLostTrackers = []

        if error == True:
            #Check if we can match up a dummy mouse with a tag
            if validationFrame:
                ln = RFID[RFIDIndex].split(';')
                position = list(int(item) for item in ln[1].strip('()\n').split(','))
                for tracker in lostTrackers:
                    if int(ln[0]) == tracker.tag():
                        foundTracker = True
                        #Match!
                        print(tracker.tag())
                        print(position)
                        position[0] *= 416/640
                        position[1] *= 416/480
                        nearestMice = sorted(mice, key= lambda x: x.distanceFromPos(position))
                        print(list(map(lambda x: x.tag(), filter(lambda x: x.tag() < 99999, mice))))
                        if abs(nearestMice[0].distanceFromPos(position) - nearestMice[1].distanceFromPos(position)) < 30:
                            #We cannot be certain which one is over the reader
                            break
                        if nearestMice[0].tag() < 99999:
                            #Anonymouse :)
                            nearestAnon = nearestMice[0]
                            print((nearestAnon.getPosition()[0]*640/416, nearestAnon.getPosition()[1]*480/416))
                            tracker.updatePositions(nearestAnon.recordedPositions)
                            lostTrackers.remove(tracker)
                            mice.remove(nearestAnon)
                            mice.append(tracker)
                        else:
                            #There was an identity swap earlier. Correct for it
                            badMouse = nearestMice[0]
                            incorrectPositions = badMouse.trimPositions()
                            tracker.updatePositions(incorrectPositions)
                            lostTrackers.remove(tracker)
                            lostTrackers.append(badMouse)
                            mice.remove(badMouse)
                            mice.append(tracker)
            if len(lostTrackers) > 1:
                av_x = 0.0
                av_y = 0.0
                for mouse in filter(lambda x: x.tag() < 99999, mice):
                     av_x += mouse.getPosition()[0]
                     av_y += mouse.getPosition()[1]
                av_x /= len(lostTrackers)
                av_y /= len(lostTrackers)
                allMiceClose = True
                for mouse in filter(lambda x: x.tag() < 99999, mice):
                    if mouse.distanceFromPos((av_x, av_y)) > 100:
                        #Cannot approximate position as the average
                        allMiceClose = False
                if allMiceClose:
                    for lostMouse in lostTrackers:
                        #In order to not lose all data, save approximate location
                        #if mice are close enough together. (e.g. sleeping in corner)
                        lostMouse.updatePosition([av_x, av_y], frameName)

            if len(lostTrackers) == 1:
                print("one")
                #Only one lost mouse = only one possibility
                print(list(map(lambda x: x.tag(), filter(lambda x: x.tag() < 99999, mice))))
                missingMouse = list(filter(lambda x: x.tag() < 99999, mice))[0]
                lostTrackers[0].updatePositions(missingMouse.recordedPositions)
                mice.append(lostTrackers[0])
                lostTrackers = []
                mice.remove(missingMouse)
                error = False
                print(list(map(lambda mouse: (mouse.tag(), mouse.getPosition()), mice)))

            if len(lostTrackers) == 0:
                error = False
        elif validationFrame:
            ln = RFID[RFIDIndex].split(';')
            readerPos = list(int(item) for item in ln[1].strip('()\n').split(','))
            readerPos[0] *= 416/640
            readerPos[1] *= 416/480
            nearestMice = sorted(mice, key= lambda x: x.distanceFromPos(readerPos))
            if abs(nearestMice[0].distanceFromPos(readerPos) - nearestMice[1].distanceFromPos(readerPos)) > 30:
                if nearestMice[0].tag() != int(ln[0]):
                    #An identity swap has occured. Remove the frames up to the last validation point.
                    otherMouse = list(filter(lambda x: x.tag() == int(ln[0]), mice))[0]
                    currentPosition = [otherMouse.getPosition()[0], otherMouse.getPosition()[1]]
                    otherMouse.trimPositions()
                    nearestMice[0].trimPositions()
                    otherMouse.updatePosition(readerPos)
                    nearestMice[0].updatePosition(currentPosition)
                else:
                    nearestMice[0].validate()



        # input("next")
    out.release()
    mouseDict = {}
    for mouse in mouseTrackers:
        mouseDict.update({mouse.tag(): mouse.recordedPositions})
        print(mouse.tag(), str(len(mouse.recordedPositions)/frameCount*100) + "% Covered")
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
    YOLO("verify", mouseTrackers, RFIDResponses)
