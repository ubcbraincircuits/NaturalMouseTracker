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
args = vars(ap.parse_args())

config_path = r'C:\Users\greg2\Desktop\Braeden\DeepLabCut\Mouse Background-Braeden-2019-08-14\config.yaml'
deeplabcut.analyze_videos(config_path, ["C:\\Users\\greg2\\Desktop\\Braeden\\MouseTrackingSystem\\darknet\\videos" + args.get("name", "")], videotype=".avi", save_as_csv=True)

with open ("darknet\\processed.json", "r") as darkFile:
    darkData = json.loads(darkFile.read())
    #lol


for tag, datum in darkData.items():
    for file in os.listdir('darknet\\videos' + args.get("name", "")):
        if fnmatch.fnmatch(file, tag + '*.csv'):
            json_index = 0
            with open('darknet\\videos' + args.get("name", "") + "\\" + file) as csvfile:
                with open('darknet\\videos' + args.get("name", "") + "\\" + tag + ".txt") as tfile:
                    reader = list(csv.reader(csvfile))
                    frames = tfile.readlines()
                    print(len(frames))
                    print(len(reader))
                    for index in range(3, len(reader)):
                        try:
                            row = list(map(float, reader[index]))
                            row[0] = frames[index - 3]
                        except Exception as e:
                            continue
                        while int(datum[json_index][3]) < int(row[0]):
                            json_index += 1
                        if int(datum[json_index][3]) > int(row[0]):
                            continue
                        if row[3] > likelihood_thresh:
                            datum[json_index].append(row[1])
                            datum[json_index].append(row[2])
                        else:
                            datum[json_index].append(None)
                            datum[json_index].append(None)
                        if row[6] > likelihood_thresh:
                            datum[json_index].append(row[4])
                            datum[json_index].append(row[5])
                        else:
                            datum[json_index].append(None)
                            datum[json_index].append(None)
                        json_index += 1

fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')  # 'x264' doesn't work
video = cv2.VideoWriter('output_pairs08132019.avi',fourcc, 15.0, (640, 480))
frameCount = 2
lastFrameDict = {}
fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')  # 'x264' doesn't work
for tag in darkData.keys():
    lastFrameDict.update({tag: 0})
while True:
    try:
        frameName = "darknet/frameData"+ args.get("name", "") + "/tracking_systembase_tracking" + str(frameCount) + ".png"
        frame_read = cv2.imread(frameName)
        frameCount += 1
        frame_rgb = cv2.cvtColor(frame_read, cv2.COLOR_BGR2RGB)
        print(frameCount)
    except Exception as e:
        print(str(e))
        break
    for (tag, datum) in darkData.items():
        while True:
            if len(datum) <= lastFrameDict[tag]:
                break
            if datum[lastFrameDict[tag]][3] == frameCount:
                x, y, w, h = datum[lastFrameDict[tag]][0]*640/608,\
                    datum[lastFrameDict[tag]][1]*480/608,\
                    datum[lastFrameDict[tag]][4]*640/608,\
                    datum[lastFrameDict[tag]][5]*480/608
                xmin, ymin, xmax, ymax = convertBack(
                    float(x), float(y), float(w), float(h))
                pt1 = (xmin, ymin)
                pt2 = (xmax, ymax)
                if len(datum[lastFrameDict[tag]]) >=10:
                    head = (datum[lastFrameDict[tag]][6], datum[lastFrameDict[tag]][7])
                    tail = (datum[lastFrameDict[tag]][8], datum[lastFrameDict[tag]][9])
                    if head != (None, None):
                        head = (int(head[0]), int(head[1]))
                        cv2.circle(frame_rgb, head, 5, [0, 0, 255])
                        if tail != (None, None):
                            tail = (int(tail[0]), int(tail[1]))
                            cv2.line(frame_rgb, head, tail, [0, 255, 0])
                    if tail != (None, None):
                        tail = (int(tail[0]), int(tail[1]))
                        cv2.circle(frame_rgb, tail, 5, [255, 0, 0])
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
with open("darknet\\processed_ht.json", "w") as outfile:
    json.dump(darkData, outfile, ensure_ascii=False)
