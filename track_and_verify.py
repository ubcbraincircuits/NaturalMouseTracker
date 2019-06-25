#Adapted from https://github.com/Ebonclaw/Mouse-Wearable-Tech---RFID-and-Localization-Grid-Computer-Vision-Enhancement
import datetime
import imutils
import time
import argparse
from picamera.array import PiRGBArray
from picamera import PiCamera
import cv2
import numpy as np
import RFID_Reader
from time import sleep
from MouseTracker import MouseTracker
mouseAreaMin = 3500
mouseAreaMax = 15000 #avoid recognizing thicc mice as multiple mice
#Main Loop
mouseTrackers = list()
bundleTrackers = list()
prevBundledMice = 0
maxMovement = 30
fileName = "test.txt"
trialName = None

# TODO: Find these numbers
readerMap = [
    (103, 170), (177, 160), (274, 145), (390, 140), (475, 138), (542, 145), #1-(1-6) [y-x]
    (105, 253), (183, 250), (278, 248), (393, 237), (487, 235), (550, 230), #2-(1-6) [y-x]
    (118, 330), (190, 336), (288, 332), (401, 326), (496, 320), (556, 305)  #3-(1-5) [y-x]
]


def sortNearestFree(pos):
    """
    Sorts all non-bundled mice by their proximity to the given location.
    """
    remainingMice = list(filter(lambda x: not x.bundled, mouseTrackers))
    return sorted(remainingMice, key= lambda x: x.distanceFromPos(pos))

def sortNearest(pos):
    """
    Sorts all mice by their proximity to the given location.
    """
    return sorted(mouseTrackers, key= lambda x: x.distanceFromPos(pos))

def sortNearestBundles(pos):
    """
    Sorts all bundles by their proximity to the given location.
    """
    return sorted(bundleTrackers, key= lambda x: x["mice"][0].distanceFromPos(pos))

def setup():
    """
    Adds all mice that can be read by the reader to the trackers.
    """
    scan = True
    camera = PiCamera()
    camera.resolution = (640, 480)
    camera.framerate = 30
    camera.iso =600
    camera.exposure_mode="off"
    while scan:
        mice = RFID_Reader.scan()
        camera.capture("startup.png")
        for (tag, Position) in mice:
            mouseList = list(filter(lambda x: x.tag() == tag, mouseTrackers))
            if len(mouseList) is 0:
                mouseTrackers.append(MouseTracker(readerMap[Position], tag))
            else:
                mouseList[0].updatePosition(readerMap[Position], False)
        frame = cv2.imread("startup.png")
        for mouse in mouseTrackers:
            cv2.circle(frame, mouse.getPosition(), 5, [0,0,255])
        cv2.imshow("Startup", frame)
        cv2.waitKey()
        temp = input("RFID detects " + str(len(mouseTrackers)) + " mice in these positions. Is this accurate? (Y/N)")
        if temp.lower()[0] == 'y':
            scan = False
    file = open("startup.txt", 'w+')
    for mouse in mouseTrackers:
        log = str(mouse.tag()) + ';' + str(mouse.getPosition()) +';' + "startup.png" + '\n'
        file.write(log)
    file.close()
    camera.close()
    cv2.destroyAllWindows

