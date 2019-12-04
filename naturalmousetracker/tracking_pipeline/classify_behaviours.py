import json
import numpy as np
import math
import argparse
import pymysql
import getpass
import re



#Additional behaviours from Tony:

# Behaviours involving one mouse
# 1) Nesting/Untracked
# 2) Active in tracked area
# 3) Stationary in corner
# 4) Stationary against wall
# 5) Center region


# 8) Average speed #AFTER
# 9) Distance traveled #AFTER
# 10) Acceleration >>> Need more specific .. (average A, instantaneous A at frame of interest?)
# 11) only mouse (self) tracked


# 12) Self alone in nesting area

# Behaviours involving 2 mice
# 13) self tracked with one other mouse
# 14) self and 1 other mouse head to head ***dlc
# 15) Grooming *Difficult*
# 16) Self and 1 other in Nesting
# 17) self Following another mouse   ***dlc
# 18) self head to side of other mouse   ***dlc
# 19) self head to Agenovential of other mouse **dlc
# 20) two mice side by side contact **dlc
# 21) self Squeeze between wall and 1 other mouse
# 22) Fighting *Unsure* possibly easy given some intuition, but most likely difficult

#behaviours involving 3 or more mice
# 23) self squeeze between 2 other mice
# 24) self and 2 other in Nesting
# 25) Self tracked with 2 other mice

#Behaviours with > 3 mice:
# 26) self and 3 others in Nesting
# 27) Self tracked with 3 other mice

#Import questions
#When mouse A does a behaviour to Mouse B, is the behavioural data still valid if we dont know the true identity of B.
    #Essentiall we need to decide if (mouse290 approaches mouse376 == mouse290 approaches dummy) evaluates to True
#If we count them as equal, we have to tweak the output format because the "behaviour: tag_other_mouse" output will include dummy tags
#If we dont count them as equal, then we must throw out any multi mouse behaviour where any mouse is a dummy

# Is mouse orientation during approach considered? Is it still an approach if a mouse walks up to another one backwards
#(I know mice dont walk backwards, but sloppy deeplabcut labels could also cause)

#Indentities not currently tracked within group forming and leaving.




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


def saveData(arr, SQL, csv, table):
    # print('save', arr)
    for val in arr:
        if val != "\n":
            csv.write(str(val) + ',')
            if len(SQL[table]) > 0:
                SQL[table][len(SQL[table]) - 1].append(val)
            else:
                SQL[table].append([val])
        else:
            csv.write(str(val))
            SQL['main'].append([])
            SQL['behaviour'].append([])
            SQL['position'].append([])
            SQL['pose'].append([])


