"""
Tracking file. Copy into the darknet folder for processing.
"""

import numpy as np
from collections import deque
from filterpy.kalman import KalmanFilter
import cv2

class MouseTracker:
    totalAllowedVis = 8

    def __init__(self, startCoord, id, frame = '', frameCount = 0, width = 0, height = 0):
        self.currCoord = startCoord
        self.positionQueue = deque(maxlen=2)
        if startCoord != [0,0]:
            startCoord.append(frame)
            startCoord.append(frameCount)
            startCoord.append(width)
            startCoord.append(height)
            self.positionQueue.append(startCoord)
            self.recordedPositions = [startCoord]
        else:
            self.recordedPositions = []
        self.visualTracker = None
        self.visualCount = 0
        self.canDoVisual = True
        self.validatedIndex = 0
        self.id = id
        self.filter = KalmanFilter
        self.lastFrameCount = 0
        self.velocity = (0,0)

    def updatePosition(self, coordinate, frame='', frameCount = 0, width = 0, height = 0):
        self.currCoord = coordinate
        coordinate.append(frame)
        coordinate.append(frameCount)
        coordinate.append(width)
        coordinate.append(height)
        self.lastFrameCount = frameCount
        self.recordedPositions.append(coordinate)
        self.positionQueue.append(coordinate)
        """
        TODO: Kalman Filter.
        Initial state covariance to be determined - depends on mouse speed and
        other factors.
        From mouse movement data, state covariance matrix P:
        x      [[350000 0       0       0       0       0       ]
        x_dot   [0      7000    0       0       0       0       ]
        x_ddot  [0      0       2700000 0       0       0       ]
        y       [0      0       0       350000  0       0       ]
        y_dot   [0      0       0       0       16470   0       ]
        y_ddot  [0      0       0       0       0       2000000 ]]

        Should use a constant acceleration model, so state transition function
        should be F = [ [1  del_t   1/2 del_t^2 0   0       0]
                    [0  1       del_t       0   0       0]
                    [0  0       1           0   0       0]
                    [0  0       0           1   del_t   1/2 del_t^2]
                    [0  0       0           0   1       del_t]
                    [0  0       0           0   0       1] ]

        Process Noise - use general white noise, call variance q
        q = 5000

        Measurement function - we only measure position, so it is simply
        H = [[1 0 0 0 0 0]
             [0 0 0 1 0 0]]
        Measurement noise matrix:
        Variances determined by experimental data:
        R = [[330 52  ]
             [52   231]]

        Use this to update velocity, which will be used to provide a secondary metric
        for detection assignment.
        """
        self.velocity = ((coordinate[0] - self.positionQueue[0][0]), (coordinate[1] - self.positionQueue[0][1]))
        if self.visualTracker is not None:
            self.visualCount += 1
            if self.visualCount > MouseTracker.totalAllowedVis:
                self.stopVisualTracking()

    def startVisualTracking(self, frame):
        self.visualTracker = cv2.TrackerKCF_create()
        bbox = (self.currCoord[0] - self.currCoord[4]/2,
            self.currCoord[1] - self.currCoord[5]/2,
            self.currCoord[4], self.currCoord[5])
        if not self.visualTracker.init(frame, bbox):
            self.visualTracker = None
            return False
        else:
            self.visualStartPoint = self.currCoord[3]
            self.canDoVisual = False
            return True

    def stopVisualTracking(self, delete=True):
        self.visualTracker = None
        self.visualCount = 0
        if delete:
            self.trimPositions(self.visualStartPoint)
        else:
            self.canDoVisual = True

    def validate(self):
        self.validatedIndex = len(self.recordedPositions) - 1

    def lastValidatedPosition(self):
        return self.recordedPositions[self.validatedIndex]

    def updatePositions(self, newPositions):
        for position in newPositions:
            for rec in self.recordedPositions:
                if rec[2] == position[2]:
                    self.recordedPositions.remove(rec)
        self.recordedPositions.extend(newPositions)
        self.recordedPositions = sorted(self.recordedPositions, key = lambda x: x[3])
        self.validatedIndex = len(self.recordedPositions) - 1
        self.currCoord = self.recordedPositions[self.validatedIndex]

    def trimPositions(self, frameCount = 0):
        for rec in self.recordedPositions:
            if rec[3] >= frameCount:
                index = self.recordedPositions.index(rec)
        if index > self.validatedIndex:
            self.validatedIndex = index
        tempPositions = self.recordedPositions[self.validatedIndex + 1:]
        self.recordedPositions = self.recordedPositions[:self.validatedIndex+1]
        print(self.id, "Trimmed to", self.validatedIndex, self.lastValidatedPosition())
        return tempPositions

    def getPosition(self):
        return self.currCoord

    def distanceFromPos(self, pos):
        x1 = self.currCoord[0]
        y1 = self.currCoord[1]
        x2 = pos[0]
        y2 = pos[1]
        return np.sqrt((x1-x2)*(x1-x2) + (y1-y2)*(y1-y2))

    def intersectionOverUnion (self, pos):
            selfArea = self.currCoord[4]*self.currCoord[5]
            if selfArea == 0:
                return 0
            posArea = pos[2]*pos[3]
            selfMinX = self.currCoord[0] - self.currCoord[4]/2
            selfMaxX = self.currCoord[0] + self.currCoord[4]/2
            selfMinY = self.currCoord[1] - self.currCoord[5]/2
            selfMaxY = self.currCoord[1] + self.currCoord[5]/2

            otherMinX = pos[0] - pos[2]/2
            otherMaxX = pos[0] + pos[2]/2
            otherMinY = pos[1] - pos[3]/2
            otherMaxY = pos[1] + pos[3]/2

            # Compute the intersection boundaries
            interLeft   = max(selfMinX, otherMinX);
            interTop    = max(selfMinY, otherMinY);
            interRight  = min(selfMaxX, otherMaxX);
            interBottom = min(selfMaxY, otherMaxY);
            # If the intersection is valid (positive non zero area), then there is an intersection
            if ((interLeft < interRight) and (interTop < interBottom)):
                intersection = (interRight - interLeft)*(interBottom - interTop)
            else:
                intersection = 0
            union = posArea + selfArea - intersection
            return intersection/union

    def tag(self):
        return self.id

    def occlusionPointBefore(self, others, distance):
        """
        Examines the recorded positions of the mouse and compares them
        to all other mice locations. The last known point where this mouse
        was near to another will be defined as the end of its last occlusion.
        """
        lastCheckedFrameDict = {}
        for mouse in others:
            lastCheckedFrameDict.update({mouse.tag(): len(mouse.recordedPositions) -1})
        occlusionPoint = len(self.recordedPositions) -1
        endLoop = False
        for i in range(len(self.recordedPositions) -1, -1, -1):
            for mouse in others:
                while self.recordedPositions[i][3] < mouse.recordedPositions[lastCheckedFrameDict[mouse.tag()]][3]:
                    if lastCheckedFrameDict[mouse.tag()] > 0:
                        lastCheckedFrameDict[mouse.tag()] -= 1
                    else:
                        break
                if self.recordedPositions[i][3] == mouse.recordedPositions[lastCheckedFrameDict[mouse.tag()]][3]:
                    x1, y1 = self.recordedPositions[i][0], self.recordedPositions[i][1]
                    x2, y2 = mouse.recordedPositions[lastCheckedFrameDict[mouse.tag()]][0], mouse.recordedPositions[lastCheckedFrameDict[mouse.tag()]][1]
                    if (np.sqrt((x1-x2)*(x1-x2) + (y1-y2)*(y1-y2))) <= distance:
                        occlusionPoint = self.recordedPositions[i][3]
                        endLoop = True
                        break
            if endLoop:
                break
        return occlusionPoint

    def occlusionPointAfter(self, others, distance):
        """
        Examines the recorded positions of the mouse and compares them
        to all other mice locations. The first point after the last validation
        of this mouse where it is near to another will be defined
        as the beginning of its first occlusion.
        """
        lastCheckedFrameDict = {}
        for mouse in others:
            lastCheckedFrameDict.update({mouse.tag(): 0})
        occlusionPoint = self.validatedIndex
        endLoop = False
        for i in range(self.validatedIndex, len(self.recordedPositions)):
            for mouse in others:
                while self.recordedPositions[i][3] > mouse.recordedPositions[lastCheckedFrameDict[mouse.tag()]][3]:
                    if lastCheckedFrameDict[mouse.tag()] < len(mouse.recordedPositions) -1:
                        lastCheckedFrameDict[mouse.tag()] += 1
                    else:
                        break
                if self.recordedPositions[i][3] == mouse.recordedPositions[lastCheckedFrameDict[mouse.tag()]][3]:
                    x1, y1 = self.recordedPositions[i][0], self.recordedPositions[i][1]
                    x2, y2 = mouse.recordedPositions[lastCheckedFrameDict[mouse.tag()]][0], mouse.recordedPositions[lastCheckedFrameDict[mouse.tag()]][1]
                    if (np.sqrt((x1-x2)*(x1-x2) + (y1-y2)*(y1-y2))) <= distance:
                        occlusionPoint = self.recordedPositions[i][3]
                        endLoop = True
                        break
            if endLoop:
                break
        return occlusionPoint
        pass
