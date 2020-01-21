import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
import cv2
import json
import os
import shutil
import argparse
from billiard.context import Process
from filterpy.kalman import KalmanFilter
from filterpy.common import Q_discrete_white_noise
from time import sleep
from tqdm import tqdm

def convertBack(x, y, w, h):
    '''
    Given some bounding box defined by x,y,w,h
    where x,y = center of bounding box

    return the coordinate of its bottom l and top r corners
    '''
    xmin = int(round(x - (w / 2)))
    xmax = int(round(x + (w / 2)))
    ymin = int(round(y - (h / 2)))
    ymax = int(round(y + (h / 2)))
    return xmin, ymin, xmax, ymax


def createVideo(tag, datum, fourcc, dataDrive, dataPath, frames, trackProgress):
    '''
    given a tracking.h264 file and tag of mouse featured in the video,
    crop every frame of the video to a box surrounding the mouse
    replacing cropped portions with whitespace

    in addition, creates a text file that contains every frame number on which
    the mouse of interest was validated by a reader.

    This function does the majority of the work for its class.
    The run method of crop_vidos.py is called from main and it creates
    worker processes to carry out this function in paralell
    '''
    global trialName
    if not frames:
        cap = cv2.VideoCapture(dataDrive + dataPath + "/tracking" + '.h264')
        print(dataDrive
            + dataPath
            + "/tracking"
            + '.h264')

    table = np.array([((i/255.0) ** 0.75)*255 #0.7 to 0.9 seems like a good range.
        for i in np.arange(0, 256)]).astype('uint8')
    frameCount = 1
    lastFrame = 0
    trialName = "base_tracking"
    video = cv2.VideoWriter(dataDrive + dataPath + "/videos/" + tag + ".avi" ,fourcc, 15.0, (912, 720))
    file = open(dataDrive + dataPath + "/videos/" + tag + ".txt", "w")
    with tqdm(total=18000) as pbar:
        while True:
            try:
                frameName = dataDrive + dataPath + "/tracking_system" + trialName + str(frameCount) + ".jpg"
                if frames:
                    frame_read = cv2.imread(frameName)
                else:
                    success, frame_read = cap.read()
                    if not success:
                        print("unable to cap read")
                        break
                frameCount += 1
                frame_read = cv2.LUT(frame_read, table)
                frame_rgb = cv2.cvtColor(frame_read, cv2.COLOR_BGR2GRAY)
                frame_rgb_c = cv2.cvtColor(frame_read, cv2.COLOR_BGR2GRAY)
                frame_rgb = cv2.cvtColor(frame_rgb, cv2.COLOR_GRAY2RGB)
                frame_rgb_c = cv2.cvtColor(frame_rgb_c, cv2.COLOR_GRAY2RGB)
                # print(frameCount)
                if trackProgress:
                    pbar.update()
            except Exception as e:
                print(str(e), 'er')
                break
            if len(datum) < 1:
                break
            del_t = 0.1
            while True:
                if len(datum) <= lastFrame:
                    break
                if datum[lastFrame][3] == frameCount -1:
                    w, h = datum[lastFrame][4]*912/640,\
                        datum[lastFrame][5]*720/640
                    z = np.array([[datum[lastFrame][0]], [datum[lastFrame][1]]])
                    x, y = z[0]*912/640, z[1]*720/640
                    xmin, ymin, xmax, ymax = convertBack(
                        float(x), float(y), float(w), float(h))
                    pt1 = (max(xmin-20, 0), max(ymin-20, 0))
                    pt2 = (min(xmax +20, 912), min(ymax + 20, 720))
                    blank_image = np.ones((720,912,3), np.uint8)*255
                    blank_image[pt1[1]:pt2[1], pt1[0]:pt2[0]] = frame_rgb[pt1[1]:pt2[1], pt1[0]:pt2[0]]
                    video.write(blank_image)
                    file.write(str(frameCount -1) + "\n")
                    cv2.rectangle(frame_rgb_c, pt1, pt2, (0, 255, 0), 1)
                    cv2.circle(frame_rgb_c, (int(x), int(y)), 5,  [0, 255, 0])
                    #cv2.arrowedLine(frame_rgb_c, (int(x - vel_x), int(y - vel_y)), (int(x + vel_x), int(y + vel_y)), [0, 0, 255])
                    cv2.putText(frame_rgb_c,
                                str(tag),
                                (pt1[0], pt1[1] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                                [0, 255, 0], 2)
                    break
                elif datum[lastFrame][3] < frameCount -1:
                    lastFrame += 1
                else:
                    break
            # main.write(frame_rgb_c)
    video.release()
    file.close()


def run(dataDrive, dataPath, frames=False):
    print("Current dir from first line in run",os.listdir())
    darkFile = open(dataDrive + dataPath + "/processed.json", "r")
    darkData = json.loads(darkFile.read())
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')  # 'x264' doesn't work
    main = cv2.VideoWriter(dataDrive + dataPath + '/output_filtered' + '.avi', fourcc, 15.0, (912, 720))
    try:
        shutil.rmtree(dataDrive + dataPath + "/videos")
    except Exception as e:
        print(str(e))
        pass
    finally:
        print("Just created videos folder")
        os.mkdir(dataDrive + dataPath + "/videos")
    processes = []
    track = True
    for tag, datum in darkData.items():
        p = Process(target=createVideo, args=(tag, datum, fourcc, dataDrive, dataPath, frames, track))
        track = False
        processes.append(p)
        p.start()
    sleep(5)
    for process in processes:
        process.join()


    cv2.destroyAllWindows()

if __name__ == "__main__":
    trialName = "base_tracking"
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", "--name", help="Name of the frame folder/text file")
    ap.add_argument("-d", "--drive", help="Path to data")
    ap.add_argument("-f", "--frames", help="Include this argument if you have individual frame files")
    args = vars(ap.parse_args())
    dataPath = args.get("name")
    dataDrive = args.get("drive", "frameData")
    frames = False
    if args.get("frames", None) is not None:
        frames = True
    run(dataDrive, dataPath, frames=frames)
