import deeplabcut
import argparse
import os
import json
import csv
import cv2
import numpy as np
import fnmatch

def convertBack(x, y, w, h):
    xmin = int(round(x - (w / 2)))
    xmax = int(round(x + (w / 2)))
    ymin = int(round(y - (h / 2)))
    ymax = int(round(y + (h / 2)))
    return xmin, ymin, xmax, ymax

likelihood_thresh = 0.9

def distanceBetweenPos(p1, p2):
    if p1[0] is None or p2[0] is None:
        return False
    x1, y1, x2, y2 = p1[0], p1[1], p2[0], p2[1]
    return np.sqrt((x1-x2)*(x1-x2) + (y1-y2)*(y1-y2))

def getHeadVector(poseData, mid_angle):
    nose     = poseData[0]
    head     = poseData[1]
    neck     = poseData[4]
    midspine = poseData[5]
    options = ((head, nose), (neck, nose), (midspine, nose),
        (neck, head), (midspine, head), (midspine, neck))
    chosen_opt, midpoint, angle = None, None, None
    for opt in options:
        if opt[0] != (None, None) and opt[1] != (None, None):
            midpoint = ((opt[0][0] + opt[1][0])/2, (opt[0][1] + opt[1][1])/2)
            angle = np.arctan2(opt[1][1] - opt[0][1], opt[1][0] - opt[0][0])
            chosen_opt = opt
            break
    return (chosen_opt, midpoint, angle)

def getFOV(headVector):
    headPoint = headVector[1]
    upperAngle = headVector[2] + np.pi/8
    lowerAngle = headVector[2] - np.pi/8
    FOVLength = 120.0
    u_y, u_x = headPoint[1] + np.sin(upperAngle)*FOVLength, \
    headPoint[0] +np.cos(upperAngle)*FOVLength
    l_y, l_x =  headPoint[1] + np.sin(lowerAngle)*FOVLength, \
    headPoint[0] +np.cos(lowerAngle)*FOVLength

    return [headPoint, (u_x, u_y), (l_x, l_y)]
def getTailVector(poseData, mid_angle):
    midspine = poseData[5]
    pelvis   = poseData[6]
    tail     = poseData[7]
    options = ((pelvis, tail), (midspine, tail), (midspine, pelvis))
    chosen_opt, midpoint, angle = None, None, None
    for opt in options:
        if opt[0] != (None, None) and opt[1] != (None, None):
            midpoint = ((opt[0][0] + opt[1][0])/2, (opt[0][1] + opt[1][1])/2)
            angle = np.arctan2(opt[1][1] - opt[0][1], opt[1][0] - opt[0][0])
            chosen_opt = opt
            break
    return (chosen_opt, midpoint, angle)

def getMidVector(poseData):
    neck = poseData[4]
    midspine = poseData[5]
    pelvis   = poseData[6]
    options = ((pelvis, neck), (midspine, neck), (pelvis, midspine))
    chosen_opt, midpoint, angle = None, None, None
    for opt in options:
        if opt[0] != (None, None) and opt[1] != (None, None):
            midpoint = ((opt[0][0] + opt[1][0])/2, (opt[0][1] + opt[1][1])/2)
            angle = np.arctan2(opt[1][1] - opt[0][1], opt[1][0] - opt[0][0])
            chosen_opt = opt
            break
    return (chosen_opt, midpoint, angle)


