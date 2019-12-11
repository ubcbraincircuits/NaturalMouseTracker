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

likelihood_thresh = 0.9

def run(dataDrive, dataPath, configPath, useFrames=False):
    # config_path = 'G://PoseEstimation-Braeden-2019-11-13//config.yaml'
    # deeplabcut.analyze_videos(configPath, [dataDrive + dataPath + "/videos"], videotype=".avi", save_as_csv=True)

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
                            while i < 13:
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
                    if len(positions[lastFrameDict[tag]]) >=10:
                        head = (positions[lastFrameDict[tag]][6], positions[lastFrameDict[tag]][7])
                        tail = (positions[lastFrameDict[tag]][8], positions[lastFrameDict[tag]][9])
                        l_ear = (positions[lastFrameDict[tag]][10], positions[lastFrameDict[tag]][11])
                        r_ear = (positions[lastFrameDict[tag]][12], positions[lastFrameDict[tag]][13])
                        if head != (None, None):
                            head = (int(head[0]), int(head[1]))
                            cv2.circle(frame_read, head, 5, [0, 0, 255])
                            if tail != (None, None):
                                tail = (int(tail[0]), int(tail[1]))
                                cv2.line(frame_read, head, tail, [0, 255, 0])
                        if tail != (None, None):
                            tail = (int(tail[0]), int(tail[1]))
                            cv2.circle(frame_read, tail, 5, [255, 0, 0])
                        if l_ear != (None, None):
                            l_ear = (int(l_ear[0]), int(l_ear[1]))
                            cv2.circle(frame_read, l_ear, 5, [255, 255, 0])
                        if r_ear != (None, None):
                            r_ear = (int(r_ear[0]), int(r_ear[1]))
                            cv2.circle(frame_read, r_ear, 5, [0, 255, 255])
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
