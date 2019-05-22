#Adapted from https://github.com/Ebonclaw/Mouse-Wearable-Tech---RFID-and-Localization-Grid-Computer-Vision-Enhancement
import datetime
import imutils
import time
import cv2
import RFID_Reader
import MouseTracker from MouseTracker
mouseAreaMin = 4500
mouseAreaMax = 9000 #???
#Main Loop
mouseTrackers = list()
bundleTrackers = list()
totMouseCount = 0
prevFreeMice = 0
prevBundledMice = 0
currContourCount = 0

# TODO: Find these numbers
readerMap = [
    [(0, 0), (0, 0), (0, 0), (0, 0), (0, 0)], #1-(1-5) [y-x]
    [(0, 0), (0, 0), (0, 0), (0, 0), (0, 0)], #2-(1-5) [y-x]
    [(0, 0), (0, 0), (0, 0), (0, 0), (0, 0)]  #3-(1-5) [y-x]
]

def cleanRFIDPosition(stringPos):
    stringPos = stringPos.split('-')
    position = (int(stringPos[1]) -1, int(stringPos[0]) -1) #Save in [y-x] form
    return readerMap[position[0]][position[1]]

def sortNearestTrackers(pos):
    """
    Sorts all non-bundled mice by their proximity to the given location.
    """
    remainingMice = list(filter(lambda x: not x.bundled(), mouseTrackers))
    return sorted(remainingMice, key= lambda x: x.distanceFromPos(pos))

def sortNearestBundles(pos):
    return sorted(bundleTrackers, key= lambda x: x["mice"][0].distanceFromPos(pos))

def setup():
    mice = RFID_Reader.scan()
    seenTags = []
    for (Tag, Position) in mice:
        if Tag not in seenTags:
            cleanedPos = cleanRFIDPosition(Position)
            mouseTrackers.append(MouseTracker(cleanedPos, Tag))
            totMouseCount += 1
    lastContourCount = totMouseCount


def process():
    camera = cv2.VideoCapture(0)
    time.sleep(0.25)
    firstFrame = None
    while True:
        #Grab the current frame
        (grabbed, frame) = camera.read()

        #If we could not get the frame, then we have reached the end of the stream.
        if not grabbed:
            break;
        #Convert to grayscale, resize, and blur the frame
        frame = imutils.resize(frame, width = 500)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21,21), 0)

        if firstFrame is None:
            # TODO: Add separate background image handling
            firstFrame = gray

        #Compute difference between current and first frame, fill in holes, and find contours
        frameDelta = cv2.absDiff(firstFrame, gray)
        thresh = cv2.threshold(frameDelta, 100, 255, cv2.THREAD_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        (_, rawContours, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

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
                continue
            elif cv2.contourArea(contour) < mouseAreaMax:
                #This is just one mouse
                moments = cv2.moments(contour)
                centerX = int(moments["m10"] / moments["m00"])
                centerY = int(moments["m01"] / moments["m00"])
                processedContours.append({'contour': contour, 'bundle' = False, 'center': (centerX, centerY)})
                currContourCount += 1
            else:
                #This is multiple mice
                moments = cv2.moments(contour)
                centerX = int(moments["m10"] / moments["m00"])
                centerY = int(moments["m01"] / moments["m00"])
                processedContours.append({'contour': contour, 'bundle' = True, 'center': (centerX, centerY)})
                bundleCount += 1
                currContourCount += 1

        freeMice = list(filter(lambda x: x.bundled(), mouseTrackers))
        if len(freeMice) ==prevFreeMice:
            #Simple. Update all mice with their new location
            for proContour in list(filter(lambda x: not x['bundle'], processedContours)):
                mouse = sortNearestTrackers(proContour["center"])[0]
                mouse.updatePosition(proContour["center"], False)
            for proContour in list(filter(lambda x: x['bundle'], processedContours)):
                bundle = sortNearestBundles(proContour["center"])
                bundle["position"] = proContour["center"]
                for mouse in bundle["mice"]:
                    mouse.updatePosition(proContour["center"], True)
            prevFreeMice = len(freeMice)
        elif len(freeMice) < prevFreeMice:
            #Some mice have joined new bundles.
            #For free mice, simple. Update all the remaining free mice.
            for proContour in list(filter(lambda x: not x['bundle'], processedContours)):
                mouse = sortNearestTrackers(proContour["center"])[0]
                mouse.updatePosition(proContour["center"], False)
            #Bundles: Form new bundles or make bigger ones
            # TODO: figure out this
        elif len(freeMice) > prevFreeMice:
            #Some mice have left their bundles.
            filteredContours = list(filter(lambda x: not x['bundle'], processedContours)
            for mouse in mouseTrackers:
                sortedContours = sorted(filteredContours, key=lambda x: mouse.distanceFromPos(x))
                mouse.updatePosition(sortedContours[i], False)
                processedContours.remove(sortedContours[i])
            

        # for proContour in list(filter(lambda x: x['bundle'], processedContours)):
        #     #First two will *always* be part of the bundle, otherwise the bundle would be merged with another.
        #     mice = []
        #     mice.append(sortNearestTrackers(proContour.center)[0])
        #     sortNearestTrackers(proContour.center)[0].updatePosition(proContour.center, True)
        #     mice.append(sortNearestTrackers(proContour.center)[1])
        #     sortNearestTrackers(proContour.center)[1].updatePosition(proContour.center, True)
        #     bundleTrackers.append({"position": proContour.center, "mice": mice})
        #     miceToBundle -=2
