import deeplabcut
import argparse
import os
import json
import csv
import cv2
import fnmatch

def convertBack(x, y, w, h):
    xmin = int(round(x - (w / 2)))
    xmax = int(round(x + (w / 2)))
    ymin = int(round(y - (h / 2)))
    ymax = int(round(y + (h / 2)))
    return xmin, ymin, xmax, ymax

likelihood_thresh = 0.5

ap = argparse.ArgumentParser()
ap.add_argument("-n", "--name", help="Name of the frame folder/text file")
ap.add_argument("-d", "--drive", help="Path to data")
ap.add_argument("-f", "--frames", help="Include this argument if you have individual frame files")
args = vars(ap.parse_args())
dataPath = args.get("name")
dataDrive = args.get("drive", "frameData")

config_path = '/home/user/CropMouseLabel-Braeden-2019-09-11/config.yaml'
#deeplabcut.analyze_videos(config_path, [dataDrive + dataPath + "/videos"], videotype=".avi", save_as_csv=True)

with open (dataDrive + dataPath + "/processed.json", "r") as darkFile:
    darkData = json.loads(darkFile.read())

for tag, datum in darkData.items():
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
                        while int(datum[json_index][3]) < int(row[0]):
                            json_index += 1
                        if int(datum[json_index][3]) > int(row[0]):
                            continue
                        i = 3
                        while i < 13:
                            if(index == 3):
                                print(i, len(row), row[0])
                                print(json_index)
                            if row[i] > likelihood_thresh:
                                datum[json_index].append(row[i-2])
                                datum[json_index].append(row[i-1])
                            else:
                                datum[json_index].append(None)
                                datum[json_index].append(None)
                            i += 3
                        json_index += 1

fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')  # 'x264' doesn't work
video = cv2.VideoWriter('output_pairs' + dataPath + '.avi',fourcc, 15.0, (912, 720))
frameCount = 2
lastFrameDict = {}
fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')  # 'x264' doesn't work
for tag in darkData.keys():
    lastFrameDict.update({tag: 0})
while True:
    try:
        frameName = dataDrive + dataPath + "/tracking_systembase_tracking" + str(frameCount) + ".jpg"
        frame_read = cv2.imread(frameName)
        frameCount += 1
        print(frameCount)
        frame_rgb = cv2.cvtColor(frame_read, cv2.COLOR_BGR2RGB)
    except Exception as e:
        print(str(e))
        break
    for (tag, datum) in darkData.items():
        while True:
            if len(datum) <= lastFrameDict[tag]:
                break
            if datum[lastFrameDict[tag]][3] == frameCount:
                x, y, w, h = datum[lastFrameDict[tag]][0]*912/640,\
                    datum[lastFrameDict[tag]][1]*720/640,\
                    datum[lastFrameDict[tag]][4]*912/640,\
                    datum[lastFrameDict[tag]][5]*720/640
                xmin, ymin, xmax, ymax = convertBack(
                    float(x), float(y), float(w), float(h))
                pt1 = (xmin, ymin)
                pt2 = (xmax, ymax)
                if len(datum[lastFrameDict[tag]]) >=10:
                    head = (datum[lastFrameDict[tag]][6], datum[lastFrameDict[tag]][7])
                    tail = (datum[lastFrameDict[tag]][8], datum[lastFrameDict[tag]][9])
                    l_ear = (datum[lastFrameDict[tag]][10], datum[lastFrameDict[tag]][11])
                    r_ear = (datum[lastFrameDict[tag]][12], datum[lastFrameDict[tag]][13])
                    if head != (None, None):
                        head = (int(head[0]), int(head[1]))
                        cv2.circle(frame_rgb, head, 5, [0, 0, 255])
                        if tail != (None, None):
                            tail = (int(tail[0]), int(tail[1]))
                            cv2.line(frame_rgb, head, tail, [0, 255, 0])
                    if tail != (None, None):
                        tail = (int(tail[0]), int(tail[1]))
                        cv2.circle(frame_rgb, tail, 5, [255, 0, 0])
                    if l_ear != (None, None):
                        l_ear = (int(l_ear[0]), int(l_ear[1]))
                        cv2.circle(frame_rgb, l_ear, 5, [255, 255, 0])
                    if r_ear != (None, None):
                        r_ear = (int(r_ear[0]), int(r_ear[1]))
                        cv2.circle(frame_rgb, r_ear, 5, [0, 255, 255])
                cv2.rectangle(frame_rgb, pt1, pt2, (0, 255, 0), 1)
                cv2.putText(frame_rgb,
                            str(tag),
                            (pt1[0], pt1[1] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                            [0, 255, 0], 2)
                break
            elif datum[lastFrameDict[tag]][3] < frameCount:
                lastFrameDict[tag] += 1
            else:
                break
    video.write(frame_rgb)
video.release()
with open(dataDrive + dataPath + "/processed_ht.json", "w") as outfile:
    json.dump(darkData, outfile, ensure_ascii=False)