def process():
    #camera = cv2.VideoCapture(0)
    camera = PiCamera()
    camera.resolution = (640, 480)
    camera.framerate = 30
    camera.iso =600
    camera.exposure_mode="off"
    rawCapture = PiRGBArray(camera, size=(640, 480))

    time.sleep(0.25)
    firstFrame = cv2.imread("ref.jpg")
    firstFrame = cv2.cvtColor(firstFrame, cv2.COLOR_BGR2GRAY)
    #firstFrame = cv2.GaussianBlur(firstFrame, (21,21), 0)
    startUpIterations = 100
    diffFrameCount = 0
    frameCount = 0
    needPulse = False
    for rawFrame in camera.capture_continuous(rawCapture, format = "bgr", use_video_port=True):
        try:
            frame = rawFrame.array
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            #gray = cv2.GaussianBlur(gray, (21,21), 0)

            if firstFrame is None:
                # TODO: Add separate background image handling
                firstFrame = gray

            #Compute difference between current and first frame, fill in holes, and find contours
            frameDelta = cv2.absdiff(firstFrame, gray)
            thresh = cv2.threshold(frameDelta, 60, 255, cv2.THRESH_BINARY)[1]

            (_, rawContours, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)



            processedContours = list()# clear stream to prepare for next frame
            rawFrame.truncate(0)

            bundleCount = 0
            #If any error occurs, scan the entire base and update mouse positions to RFID tags
            error = False
            updated = False
            for contour in rawContours:
                if cv2.contourArea(contour) < mouseAreaMin:
                    #Not a mouse :(
                    continue
                elif cv2.contourArea(contour) < mouseAreaMax:
                    #This is just one mouse
                    moments = cv2.moments(contour)
                    centerX = int(moments["m10"] / moments["m00"])
                    centerY = int(moments["m01"] / moments["m00"])
                    processedContours.append({'contour': contour, 'bundle': False, 'center': (centerX, centerY)})
                    rotated_box = cv2.minAreaRect(contour)
                    box = cv2.boxPoints(rotated_box)
                    box = np.int0(box)
                    #Green Box
                    cv2.drawContours(frame, [box], 0, (0, 255, 0),2)
                else:
                    #This is multiple mice
                    moments = cv2.moments(contour)
                    centerX = int(moments["m10"] / moments["m00"])
                    centerY = int(moments["m01"] / moments["m00"])
                    processedContours.append({'contour': contour, 'bundle': True, 'center': (centerX, centerY)})
                    rotated_box = cv2.minAreaRect(contour)
                    box = cv2.boxPoints(rotated_box)
                    box = np.int0(box)
                    #Red Box
                    cv2.drawContours(frame, [box], 0, (0, 0, 255),2)


            #processedContours = []

            prevFreeMice = list(filter(lambda x: not x.bundled, mouseTrackers))
            freeMouseContours = list(filter(lambda x: not x["bundle"], processedContours))
            bundleContours = list(filter(lambda x: x['bundle'], processedContours))
            if len(freeMouseContours) ==len(prevFreeMice) and needPulse:
                diffFrameCount += 1
                if diffFrameCount < 50:
                    #Give enough time for mice to be clearly separated
                    continue
                #A good base. Pulse nearby RFIDs to determine mouse positions.
                for contour in freeMouseContours:
                    #Update mouse with tag
                    x2 = contour["center"][0]
                    y2 = contour["center"][1]
                    nearestReaders = sorted(readerMap, key= lambda x: np.sqrt(((x[0]-x2)*(x[0]-x2) + (x[1]-y2)*(x[1]-y2))))
                    #print(nearestTagIndex)
                    #tag readers are upside down, fix later
                    tag = False
                    index = 0
                    index = readerMap.index(nearestReaders[0])
                    tag = RFID_Reader.readTag(17 - index)
                    if tag is False:
                        #Try again next time
                        error = True
                        break
                    tag = tag[0]
                    mouseList = list(filter(lambda x: x.tag() == tag, mouseTrackers))
                    if len(mouseList) is 0:
                        print("brand new")
                        print(list(map(lambda x: x.tag(), mouseTrackers)))
                        mouseTrackers.append(MouseTracker(readerMap[index], tag))
                        mouseList = list(filter(lambda x: x.tag() == tag, mouseTrackers))
                        mouseList[0].updatePosition(readerMap[index], False)
                    else:
                        mouseList[0].updatePosition(readerMap[index], False)

                for proContour in freeMouseContours:
                    mouse = sortNearestFree(proContour["center"])[0]
                    mouse.updatePosition(proContour["center"], False)
                needPulse = False
                updated = True

            elif len(freeMouseContours) < len(prevFreeMice):
                if len(bundleContours) == 0:
                    diffFrameCount = 0
                    #Mice have climbed on top of each other(probably)
                    needPulse = True
                # diffFrameCount += 1
                # print("bundle")
                # if diffFrameCount <= 5:
                #     #Ignore frames of mice briefly passing by each other.
                #     #Slows the algorithm significantly to process these.
                #     continue
                # #Some mice have joined new bundles.
                # #For free mice, simple. Update all the remaining free mice.
                # remainingMice = mouseTrackers.copy()
                # for proContour in freeMouseContours:
                #     try:
                #         mouse = sortNearestFree(proContour["center"])[0]
                #         mouse.updatePosition(proContour["center"], False)
                #         remainingMice.remove(mouse)
                #     except Exception as e:
                #         error = True
                # #Bundles: Form new bundles or make bigger ones
                # for proContour in bundleContours:
                #     nearestMice = sortNearest(proContour["center"])
                #     if(nearestMice[0].bundled and len(bundleTrackers) >0):
                #         #This is a previously created bundle! (Mice in a bundle have same position as bundle center)
                #         print(bundleTrackers)
                #         try:
                #             bundle = sortNearestBundles(proContour["center"])[0]
                #             bundle["position"] = proContour["center"]
                #             for mouse in bundle["mice"]:
                #                 mouse.updatePosition(proContour["center"], True)
                #         except Exception as e:
                #             error = True
                #         continue
                #     else:
                #         #New bundle!
                #         #First two will *always* be part of the bundle, otherwise the bundle would be merged with another.
                #         mice = []
                #         print(len(remainingMice))
                #         if len(remainingMice) < 2:
                #             error = True
                #             break
                #         mice.append(nearestMice[0])
                #         #This mouse *has* to be in remaining mice, otherwise it is both the closest
                #         #to a free contour and a bundle contour, which is impossible.
                #         try:
                #             remainingMice.remove(nearestMice[0])
                #             nearestMice[0].updatePosition(proContour["center"], True)
                #             mice.append(nearestMice[1])
                #             nearestMice[1].updatePosition(proContour["center"], True)
                #             remainingMice.remove(nearestMice[1])
                #             bundleTrackers.append({"position": proContour["center"], "mice": mice, "processed": False})
                #         except Exception as e:
                #             error = True
                # #Now any remaining mice must be in a bundle.
                # for mouse in remainingMice:
                #     try:
                #         if len(bundleContours) is 0 or len(bundleTrackers) is 0:
                #            #Mouse has left
                #             print("mouse left")
                #             mouseTrackers.remove(mouse)
                #             continue
                #         nearestBundle = min(bundleContours, key=lambda x: mouse.distanceFromPos(x["center"]))
                #         if mouse.distanceFromPos(nearestBundle["center"]) > maxMovement:
                #             #Mouse has left (or we lost it)
                #             print("mouse left")
                #             mouseTrackers.remove(mouse)
                #             continue
                #         mouse.updatePosition(nearestBundle["center"], True)
                #         bundle = sortNearestBundles(proContour["center"])[0]
                #         bundle["mice"].append(mouse)
                #     except Exception as e:
                #         error = true
            elif len(freeMouseContours) > len(prevFreeMice):
                pass
                # diffFrameCount += 1
                # if diffFrameCount <= 5:
                #     continue
                # print("separate")
                # #Some mice have left their bundles, or new mice have arrived.
                # for mouse in prevFreeMice:
                #     try:
                #         nearestContour = sorted(freeMouseContours, key=lambda x: mouse.distanceFromPos(x["center"]))[0]
                #         mouse.updatePosition(nearestContour["center"], False)
                #         processedContours.remove(nearestContour)
                #         freeMouseContours.remove(nearestContour)
                #     except Exception as e:
                #         error = True
                # for contour in freeMouseContours:
                #     #Update mouse with tag
                #     x2 = contour["center"][0]
                #     y2 = contour["center"][1]
                #     nearestReaders = sorted(readerMap, key= lambda x: np.sqrt(((x[0]-x2)*(x[0]-x2) + (x[1]-y2)*(x[1]-y2))))
                #     #print(nearestTagIndex)
                #     #tag readers are upside down, fix later
                #     tag = False
                #     index = 0
                #     num = 0
                #     count = 0
                #     while tag is False:
                #         index = readerMap.index(nearestReaders[num])
                #         tag = RFID_Reader.readTag(17 - index)
                #         count+= 1
                #         if count > 3:
                #             break
                #     if tag is False:
                #         #Try again next time
                #         error = True
                #         break
                #     tag = tag[0]
                #     mouseList = list(filter(lambda x: x.tag() == tag, mouseTrackers))
                #     if len(mouseList) is 0:
                #         print("brand new")
                #         print(list(map(lambda x: x.tag(), mouseTrackers)))
                #         mouseTrackers.append(MouseTracker(readerMap[index], tag))
                #         mouseList = list(filter(lambda x: x.tag() == tag, mouseTrackers))
                #         mouseList[0].updatePosition(readerMap[index], False)
                #     else:
                #         mouseList[0].updatePosition(readerMap[index], False)
                #     #Update remaining bundles
                #     for proContour in bundleContours:
                #         bundle = sortNearestBundles(proContour["center"])[0]
                #         bundle["position"] = proContour["center"]
                #         bundle["processed"] = True
                #         for mouse in bundle["mice"]:
                #             if mouse.bundled:
                #                 mouse.updatePosition(proContour["center"], True)
                #             else:
                #                 bundle["mice"].remove(mouse)
                #     #Remove any unprocessed bundles (these are now empty)
                #     for bundle in bundleTrackers:
                #         if bundle["processed"]:
                #                 bundle["processed"] = False
                #         else:
                #             bundleTrackers.remove(bundle)
            if error:
                #Not a good set of tags
                continue
                #Refresh from RFID
                #setup()
            frameName = "tracking_system" + trialName + str(frameCount) + ".png"
            frameCount += 1
            if updated:
                for mouse in mouseTrackers:
                    pos = mouse.getPosition()
                    cv2.putText(frame, str(mouse.tag()), pos, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                    file = open(fileName, 'a')
                    log = str(mouse.tag()) + ';' + str(pos) +';' + frameName + '\n'
                    file.write(log)
                    file.close()
            cv2.imshow("Mouse Tracking", frame)
            key = cv2.waitKey(1)& 0xFF
            #cv2.imwrite("frameData/" + frameName, gray)


            if key==ord('q'):
                break
        except KeyboardInterrupt:
            break





if __name__=="__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-t", "--text", help="path to the text file")
    ap.add_argument("-n", "--name", default ="base_tracking", help="trial name")
    args = vars(ap.parse_args())

    if args.get("text", None) is not None:
        fileName = args.get('text')
        open(fileName, "w+").close()
    trialName = args.get("name")
    print('hello')
    setup()
    process()

        # for proContour in list(filter(lambda x: x['bundle'], processedContours)):
        #     #First two will *always* be part of the bundle, otherwise the bundle would be merged with another.
        #     mice = []
        #     mice.append(sortNearestFree(proContour.center)[0])
        #     sortNearestFree(proContour.center)[0].updatePosition(proContour.center, True)
        #     mice.append(sortNearestFree(proContour.center)[1])
        #     sortNearestFree(proContour.center)[1].updatePosition(proContour.center, True)
        #     bundleTrackers.append({"position": proContour.center, "mice": mice})
        #     miceToBundle -=2