def run(dataDrive, dataPath, user, host, db, password):
    darkFile = open(dataDrive + dataPath + "/processed.json", "r")
    darkData = json.loads(darkFile.read())

    mouseDict = {} #Holds key=value pair in format Tag=List where every index is a frame
    lastFrameDict = {} # Holds key=value pairs in format Tag=last index of data from json file added
    for tag in darkData.keys():
        mouseDict.update({tag: []})
        lastFrameDict.update({tag: 0})

    totalFrames = max(map(lambda x: x[-1][3], darkData.values()))

    frameCount = 1
    while True:
        for (tag, datum) in darkData.items():
            if datum[-1][3] < frameCount:
                mouseDict[tag].append(None)
            else:
                for i in range(lastFrameDict[tag], len(datum)):
                    if datum[i][3] == frameCount:
                        if len(datum[i]) > 4:# if datum[row].length() > 4 what does that mean and why do we scale values
                            x, y, w, h = datum[i][0]*912/640,\
                                datum[i][1]*720/640,\
                                datum[i][4]*912/640,\
                                datum[i][5]*720/640  #darknet outputs square
                        else:
                            x, y, w, h = datum[i][0]*912/640,\
                                datum[i][1]*720/640, 0, 0
                        xmin, ymin, xmax, ymax = convertBack(
                            float(x), float(y), float(w), float(h))
                        # head_pos = (datum[i][6], datum[i][7])
                        # tail_pos = (datum[i][8], datum[i][9])
                        center = (float(x), float(y))
                        # pt1 = (xmin, ymin)
                        # pt2 = (xmax, ymax)
                        pos = [center, float(w), float(h)] # head_pos, #tail_pos]
                        mouseDict[tag].append(pos)
                        lastFrameDict[tag] =i
                        break
                    elif datum[i][3] > frameCount:
                        mouseDict[tag].append(None)
                        break
        frameCount += 1
        print(frameCount)
        if frameCount > totalFrames:
            break
    velocities = {}
    approaches = {}
    files = {}
    SQL = {}
    for tag in mouseDict.keys():
        velocities.update({tag: None})
        approaches.update({tag: []})
        files.update({tag: dataDrive + dataPath + "/classified_" + tag + ".csv"})
        SQL.update({tag: {'main': [], 'behaviour': [], 'position': [], 'pose': []}})
    twoGroupFormingFrames = []
    twoGroupLeavingFrames = []
    threeGroupFormingFrames = []
    threeGroupLeavingFrames = []
    lastGroup = set()
    date, timestamp = dataPath.split('_')
    db = pymysql.connect(host=host, user=user, db=db, password=password)
    cur = db.cursor()
    main_save_query = """INSERT INTO `MiceEvents` (`Tag`, `Date`, `Time`,
    `Behaviour`, `Position`, `Pose`) VALUES(%s,%s,%s,%s,%s,%s)"""
    behaviour_save_query = """INSERT INTO `Behaviours` (`Name`, `Others`,
        `Location`) VALUES(%s,%s,%s)"""
    position_save_query = """INSERT INTO `Positions` (`Center_x`, `Center_y`,
        `Width`, `Height`, `V_x`, `V_y`, `Speed`)
        VALUES(%s,%s,%s,%s,%s,%s,%s)"""
    pose_save_query = """INSERT INTO `Pose` (`Head_x`, `Head_y`,
        `Tail_x`, `Tail_y`, `LeftEar_x`, `LeftEar_y`,
        `RightEar_x`, `RightEar_y`) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"""
    for tag, name in files.items():
        files[tag] = open(name, 'w')
        files[tag].write("Tag,Date,Time,Behaviour,Others_Involved,Location,"
                            "Center_x,Center_y,Width,"
                            "Height,Head_x,Head_y,Tail_x,Tail_y,"
                            "L_Ear_x,L_Ear_y,R_Ear_x,R_Ear_y,"
                            "Velocity_x,Velocity_y,Speed,\n")

    for i in range(0, totalFrames): #Iterate over all frames

        group = set()
        print(i)
        for mouse, positions in mouseDict.items():
            behaviourAssigned = False
            saveData([mouse, date, timestamp + '-' + str(i).zfill(5)], SQL[mouse], files[mouse], 'main')
            if len(positions) <= i:
                saveData(['Nesting', '\n'], SQL[mouse], files[mouse], 'behaviour')
                break
            if i >= 1 and positions[i-1] is not None and positions[i] is not None: #If we have atleast 1 detection and it is not the first
                velocities.update({mouse:(positions[i][0][0] - positions[i-1][0][0],
                    positions[i][0][1] - positions[i-1][0][1])})
            else:
                velocities.update({mouse: None})
            for other, other_pos in mouseDict.items():
                if mouse != other:
                    if len(positions) <= i or len(other_pos) <= i:
                        continue
                    dist = distanceBetweenPos(positions[i], other_pos[i]) #distance between two mice
                    if dist and dist < group_radius:
                        group.add(mouse)
                        group.add(other)
                    elif dist and dist < social_radius and velocities[mouse] is not None:
                        dist_vector = (other_pos[i][0][0] - positions[i][0][0],
                            other_pos[i][0][1] - positions[i][0][1])
                        dot = dist_vector[0]*velocities[mouse][0] + dist_vector[1]*velocities[mouse][1]
                        det = dist_vector[0]*velocities[mouse][1] - dist_vector[1]*velocities[mouse][0]
                        angle = math.atan2(det, dot)*(180/np.pi)  # atan2(y, x) or atan2(sin, cos)
                        if abs(angle) < 20 and np.sqrt(velocities[mouse][1]**2 + velocities[mouse][0]**2) > velocity_thresh:
                            if len(approaches[mouse]) == 0 or  approaches[mouse][-1][0] < i -10:
                                approaches[mouse].append((i, other))
                                behaviourAssigned = True
                                saveData(['Approaching', other],SQL[mouse], files[mouse], 'behaviour')
            if mouse in group:
                behaviourAssigned = True
                if mouse not in lastGroup:
                    saveData(['GroupEntering'], SQL[mouse], files[mouse], 'behaviour')
                else:
                    if velocities[mouse] and np.sqrt(velocities[mouse][1]**2 + velocities[mouse][0]**2) > velocity_thresh:
                        saveData(['Grouping'], SQL[mouse], files[mouse], 'behaviour')
                    else:
                        saveData(['Nesting'], SQL[mouse], files[mouse], 'behaviour')
                writeStr = " "
                for other in group:
                    if other != mouse:
                        writeStr += other + ';'
                saveData([writeStr[:-1]], SQL[mouse], files[mouse], 'behaviour')
            else:
                if mouse in lastGroup:
                    saveData(['GroupLeaving'], SQL[mouse], files[mouse], 'behaviour')
                    behaviourAssigned = True
                    writeStr = " "
                    for other in lastGroup:
                        if other != mouse:
                            writeStr += other + ';'
                    saveData([writeStr[:-1]], SQL[mouse], files[mouse], 'behaviour')

            if not behaviourAssigned:
                if velocities[mouse] and np.sqrt(velocities[mouse][1]**2 + velocities[mouse][0]**2) > velocity_thresh:
                    saveData(["Exploring"], SQL[mouse], files[mouse], 'behaviour')
                elif positions[i] is None:
                    if (i > 5 and positions[i -5] is None) or (i < totalFrames - 6 and positions[i+5] is None):
                        saveData(["Nesting"], SQL[mouse], files[mouse], 'behaviour')
                    else:
                        saveData(["Untracked"], SQL[mouse], files[mouse], 'behaviour')
                else:
                    saveData(["Stationary"], SQL[mouse], files[mouse], 'behaviour')
                # No other mouse involved
                saveData(["NULL"], SQL[mouse], files[mouse], 'behaviour')

            if positions[i] is not None:
                x, y = positions[i][0]
                if x > 912*3/4 or x < 912*1/4:
                    if y > 720*3/4 or y < 720*1/4:
                        saveData(["Corner"], SQL[mouse], files[mouse], "behaviour")
                    else:
                        saveData(["Wall"], SQL[mouse], files[mouse], "behaviour")
                elif y > 912*3/4 or y < 912*1/4:
                    saveData(["Wall"], SQL[mouse], files[mouse], "behaviour")
                else:
                    saveData(["Center"], SQL[mouse], files[mouse], "behaviour")
                count = 0
                table = 'position'
                for aspect in positions[i]:
                    if count >= 4:
                        table = "pose"
                    if type(aspect).__name__ == 'tuple':
                        for num in aspect:
                            count += 1
                            saveData([float(re.sub('[^A-Za-z0-9,.]+', '', str(num)))], SQL[mouse], files[mouse], table)
                    else:
                        count += 1
                        saveData([float(re.sub('[^A-Za-z0-9,.]+', '', str(aspect)))], SQL[mouse], files[mouse], table)
                while count < 12:  # Number of potential positions (i.e head, tail)
                    if count >= 4:
                        table = "pose"
                    saveData([0], SQL[mouse], files[mouse], table)
                    count += 1
            else:
                # No Location
                saveData(["NULL"], SQL[mouse], files[mouse], "behaviour")
                table = 'position'
                count = 0
                while count < 12:  # Number of potential positions (i.e head, tail)
                    if count >= 4:
                        table = "pose"
                    saveData([0], SQL[mouse], files[mouse], table)
                    count += 1
            if velocities[mouse] is not None:
                x, y = velocities[mouse]
                speed = np.sqrt(x**2 + y**2)
                saveData([float(x), float(y), float(speed)], SQL[mouse], files[mouse], 'position')
            else:
                saveData([0, 0, 0], SQL[mouse], files[mouse], 'position')
            saveData(['\n'], SQL[mouse], files[mouse], '')

        if len(group) == 2 and len(lastGroup) < 2:
            twoGroupFormingFrames.append(i)
        if len(group) == 3 and len(lastGroup) < 3:
            threeGroupFormingFrames.append(i)
        if len(group) < 3 and len(lastGroup) == 3:
            threeGroupLeavingFrames.append(i)
        if len(group) < 2 and len(lastGroup) == 2:
            twoGroupLeavingFrames.append(i)
        lastGroup = group

    for file in files.values():
        file.close()
    for tag, data in SQL.items():
            for i in range(0, len(data['main']) -1):
                if i % 100 == 0:
                    print(i)
                try:
                    cur.execute(pose_save_query, data['pose'][i])
                    pose_id = cur.lastrowid
                    # print('pose done')
                    cur.execute(position_save_query, data['position'][i])
                    position_id = cur.lastrowid
                    # print('position done')
                    cur.execute(behaviour_save_query, data['behaviour'][i])
                    # print('behaviour done')
                    behaviour_id = cur.lastrowid
                    cur.execute(main_save_query, data['main'][i] + [behaviour_id, position_id, pose_id])
                except pymysql.Error as e:
                    pass
                    # print(str(e))
            db.commit()
    db.close()
    print("two - Entering:", len(twoGroupFormingFrames),  "- Leaving:",  len(twoGroupLeavingFrames))
    print("three - Entering:", len(threeGroupFormingFrames), "- Leaving:",  len(threeGroupLeavingFrames))
    print(approaches)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", "--name", help="Name of the frame folder/text file")
    ap.add_argument("-d", "--drive", help="Path to data")
    ap.add_argument("-f", "--frames", help="Include this argument if you have individual frame files")
    args = vars(ap.parse_args())
    dataPath = args.get("name")
    dataDrive = args.get("drive", "frameData")
    password = getpass.getpass(prompt="Please enter the password for the database")
    run(dataDrive, dataPath, "slavePi", "142.103.107.236", 'tracking_behaviour', password)
