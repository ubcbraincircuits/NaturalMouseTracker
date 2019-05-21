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
