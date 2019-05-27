#Adapted from https://github.com/Ebonclaw/Mouse-Wearable-Tech---RFID-and-Localization-Grid-Computer-Vision-Enhancement
import datetime
import imutils
import time
from picamera.array import PiRGBArray
from picamera import PiCamera
import cv2
import numpy as np
import RFID_Reader
from MouseTracker import MouseTracker
mouseAreaMin = 4500
mouseAreaMax = 15000 #avoid recognizing thicc mice as multiple mice
#Main Loop
mouseTrackers = list()
bundleTrackers = list()
prevBundledMice = 0
maxMovement = 30
fileName = "test.txt"

# TODO: Find these numbers
readerMap = [
    (75, 115), (173, 113), (283, 113), (395, 118), (496, 127), (587, 136), #1-(1-6) [y-x]
    (75, 215), (174, 213), (283, 220), (390, 220), (495, 225), (585, 227), #2-(1-6) [y-x]
    (78, 315), (175, 316), (283, 320), (390, 320), (487, 325), (577, 320)  #3-(1-5) [y-x]
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
    time.sleep(5)
    print("setup start")
    mice = RFID_Reader.scan()
    print("done scan")
    seenTags = []
    open(fileName, "w+").close()
    for (Tag, Position) in mice:
        if Tag not in seenTags:
            cleanedPos = readerMap[Position]
            mouseTrackers.append(MouseTracker(cleanedPos, Tag))


def process():
    #camera = cv2.VideoCapture(0)
    camera = PiCamera()
    camera.resolution = (640, 480)
    camera.framerate = 32
    rawCapture = PiRGBArray(camera, size=(640, 480))

    time.sleep(0.25)
    firstFrame = cv2.imread("ref.jpg")
    firstFrame = cv2.cvtColor(firstFrame, cv2.COLOR_BGR2GRAY)
    firstFrame = cv2.GaussianBlur(firstFrame, (21,21), 0)
    bgsub = cv2.bgsegm.createBackgroundSubtractorGMG()
    startUpIterations = 100
    frameCount = 0
    for rawFrame in camera.capture_continuous(rawCapture, format = "bgr", use_video_port=True):
        try:
            #Grab the current frame
            # print("got the frame")
            # (grabbed, frame) = camera.read()
            #
            # #If we could not get the frame, then we have reached the end of the stream.
            # if not grabbed:
            #     break;
            #Convert to grayscale, resize, and blur the frame
            #frame = imutils.resize(frame, width = 500)
            frame = rawFrame.array
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21,21), 0)

            if firstFrame is None:
                # TODO: Add separate background image handling
                firstFrame = gray

            #Compute difference between current and first frame, fill in holes, and find contours
            frameDelta = cv2.absdiff(firstFrame, gray)
            thresh = cv2.threshold(frameDelta, 100, 255, cv2.THRESH_BINARY)[1]
            thresh = cv2.dilate(thresh, None, iterations=2)
            
            # thresh = bgsub.apply(frame, learningRate = 0.2)
          
            (rawContours, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            processedContours = list()
            """
            Capstone process:
                If area of contour is bigger than min, it must be at least one mouse.
                If it is less than two mice, it is one.
                If it is greater than minimum for two mice and less than minimum for three, it is two mice.
                If it is greater than min. for three, it is three mice.
                Otherwise, it is not a mouse (something smaller has moved: dust, food, etc.)
                If any mice have merged, record this.
                Then, for all contours that are mice, first check for all single mice.
                Single mice are simple. Find their center and store it in the tracker.
                Merged mice: very complex.
            How can we improve this?
                Idea #1: Simply, don't handle the merge case. At the point the mice merge,
                we treat them as one "bundle" of mice. *If* we can assume the number of mice in the cage is
                constant, then this is simple. For situations such as AHF, we can potentially designate
                a region of the image as an "entrance/exit zone", where we can decrement and increment a
                global mouse counter.
                With this, we may not have to have set sizes for the individual sets of mice,
                which strikes me as a poor idea regardless.
                A maximum size for a mouse should suffice.
                Then, whenever the contour count decrements, we check the distance between
                the bundle and the last known position of the vanished mouse. If it is close enough,
                assume the mouse has joined the bundle. Otherwise, assume the mouse has left the cage.
                Whenever a mouse leaves the bundle (i.e. a new contour appears), verify which it is
                with the RFID system.
                Possible problems:
                    - A mouse could leave the cage at the same time as another leaves the bundle.
                      This system could potentially not notice this.
                    - The size of mouse bundles could become too large to get meaningful data out of.
                    - Multiple bundles forming nearby each other?
            """
            bundleCount = 0
            for contour in rawContours:
                if cv2.contourArea(contour) < mouseAreaMin:
                    print("no mouse")
                    #Not a mouse :(
                    continue
                elif cv2.contourArea(contour) < mouseAreaMax:
                    print("hey it a mouse yo")
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
                    print("o shit so many mice")
                    moments = cv2.moments(contour)
                    centerX = int(moments["m10"] / moments["m00"])
                    centerY = int(moments["m01"] / moments["m00"])
                    processedContours.append({'contour': contour, 'bundle': True, 'center': (centerX, centerY)})
                    rotated_box = cv2.minAreaRect(contour)
                    box = cv2.boxPoints(rotated_box)
                    box = np.int0(box)
                    #Red Box
                    cv2.drawContours(frame, [box], 0, (0, 0, 255),2)


            cv2.imshow("Mouse Tracking", thresh)
            key = cv2.waitKey(1)& 0xFF
            # clear stream to prepare for next frame
            rawFrame.truncate(0)
            prevFreeMice = list(filter(lambda x: not x.bundled, mouseTrackers))
            freeMouseContours = list(filter(lambda x: not x["bundle"], processedContours))
            bundleContours = list(filter(lambda x: x['bundle'], processedContours))
            if len(freeMouseContours) ==len(prevFreeMice):
                #Simple. Update all mice with their new location
                for proContour in freeMouseContours:
                    mouse = sortNearestFree(proContour["center"])[0]
                    mouse.updatePosition(proContour["center"], False)
                for proContour in bundleContours:
                    if len(bundleTrackers) == 0:
                        #Handle it next time
                        break
                    bundle = sortNearestBundles(proContour["center"])[0]
                    bundle["position"] = proContour["center"]
                    for mouse in bundle["mice"]:
                        mouse.updatePosition(proContour["center"], True)
            elif len(freeMouseContours) < len(prevFreeMice):
                #Some mice have joined new bundles.
                #For free mice, simple. Update all the remaining free mice.
                remainingMice = mouseTrackers.copy()
                for proContour in freeMouseContours:
                    mouse = sortNearestFree(proContour["center"])[0]
                    mouse.updatePosition(proContour["center"], False)
                    remainingMice.remove(mouse)
                #Bundles: Form new bundles or make bigger ones
                for proContour in bundleContours:
                    nearestMice = sortNearest(proContour["center"])
                    if(nearestMice[0].bundled and len(bundleTrackers) >0):
                        #This is a previously created bundle! (Mice in a bundle have same position as bundle center)
                        print(bundleTrackers)
                        if len(bundleTrackers)==0:
                            break
                        bundle = sortNearestBundles(proContour["center"])[0]
                        bundle["position"] = proContour["center"]
                        for mouse in bundle["mice"]:
                            mouse.updatePosition(proContour["center"], True)
                        continue
                    else:
                        #New bundle!
                        #First two will *always* be part of the bundle, otherwise the bundle would be merged with another.
                        mice = []
                        print(len(remainingMice))
                        if len(remainingMice) < 2:
                            break
                        mice.append(nearestMice[0])
                        #This mouse *has* to be in remaining mice, otherwise it is both the closest
                        #to a free contour and a bundle contour, which is impossible.
                        remainingMice.remove(nearestMice[0])
                        nearestMice[0].updatePosition(proContour["center"], True)
                        mice.append(nearestMice[1])
                        nearestMice[1].updatePosition(proContour["center"], True)
                        remainingMice.remove(nearestMice[1])
                        bundleTrackers.append({"position": proContour["center"], "mice": mice, "processed": False})
                #Now any remaining mice must be in a bundle.
                for mouse in remainingMice:
                    if len(bundleContours) is 0 or len(bundleTrackers) is 0:
                       #Mouse has left
                        mouseTrackers.remove(mouse)
                        continue
                    nearestBundle = min(bundleContours, key=lambda x: mouse.distanceFromPos(x["center"]))
                    if mouse.distanceFromPos(nearestBundle["center"]) > maxMovement:
                        #Mouse has left (or we lost it)
                        mouseTrackers.remove(mouse)
                        continue
                    mouse.updatePosition(nearestBundle["center"], True)
                    bundle = sortNearestBundles(proContour["center"])[0]
                    bundle["mice"].append(mouse)
            elif len(freeMouseContours) > len(prevFreeMice):
                #Some mice have left their bundles, or new mice have arrived.
                for mouse in prevFreeMice:
                    nearestContour = sorted(freeMouseContours, key=lambda x: mouse.distanceFromPos(x["center"]))[0]
                    mouse.updatePosition(nearestContour["center"], False)
                    processedContours.remove(nearestContour)
                    freeMouseContours.remove(nearestContour)
                for contour in freeMouseContours:
                    #Update mouse with tag
                    x2 = contour["center"][0]
                    y2 = contour["center"][1]
                    nearestReaders = sorted(readerMap, key= lambda x: np.sqrt(((x[0]-x2)*(x[0]-x2) + (x[1]-y2)*(x[1]-y2))))
                    #print(nearestTagIndex)
                    #tag readers are upside down, fix later
                    tag = False
                    index = 0
                    num = 0
                    count = 0
                    while tag is False:
                        index = readerMap.index(nearestReaders[num])
                        tag = RFID_Reader.readTag(17 - index)
                        count+= 1
                        num = count%3
                        if count > 7:
                            break
                    if tag is False:
                        #Try again next time
                        break
                    tag = tag[0]
                    mouseList = list(filter(lambda x: x.tag() is tag, mouseTrackers))
                    if len(mouseList) is 0:
                        mouseTrackers.append(MouseTracker(index, tag))
                        mouseList = list(filter(lambda x: x.tag() is tag, mouseTrackers))
                        mouseList[0].updatePosition(readerMap[index], False)
                    else:
                        mouseList[0].updatePosition(readerMap[index], False)
                    #Update remaining bundles
                    for proContour in bundleContours:
                        bundle = sortNearestBundles(proContour["center"])[0]
                        bundle["position"] = proContour["center"]
                        bundle["processed"] = True
                        for mouse in bundle["mice"]:
                            if mouse.bundled:
                                mouse.updatePosition(proContour["center"], True)
                            else:
                                bundle["mice"].remove(mouse)
                    #Remove any unprocessed bundles (these are now empty)
                    for bundle in bundleTrackers:
                        if bundle["processed"]:
                            bundle["processed"] = False
                        else:
                            bundleTrackers.remove(bundle)
            for mouse in mouseTrackers:
                pos = mouse.getPosition()
                file = open(fileName, 'a')
                log = str('%.4f' %time.time()) + ';' + '[' + str(mouse.tag()) + ']' + ';' + str(pos) + '\n'
                file.write(log)
                file.close()
                
            if key==ord('q'):
                break
        except KeyboardInterrupt:
            break
        
    


        
if __name__=="__main__":
    print('hello')
    #setup()
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
