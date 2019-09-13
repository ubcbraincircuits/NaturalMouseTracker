import json
import numpy as np
import math

totalFrames = 10936
def distanceBetweenPos(p1, p2):
    if p1 is None or p2 is None:
        return False
    x1, y1, x2, y2 = p1[0][0], p1[0][1], p2[0][0], p2[0][1]
    return np.sqrt((x1-x2)*(x1-x2) + (y1-y2)*(y1-y2))
group_radius = 120
social_radius = 150


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
                head_pos = (position[6], position[7])
                tail_pos = (position[8], position[9])
                center = (x, y)
                pt1 = (xmin, ymin)
                pt2 = (xmax, ymax)
                pos = [center, pt1, pt2, head_pos, tail_pos]
                mouseDict[tag].append(pos)
                break
            elif position[3] > frameCount:
                mouseDict[tag].append(None)
                break
    frameCount += 1
    if frameCount > totalFrames:
        break
velocities = {}
approaches = {}
for tag in mouseDict.keys():
    velocities.update({tag: None})
    approaches.update({tag: []})
twoGroupFormingFrames = []
twoGroupLeavingFrames = []
threeGroupFormingFrames = []
threeGroupLeavingFrames = []
lastGroup = set()
for i in range(0, totalFrames):
    group = set()
    for mouse, positions in mouseDict.items():
        if len(positions) <= i:
            break
        if i > 4 and positions[i-5] is not None and positions[i] is not None:
            velocities.update({mouse:(positions[i][0][0] - positions[i-5][0][0],
                positions[i][0][1] - positions[i-5][0][1])})
        else:
            velocities.update({mouse: None})
        for other, other_pos in mouseDict.items():
            if mouse != other:
                if len(positions) <= i or len(other_pos) <= i:
                    continue
                dist = distanceBetweenPos(positions[i], other_pos[i])
                if dist and dist < group_radius:
                    group.add(mouse)
                    group.add(other)
                elif dist and dist < social_radius and velocities[mouse] is not None:
                    dist_vector = (other_pos[i][0][0] - positions[i][0][0],
                        other_pos[i][0][1] - positions[i][0][1])
                    dot = dist_vector[0]*velocities[mouse][0] + dist_vector[1]*velocities[mouse][1]
                    det = dist_vector[0]*velocities[mouse][1] - dist_vector[1]*velocities[mouse][0]
                    angle = math.atan2(det, dot)*(180/np.pi)  # atan2(y, x) or atan2(sin, cos)
                    if abs(angle) < 20 and np.sqrt(velocities[mouse][1]**2 + velocities[mouse][0]**2) > 2:
                        if len(approaches[mouse]) == 0 or  approaches[mouse][-1][0] < i -10:
                            approaches[mouse].append((i, other))
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
print("three - Entering:", len(threeGroupFormingFrames), "- Leaving:",  len(threeGroupLeavingFrames))
print(approaches)
