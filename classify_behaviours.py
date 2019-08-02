import json
import numpy as np

totalFrames = 17404
def distanceBetweenPos(p1, p2):
    if p1 is None or p2 is None:
        return False
    x1, y1, x2, y2 = p1[0][0], p1[0][1], p2[0][0], p2[0][1]
    return np.sqrt((x1-x2)*(x1-x2) + (y1-y2)*(y1-y2))
social_radius = 90


def convertBack(x, y, w, h):
    xmin = int(round(x - (w / 2)))
    xmax = int(round(x + (w / 2)))
    ymin = int(round(y - (h / 2)))
    ymax = int(round(y + (h / 2)))
    return xmin, ymin, xmax, ymax


darkFile = open("darknet/processed.json", "r")
darkData = json.loads(darkFile.read())

mouseDict = {}
for tag in darkData.keys():
    mouseDict.update({tag: []})

frameCount = 1
while True:
    for (tag, datum) in darkData.items():
        for position in datum:
            if position[3] == frameCount:
                if len(position) > 4:
                    x, y, w, h = position[0]*640/608,\
                        position[1]*480/608,\
                        position[4]*640/608,\
                        position[5]*480/608
                else:
                    x, y, w, h = position[0]*640/608,\
                        position[1]*480/608, 0, 0
                xmin, ymin, xmax, ymax = convertBack(
                    float(x), float(y), float(w), float(h))
                center = (x, y)
                pt1 = (xmin, ymin)
                pt2 = (xmax, ymax)
                pos = [center, pt1, pt2]
                mouseDict[tag].append(pos)
                break
            elif position[3] > frameCount:
                mouseDict[tag].append(None)
                break
    frameCount += 1
    if frameCount > totalFrames:
        break

twoGroupFormingFrames = []
twoGroupLeavingFrames = []
threeGroupFormingFrames = []
threeGroupLeavingFrames = []
lastGroup = set()
for i in range(0, totalFrames):
    group = set()
    for mouse, positions in mouseDict.items():
        for other, other_pos in mouseDict.items():
            if mouse != other:
                dist = distanceBetweenPos(positions[i], other_pos[i])
                if dist and dist < social_radius:
                    group.add(mouse)
                    group.add(other)
    if len(group) == 2 and len(lastGroup) < 2:
        twoGroupFormingFrames.append(i)
    if len(group) == 3 and len(lastGroup) < 3:
        threeGroupFormingFrames.append(i)
    if len(group) < 3 and len(lastGroup) == 3:
        threeGroupLeavingFrames.append(i)
    if len(group) < 2 and len(lastGroup) ==2 :
        twoGroupLeavingFrames.append(i)
    lastGroup = group

print("two - Entering:", len(twoGroupFormingFrames),  "- Leaving:",  len(twoGroupLeavingFrames))
print("three - Entering:", len(threeGroupFormingFrames), "-Leaving:",  len(threeGroupLeavingFrames))
