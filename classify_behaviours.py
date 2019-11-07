import json
import numpy as np
import math
import argparse
from contextlib import ExitStack
import re

totalFrames = 10936


def distanceBetweenPos(p1, p2):
    if p1 is None or p2 is None:
        return False
    x1, y1, x2, y2 = p1[0][0], p1[0][1], p2[0][0], p2[0][1]
    return np.sqrt((x1-x2)*(x1-x2) + (y1-y2)*(y1-y2))


group_radius = 120
social_radius = 150
velocity_thresh = 5

def convertBack(x, y, w, h):
    xmin = int(round(x - (w / 2)))
    xmax = int(round(x + (w / 2)))
    ymin = int(round(y - (h / 2)))
    ymax = int(round(y + (h / 2)))
    return xmin, ymin, xmax, ymax


ap = argparse.ArgumentParser()
ap.add_argument("-n", "--name", help="Name of the frame folder/text file")
ap.add_argument("-d", "--drive", help="Path to data")
ap.add_argument("-f", "--frames", help="Include this argument if you have individual frame files")
args = vars(ap.parse_args())
dataPath = args.get("name")
dataDrive = args.get("drive", "frameData")

darkFile = open(dataDrive + dataPath + "/processed_ht.json", "r")
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
                    x, y, w, h = position[0]*912/640,\
                        position[1]*720/640,\
                        position[4]*912/640,\
                        position[5]*720/640
                else:
                    x, y, w, h = position[0]*912/640,\
                        position[1]*720/640, 0, 0
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
files = {}
for tag in mouseDict.keys():
    velocities.update({tag: None})
    approaches.update({tag: []})
    files.update({tag: dataDrive + dataPath + "/classified_" + tag + ".csv"})
twoGroupFormingFrames = []
twoGroupLeavingFrames = []
threeGroupFormingFrames = []
threeGroupLeavingFrames = []
lastGroup = set()
with ExitStack() as stack:
    for tag, name in files.items():
        files[tag] = stack.enter_context(open(name))
        files[tag].write("Frame,Behaviour,Center_x,Center_y,Width," +
                            "Height,Head_x,Head_y,Tail_x,Tail_y\n")
    for i in range(0, totalFrames):
        group = set()
        for mouse, positions in mouseDict.items():
            if len(positions) <= i:
                files[tag].write(str(i) + ",Nesting\n")
                break
            if i > 1 and positions[i-1] is not None and positions[i] is not None:
                velocities.update({mouse:(positions[i][0][0] - positions[i-1][0][0],
                    positions[i][0][1] - positions[i-1][0][1])})
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
            if mouse in group:
                if mouse not in lastGroup:
                    files[tag].write(str(i) + ",GroupEntering")
                else:
                    if velocities[mouse] > velocity_thresh:
                        files[tag].write(str(i) + ",Grouping")
                    else:
                        files[tag].write(str(i) + ",Nesting")
            for aspect in position:
                files[tag].write(re.sub('[^A-Za-z0-9\,]+', '', str(aspect)) + ",")
            files[tag].write("\n")
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
""