def run(dataDrive, dataPath, configPath, useFrames=False):
    # config_path = 'G://PoseEstimation-Braeden-2019-11-13//config.yaml'
    deeplabcut.analyze_videos(configPath, [dataDrive + dataPath + "/videos"], videotype=".avi", save_as_csv=True)

    with open (dataDrive + dataPath + "/processed.json", "r") as darkFile:
        darkData = json.loads(darkFile.read())

    for tag, positions in darkData.items():
        for file in os.listdir(dataDrive + dataPath + "/videos"):
            if fnmatch.fnmatch(file, tag + '*.csv'):
                json_index = 0
                with open(dataDrive + dataPath + "/videos" + "/" + file) as csvfile:
                    with open(dataDrive + dataPath + "/videos" + "/" + tag + ".txt") as tfile:
                        reader = list(csv.reader(csvfile))
                        frames = tfile.readlines()
                        print(len(frames))
                        print(len(reader))
                        for index in range(3, len(reader)):
                            print(index)
                            try:
                                row = list(map(float, reader[index]))
                                row[0] = frames[index - 3]
                            except Exception as e:
                                print(str(e))
                                continue
                            while int(positions[json_index][3]) < int(row[0]):
                                json_index += 1
                            if int(positions[json_index][3]) > int(row[0]):
                                continue
                            i = 3
                            while i < 25:
                                if(index == 3):
                                    print(i, len(row), row[0])
                                    print(json_index)
                                if row[i] > likelihood_thresh:
                                    positions[json_index].append(row[i-2])
                                    positions[json_index].append(row[i-1])
                                else:
                                    positions[json_index].append(None)
                                    positions[json_index].append(None)
                                i += 3
                            json_index += 1

    fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')  # 'x264' doesn't work
    video = cv2.VideoWriter(dataDrive + dataPath + '/output_pairs.avi',fourcc, 15.0, (912, 720))
    frameCount = 1
    lastFrameDict = {}
    fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')  # 'x264' doesn't work
    for tag in darkData.keys():
        lastFrameDict.update({tag: 0})
    if not useFrames:
        cap = cv2.VideoCapture(dataDrive + dataPath + "/tracking" + '.h264')
        print(dataDrive
            + dataPath
            + "/tracking"
            + '.h264')
    while True:
        try:
            frameName = dataDrive + dataPath + "/tracking_systembase_tracking" + str(frameCount) + ".jpg"
            if useFrames:
                frame_read = cv2.imread(frameName)
            else:
                success, frame_read = cap.read()
                if not success:
                    print("unable to cap read")
                    raise Exception("Done")
                    break
            frameCount += 1
            # frame_read = cv2.cvtColor(frame_read, cv2.COLOR_BGR2RGB)
        except Exception as e:
            print(str(e))
            break
        for (tag, positions) in darkData.items():
            while True:
                if len(positions) <= lastFrameDict[tag]:
                    break
                if positions[lastFrameDict[tag]][3] == frameCount -1:
                    x, y, w, h = positions[lastFrameDict[tag]][0]*912/640,\
                        positions[lastFrameDict[tag]][1]*720/640,\
                        positions[lastFrameDict[tag]][4]*912/640,\
                        positions[lastFrameDict[tag]][5]*720/640
                    xmin, ymin, xmax, ymax = convertBack(
                        float(x), float(y), float(w), float(h))
                    pt1 = (xmin, ymin)
                    pt2 = (xmax, ymax)
                    poseParts = []
                    # Nose, head, left ear, right ear, neck,
                    # midspine, pelvis, tail
                    colors = [
                        [255, 0, 0],
                        [0, 255, 0],
                        [0, 0, 255],
                        [255, 255, 0],
                        [255, 0, 255],
                        [0, 255, 255],
                        [255,255,255],
                        [0,0,0]
                    ]
                    i = 6
                    while i < len(positions[lastFrameDict[tag]]) - 1:
                        if positions[lastFrameDict[tag]][i] is not None:
                            poseParts.append((int(positions[lastFrameDict[tag]][i]),\
                                int(positions[lastFrameDict[tag]][i+1])))
                        else:
                            poseParts.append((None, None))
                        i += 2
                    dist, closest = 9999, -1
                    nose = poseParts[0]
                    if nose[0] is not None:
                        for i in range(1, len(poseParts)-1):
                            if poseParts[i] is not None and distanceBetweenPos(nose, poseParts[i]) < dist:
                                dist = distanceBetweenPos(nose, poseParts[i])
                                closest = i
                        if closest > 4:
                            poseParts[0] = (None, None)
                            positions[lastFrameDict[tag]][6] = None
                            positions[lastFrameDict[tag]][7] = None
                    tail = poseParts[7]
                    dist, closest = 9999, 8
                    if tail[0] is not None:
                        for i in range(1, len(poseParts)-1):
                            if poseParts[i] is not None and distanceBetweenPos(tail, poseParts[i]) < dist:
                                dist = distanceBetweenPos(tail, poseParts[i])
                                closest = i
                        if closest < 5:
                            poseParts[7] = (None, None)
                            positions[lastFrameDict[tag]][20] = None
                            positions[lastFrameDict[tag]][21] = None
                    if len(positions[lastFrameDict[tag]]) >=10:
                        for i in range(0, len(poseParts)):
                            if poseParts[i][0] is not None:
                                cv2.circle(frame_read, poseParts[i], 5, colors[i])
                        m_v = getMidVector(poseParts)
                        h_v = getHeadVector(poseParts, m_v[2])
                        t_v = getTailVector(poseParts, m_v[2])
                        if h_v[0] is not None:
                            cv2.arrowedLine(frame_read, h_v[0][0], h_v[0][1], [255, 0, 0])
                            FOV = np.array(getFOV(h_v), dtype=np.int32)
                            cv2.fillPoly(frame_read, np.int32([FOV]), [0, 255, 0])
                        if t_v[0] is not None:
                            cv2.arrowedLine(frame_read, t_v[0][0], t_v[0][1], [0, 255, 0])
                        if m_v[0] is not None:
                            cv2.arrowedLine(frame_read, m_v[0][0], m_v[0][1], [0, 0, 255])
                    cv2.rectangle(frame_read, pt1, pt2, (0, 255, 0), 1)
                    cv2.putText(frame_read,
                                str(tag),
                                (pt1[0], pt1[1] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                                [0, 255, 0], 2)
                    break
                elif positions[lastFrameDict[tag]][3] < frameCount -1:
                    lastFrameDict[tag] += 1
                else:
                    break
        print("wrote frame", frameCount)
        video.write(frame_read)
    video.release()
    with open(dataDrive + dataPath + "/processed_ht.json", "w") as outfile:
        json.dump(darkData, outfile, ensure_ascii=False)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", "--name", help="Name of the frame folder/text file")
    ap.add_argument("-d", "--drive", help="Path to data")
    ap.add_argument("-f", "--frames", help="Include this argument if you have individual frame files")
    args = vars(ap.parse_args())
    dataPath = args.get("name")
    dataDrive = args.get("drive", "frameData")
    run(dataDrive, dataPath)
