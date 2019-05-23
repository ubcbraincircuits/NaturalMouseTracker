import numpy as np
class MouseTracker:

    def __init__(self, startCoord, id):
        self.prevCoord = startCoord
        self.currCoord = startCoord
        self.id = id
        self.bundled = False

    def updatePosition(self, coordinate, isBundle):
        self.prevCoord = self.currCoord
        self.currCoord = coordinate
        self.bundled = isBundle

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
