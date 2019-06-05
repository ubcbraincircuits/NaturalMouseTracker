import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
import json
from MouseTracker import MouseTracker

fileName = "test.txt"
width = 640
height = 480

mice = {}
# file = open(fileName)
# file.seek(0)
# for line in file:
#     ln = line.split(";")
#     mouse = mice.get(ln[1], None)
#     if mouse is None:
#         mice.update({ln[1]: [{"position": [item for item in ln[2].strip('()\n').split(',')], "time": float(ln[0])}]})
#     else:
#         mice[ln[1]].append({"position": [item for item in ln[2].strip('()\n').split(',')], "time": float(ln[0])})

#Temporary, need to store different info
mouseTrackers = []
mouseTrackers.append(MouseTracker((341, 266), 1))
mouseTrackers.append(MouseTracker((210, 166), 2))
mouseTrackers.append(MouseTracker((172, 82), 3))
recordedPositions = {1: [], 2: [], 3: []}

darkFile = open("result.json", "r")
darkData = json.loads(darkFile.read())
for datum in darkData:
    for detected in datum["objects"]:
        allowedTrackers = []
        position = (width*detected["relative_coordinates"]["center_x"], height*detected["relative_coordinates"]["center_y"])
        nearestTracker = sorted(list(filter(lambda x: x not in allowedTrackers, mouseTrackers)), key= lambda x: x.distanceFromPos(position))[0]
        allowedTrackers.append(nearestTracker)
        nearestTracker.updatePosition(position)
        recordedPositions[nearestTracker.tag()].append(position)


fig = plt.figure()
img = mpimg.imread("ref.jpg")
plt.imshow(img)
plt.axis((0, 640, 0, 480))
for positionData in recordedPositions.values():
    x = list(map(lambda x: int(x[0]), positionData))
    y = list(map(lambda x: int(x[1]), positionData))
    print(positionData)
    plt.plot(x, y)
plt.show()
