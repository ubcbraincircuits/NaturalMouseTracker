"""
Tracking file. Copy into the darknet folder for processing.
"""

import numpy as np
from collections import deque
class MouseTracker:

    def __init__(self, startCoord, id, frame = ''):
        self.currCoord = startCoord
        self.positionQueue = deque(maxlen=5)
        if startCoord != [0,0]:
            startCoord.append(frame)
            self.positionQueue.append(startCoord)
            self.recordedPositions = [startCoord]
        else:
            self.recordedPositions = []
        self.id = id
        self.bundled = False
        self.lastFrameCount = 0
        self.velocity = (0,0)

    def updatePosition(self, coordinate, frame='', frameCount = 0):
        self.currCoord = coordinate
        coordinate.append(frame)
        self.lastFrameCount = frameCount
        self.recordedPositions.append(coordinate)
        self.positionQueue.append(coordinate)
        self.velocity = ((coordinate[0] - self.positionQueue[0][0]), (coordinate[1] - self.positionQueue[0][1]))

    def getPosition(self):
        return self.currCoord

    def distanceFromPos(self, pos):
        x1 = self.currCoord[0]
        y1 = self.currCoord[1]
        x2 = pos[0]
        y2 = pos[1]
        return np.sqrt((x1-x2)*(x1-x2) + (y1-y2)*(y1-y2))

    def bundled(self):
        return self.bundled

    def tag(self):
        return self.id

"""
    We have 5 mice
    at positions (1,1), (232, 222), (77, 11), (2, 10), (72, 8)
    thus mouseTrackers: {
        mouse0: (1,1),
        mouse1: (232, 222),
        mouse2: (77, 11),
        mouse3: (2, 10),
        mouse4: (72, 8)
    }
    now mouse 0 and 3 merge, and 2 and 4 merge.
    thus we have one bundle at (2, 3), and one bundle at (73, 10)
    So we count 3 contours, 2 are bundles.
    We take the bundles first.
    There are 2 mice near the first bundle, and 4 mice must be in a bundle.
    Therefore, mouse0 and mouse4 are placed in a bundle.
"""
