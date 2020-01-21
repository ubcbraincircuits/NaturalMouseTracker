import cv2
from time import sleep
import json
import mysql.connector
import numpy as np

entranceX = 827
entranceY = 281

videoFile = input("Please enter the path of the data folder to verify results")
cap = cv2.VideoCapture(videoFile + "/tracking.h264")
print(videoFile + "/tracking.h264")


behaviour_json = open(videoFile + "/processed_ht.json", "r")
behaviour = json.loads(behaviour_json.read())

query_results = {}
pose_results = {}

for i in behaviour:
    pose_results.update({i:[]})
    query_results.update({i:[]})
print(query_results.items())




try:
    db = mysql.connector.connect(host='localhost', user='admin', db='tracking_behaviour', password='AutoHead2015',
    auth_plugin="mysql_native_password")
    cur = db.cursor(dictionary=True)
    ts_Regex = videoFile[-5:]
    date = videoFile[-16:-6]
    print(ts_Regex, date)
    query = """ select Tag, Date, Time, Name, Center_x, Center_y, Width, Height from miceevents
    LEFT JOIN behaviours ON miceevents.behaviour=behaviours.ID LEFT JOIN positions ON miceevents.Position=Positions.ID
    WHERE Time like %s AND Date=%s AND Tag=%s;  """

    pose_query = """ select Nose_x, Nose_y, Head_x, Head_y, LeftEar_x,
        LeftEar_y, RightEar_x, RightEar_y, Neck_x, Neck_y, Midspine_x,
        Midspine_y, Pelvis_x, Pelvis_y, Tail_x, Tail_y FROM miceevents
        LEFT JOIN poses on miceevents.pose=poses.ID WHERE Time like %s AND Date=%s AND Tag=%s;
        """
    for tag in query_results.keys():
        cur.execute(pose_query, [ts_Regex + '%', date, tag])
        pose_results[tag] = cur.fetchall()
        print(query.format(ts_Regex))
        cur.execute(query, [ts_Regex + '%', date, tag])
        query_results[tag] = cur.fetchall()
        print(tag, query_results[tag][2])
    cur.close()




except Exception as e:
    print(str(e))

def getHeadVector(poseData):
    nose     = poseData['Nose_x'], poseData['Nose_y']
    head     = poseData['Head_x'], poseData['Head_y']
    neck     = poseData['Neck_x'], poseData['Neck_y']
    midspine = poseData['Midspine_x'], poseData['Midspine_y']
    options = ((neck, head), (midspine, head),
    (head, nose), (neck, nose), (midspine, nose), (midspine, neck))
    chosen_opt, midpoint, angle = None, None, None
    for opt in options:
        if opt[0] != (0, 0) and opt[1] != (0, 0):
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

def getTailVector(poseData):
    midspine = poseData['Midspine_x'], poseData['Midspine_y']
    pelvis   = poseData['Pelvis_x'], poseData['Pelvis_y']
    tail     = poseData['Tail_x'], poseData['Tail_y']
    options = ((pelvis, tail), (midspine, tail), (midspine, pelvis))
    chosen_opt, midpoint, angle = None, None, None
    for opt in options:
        if opt[0] != (0, 0) and opt[1] != (0, 0):
            midpoint = ((opt[0][0] + opt[1][0])/2, (opt[0][1] + opt[1][1])/2)
            angle = np.arctan2(opt[1][1] - opt[0][1], opt[1][0] - opt[0][0])
            chosen_opt = opt
            break
    return (chosen_opt, midpoint, angle)

def getMidVector(poseData):
    neck     = poseData['Neck_x'], poseData['Neck_y']
    midspine = poseData['Midspine_x'], poseData['Midspine_y']
    pelvis   = poseData['Pelvis_x'], poseData['Pelvis_y']
    options = ((pelvis, neck), (midspine, neck), (pelvis, midspine))
    chosen_opt, midpoint, angle = None, None, None
    for opt in options:
        if opt[0] != (0, 0) and opt[1] != (0, 0):
            midpoint = ((opt[0][0] + opt[1][0])/2, (opt[0][1] + opt[1][1])/2)
            angle = np.arctan2(opt[1][1] - opt[0][1], opt[1][0] - opt[0][0])
            chosen_opt = opt
            break
    return (chosen_opt, midpoint, angle)


colors = [
    [255, 0, 0],
    [0, 255, 0],
    [0, 0, 255],
    [255, 255, 0]
    ]

curFrame=0
while True:
    success, frame_read = cap.read()

    if success:
        cv2.putText(frame_read, str(curFrame), (800,50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
        i = 0
        cv2.rectangle(frame_read, (entranceX, entranceY), (912, 720), [0, 120,120])
        for tag, results in query_results.items():
            print(results[curFrame])
            print(pose_results[tag][curFrame])
            x, y, w, h = int(float(results[curFrame]['Center_x'])),\
                int(float(results[curFrame]['Center_y'])),\
                int(float(results[curFrame]['Width'])),\
                int(float(results[curFrame]['Height']))
            pt1 = [int(x - w/2), int(y - h/2)]
            pt2 = [int(x + w/2), int(y + h/2)]
            pt1 = (max(pt1[0], 0), max(pt1[1], 0))
            pt2 = (min(pt2[0], 912), min(pt2[1], 720))
            cv2.putText(frame_read, str(tag + ' ' + results[curFrame]['Name']), (50,50 + 40*i), cv2.FONT_HERSHEY_SIMPLEX, 0.5, colors[i], 1)
            try:
                cv2.circle(frame_read, (x, y), 5, colors[i])
                cv2.rectangle(frame_read, pt1, pt2, colors[i])
                print("i put the rectangles on")
            except Exception as e:
                print(str(e))
            i += 1
            for key, val in pose_results[tag][curFrame].items():
               pose_results[tag][curFrame][key] = int(val)
            h_v = getHeadVector(pose_results[tag][curFrame])
            m_v = getMidVector(pose_results[tag][curFrame])
            t_v = getTailVector(pose_results[tag][curFrame])

            if h_v[0] is not None:
               print(h_v)
               cv2.arrowedLine(frame_read, h_v[0][0], h_v[0][1], [255, 0, 0])
               FOV = np.array(getFOV(h_v), dtype=np.int32)
               cv2.fillPoly(frame_read, np.int32([FOV]), [0, 255, 0])

            if t_v[0] is not None:
               cv2.arrowedLine(frame_read, t_v[0][0], t_v[0][1], [0, 255, 0])

            if m_v[0] is not None:
               cv2.arrowedLine(frame_read, m_v[0][0], m_v[0][1], [0, 0, 255])

        cv2.imshow("frame_read", frame_read)
        cv2.waitKey(1)
        input("next")
    curFrame+=1


cap.release()
