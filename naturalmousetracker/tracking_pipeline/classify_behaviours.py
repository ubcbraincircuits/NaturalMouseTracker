import json
import numpy as np
import math
import argparse
import pymysql
import getpass
import re
import mysql.connector



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


group_radius = 160
social_radius = 250
entranceX = 827
entranceY = 281
velocity_thresh = 10


def convertBack(x, y, w, h):
    xmin = int(round(x - (w / 2)))
    xmax = int(round(x + (w / 2)))
    ymin = int(round(y - (h / 2)))
    ymax = int(round(y + (h / 2)))
    return xmin, ymin, xmax, ymax

def getHeadVector(poseData):
    nose     = poseData[0]
    head     = poseData[1]
    neck     = poseData[4]
    midspine = poseData[5]
    options = ((neck, head), (midspine, head),
    (head, nose), (neck, nose), (midspine, nose), (midspine, neck))
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
def getTailVector(poseData):
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

#
# def pointInTriangle(triangle, point):
#     # print("Point in triangle")
#     p0, p1, p2 = triangle
#     px, py = point
#     Area = 0.5 *(-p1[1]*p2[0] + p0[1]*(-p1[1] + p2[0]) + p0[0]*(p1[1] - p2[1]) + p1[1]*p2[1]);
#     s = 1/(2*Area)*(p0[1]*p2[0] - p0[0]*p2[1] + (p2[1] - p0[1])*px + (p0[0] - p2[0])*py);
#     t = 1/(2*Area)*(p0[0]*p1[1] - p0[1]*p1[1] + (p0[1] - p1[1])*px + (p1[1] - p0[0])*py);
#     return (s > 0 and t > 0 and 1-s-t > 0)

def triangle_area(tri): # tri = (0,0), (0,0), (0,0)
    x1, y1, x2, y2, x3, y3 = tri[0][0], tri[0][1], tri[1][0], tri[1][1], tri[2][0], tri[2][1]
    return abs(0.5 * (((x2-x1)*(y3-y1))-((x3-x1)*(y2-y1))))

def pointInTriangle(triangle, point):
    p = point
    p0, p1, p2 = triangle

    t1 = (point, p0, p1)
    t2 = (point, p1, p2)
    t3 = (point, p0, p2)

    a_total = triangle_area(triangle)
    a1 = triangle_area(t1)
    a2 = triangle_area(t2)
    a3 = triangle_area(t3)

    return (a_total == (a1 + a2 + a3))





def saveData(arr, SQL, csv, table):
    # Save to both the CSV files and the array of data to be saved to the database at once.
    # print('save', arr)
    for val in arr:
        if val != "\n":
            csv.write(str(val) + ',')
            if len(SQL[table]) > 0:
                SQL[table][len(SQL[table]) - 1].append(val)
            else:
                SQL[table].append([val])
        else:
            # New Lines mark the end of frames
            csv.write(str(val))
            SQL['main'].append([])
            SQL['behaviour'].append([])
            SQL['position'].append([])
            SQL['pose'].append([])





def run(dataDrive, dataPath, user, host, db, password):
    darkFile = open(dataDrive + dataPath + "/processed_ht.json", "r")
    darkData = json.loads(darkFile.read())

    mouseDict = {} #Holds key=value pair in format Tag=List where every index is a frame
    lastFrameDict = {} # Holds key=value pairs in format Tag=last index of data from json file added n
    for tag in darkData.keys():
        mouseDict.update({tag: []})
        lastFrameDict.update({tag: 0})

    totalFrames = max(map(lambda x: x[-1][3] if len(x) > 0 else 0, darkData.values()))

    frameCount = 1
    """
    This section simply concatenates the positions into arrays of positions for each mouse,
    for every frame. For frames where they are not tracked we append "None" instead.
    This lets us iterate through the data as if it was a video, frame by frame.
    Example:
    Say we had two mice we were tracking, Mouse 1 and 2.
    1 was tracked for frames 1, 2, 3, 5, 6, and 7.
    2 was tracked for frames 0, 1, 2, 3, 4, 9, and 10.
    The resulting mouseDict would look like this:
    {
        1: [None, posn, posn, posn, None, posn, posn, posn, None, None, None],
        2: [posn, posn, posn, posn, posn, None, None, None, None, posn, posn]
    }
    A position looks like [x, y, w, h, <POSE DATA>]
    We use the lastFrameDict when iterating through as we know the JSON file is sorted, so
    we can build these arrays in one pass, an O(n) operation.
    """
    while True:
        for (tag, datum) in darkData.items():
            if datum[-1][3] < frameCount:
                mouseDict[tag].append(None)
            else:
                for i in range(lastFrameDict[tag], len(datum)):
                    if datum[i][3] == frameCount:
                        if len(datum[i]) > 4:
                            x, y, w, h = datum[i][0]*912/640,\
                                datum[i][1]*720/640,\
                                datum[i][4]*912/640,\
                                datum[i][5]*720/640  # Darknet saves the images to a 640x640 square
                                # We resize these back to the original frame size.
                            # mask = datum[i][2].values()
                        else:
                            x, y, w, h = datum[i][0]*912/640,\
                                datum[i][1]*720/640, 0, 0
                            # mask = []
                        xmin, ymin, xmax, ymax = convertBack(
                            float(x), float(y), float(w), float(h))
                        poseParts = []
                        # Nose, head, left ear, right ear, neck,
                        # midspine, pelvis, tail
                        j = 6
                        while j < len(datum[i]) - 1:
                            if datum[i][j] is not None:
                                poseParts.append((float(datum[i][j]),\
                                    float(datum[i][j+1])))
                            else:
                                poseParts.append((None, None))
                            j += 2
                        center = (float(x), float(y))
                        # pt1 = (xmin, ymin)
                        # pt2 = (xmax, ymax)
                        pos = [center, float(w), float(h), poseParts]
                        mouseDict[tag].append(pos)
                        lastFrameDict[tag] =i
                        break
                    elif datum[i][3] > frameCount:
                        mouseDict[tag].append(None)
                        break
        frameCount += 1
        # print(frameCount)
        if frameCount >= totalFrames:
            break
    velocities = {}
    vectors = {}
    approaches = {}
    exitPos = {}
    entrancePos = {}
    files = {}
    SQL = {}
    """
    This is setting up the dictionaries of information
    we want to easily access in each loop: the CSV files
    we are writing to, the array of behaviours we save
    to the SQL database later, and the exit and entry positions
    for determining probablistic behaviours when mice are untracked.
    """
    for tag in mouseDict.keys():
        velocities.update({tag: None})
        approaches.update({tag: []})
        vectors.update({tag: {'head': None, 'tail':None, 'mid': None}})
        files.update({tag: dataDrive + dataPath + "/classified_" + tag + ".csv"})
        SQL.update({tag: {'main': [], 'behaviour': [], 'position': [], 'pose': []}})
        exitPos.update({tag: None})
        entrancePos.update({tag: None})
    twoGroupFormingFrames = []
    twoGroupLeavingFrames = []
    threeGroupFormingFrames = []
    threeGroupLeavingFrames = []
    lastGroup = set()
    date, timestamp = dataPath.split('_')
    print("trying to connect")
    try:
        db = mysql.connector.connect(host=host, user=user, db=db, password=password,
            auth_plugin="mysql_native_password")
        cur = db.cursor()
    except Exception as e:
        print(str(e))
        return
    main_save_query = """INSERT INTO `miceevents` (`Tag`, `Date`, `Time`,
    `Behaviour`, `Position`, `Pose`) VALUES(%s,%s,%s,%s,%s,%s)"""
    behaviour_save_query = """INSERT INTO `Behaviours` (`Name`, `Others`,
        `Location`) VALUES(%s,%s,%s)"""
    position_save_query = """INSERT INTO `positions` (`Center_x`, `Center_y`,
        `Width`, `Height`, `V_x`, `V_y`, `Speed`)
        VALUES(%s,%s,%s,%s,%s,%s,%s)"""
    pose_save_query = """INSERT INTO `poses` (`Nose_x`, `Nose_y`,
        `Head_x`, `Head_y`, `LeftEar_x`, `LeftEar_y`, `RightEar_x`, `RightEar_y`,
        `Neck_x`, `Neck_y`, `Midspine_x`, `Midspine_y`,
        `Pelvis_x`, `Pelvis_y`, `Tail_x`, `Tail_y`
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
    for tag, name in files.items():
        files[tag] = open(name, 'w')
        files[tag].write("Tag,Date,Time,Behaviour,Others_Involved,Location,"
                            "Center_x,Center_y,Width,"
                            "Height,Nose_x,Nose_y,Head_x,Head_y,"
                            "L_Ear_x,L_Ear_y,R_Ear_x,R_Ear_y,"
                            "Neck_x, Neck_y, Midspine_x, Midspine_y,"
                            "Pelvis_x, Pelvis_y, Tail_x, Tail_y"
                            "Velocity_x,Velocity_y,Speed,\n")

    for i in range(0, totalFrames): # Iterate over all frames

        group = set()
        # print(i)
        # Assign a behaviour for each mouse.
        for mouse, positions in mouseDict.items():
            behaviourAssigned = False
            saveData([mouse, date, timestamp + '-' + str(i).zfill(5)], SQL[mouse], files[mouse], 'main')
            if len(positions) <= i:
                # An edge case. Should not get to this point, but if so, assume mouse is nesting.
                saveData(['Nesting', '\n'], SQL[mouse], files[mouse], 'behaviour')
                break
            if i >= 1 and positions[i-1] is not None and positions[i] is not None:
                # If we can calculate a velocity, do so and save it.
                velocities.update({mouse:(positions[i][0][0] - positions[i-1][0][0],
                    positions[i][0][1] - positions[i-1][0][1])})
            else:
                velocities.update({mouse: None})
            # Are these mice grouping together with others?
            for other, other_pos in mouseDict.items():
                if mouse != other:
                    if len(positions) <= i or len(other_pos) <= i:
                        continue
                    dist = distanceBetweenPos(positions[i], other_pos[i])
                    # Add mice to the 'group' if they are close enough together
                    if dist and dist < social_radius and velocities[mouse] is not None:
                        # If they are not grouping, they may be approaching. Determine
                        # if their direction of motion is in the direction of another mouse.
                        # Add Head/tail information to this later.
                        poseData = positions[i][3]
                        m_v = getMidVector(poseData)
                        h_v = getHeadVector(poseData)
                        t_v = getTailVector(poseData)
                        otherPoseData = other_pos[i][3]
                        o_m_v = getMidVector(otherPoseData)
                        o_h_v = getHeadVector(otherPoseData)
                        o_t_v = getTailVector(otherPoseData)
                        if h_v[0] is not None:
                            fov = getFOV(h_v)
                            if o_h_v[0] is not None and\
                                pointInTriangle(fov, o_h_v[0][1]):
                                o_fov = getFOV(o_h_v)
                                if pointInTriangle(o_fov, h_v[0][1]):
                                    saveData(['HeadToHead', other], SQL[mouse], files[mouse], 'behaviour')
                                    behaviourAssigned = True
                            elif o_t_v[0] is not None and pointInTriangle(fov, o_t_v[0][1]):
                                print(mouse, other, o_t_v, fov)
                                saveData(['HeadToAgenovenital', other], SQL[mouse], files[mouse], 'behaviour')
                                print("Agenovential")
                                print("type: ", type(o_t_v))
                                print("otv =", o_t_v[0][1])
                                print("HeadV=", h_v)
                                behaviourAssigned = True
                            # elif any(pointInTriangle(fov, x[0]) for x in positions[i][4]):
                            #     saveData(['HeadToSide', other], SQL[mouse], files[mouse], 'behaviour')
                            #     behaviourAssigned = True
                            # print("here")
                        if not behaviourAssigned:
                            dist_vector = (other_pos[i][0][0] - positions[i][0][0],
                                other_pos[i][0][1] - positions[i][0][1])
                            dot = dist_vector[0]*velocities[mouse][0] + dist_vector[1]*velocities[mouse][1]
                            det = dist_vector[0]*velocities[mouse][1] - dist_vector[1]*velocities[mouse][0]
                            angle = math.atan2(det, dot)*(180/np.pi)  # atan2(y, x) or atan2(sin, cos)
                            if abs(angle) < 20 and np.sqrt(velocities[mouse][1]**2 + velocities[mouse][0]**2) > velocity_thresh:
                                if len(approaches[mouse]) == 0 or  approaches[mouse][-1][0] < i -10:
                                    approaches[mouse].append((i, other))
                                    behaviourAssigned = True
                                    # If they are approaching, that is their behaviour on this frame.
                                    saveData(['Approaching', other],SQL[mouse], files[mouse], 'behaviour')
                    if dist and dist < group_radius:
                        group.add(mouse)
                        group.add(other)


            if mouse in group and not behaviourAssigned:
                behaviourAssigned = True
                if mouse not in lastGroup:
                    #If they entered this group and they were not in a group before
                    saveData(['GroupEntering'], SQL[mouse], files[mouse], 'behaviour')
                else:
                    if velocities[mouse] and np.sqrt(velocities[mouse][1]**2 + velocities[mouse][0]**2) > velocity_thresh:
                        #In a group, moving
                        saveData(['Grouping'], SQL[mouse], files[mouse], 'behaviour')
                    else:
                        #In a group, not moving
                        saveData(['Clumping'], SQL[mouse], files[mouse], 'behaviour')
                # Adding "Others Involved"
                writeStr = " "
                for other in group:
                    if other != mouse:
                        writeStr += other + ';'
                saveData([writeStr[:-1]], SQL[mouse], files[mouse], 'behaviour')
            elif mouse not in group and not behaviourAssigned:
                if mouse in lastGroup:
                    #If they were in a group before and are no longer in one
                    saveData(['GroupLeaving'], SQL[mouse], files[mouse], 'behaviour')
                    behaviourAssigned = True
                    writeStr = " "
                    #Adding "Others Involved"
                    for other in lastGroup:
                        if other != mouse:
                            writeStr += other + ';'
                    saveData([writeStr[:-1]], SQL[mouse], files[mouse], 'behaviour')

            if positions[i] is not None:
                # Reset exit and entry points when mouse is tracked
                exitPos[tag] = None
                entrancePos[tag] = None
            else:
                #Assign entry and exit points
                if exitPos[tag] is None:
                    j = i
                    while j >= 0 and positions[j] is None:
                        j -= 1
                    if positions[j] is not None:
                        exitPos[tag] = (j, positions[j][0])
                    else:
                        exitPos[tag] = (0, [0,0])
                if entrancePos[tag] is None:
                    j = i
                    while j < len(positions) - 1 and positions[j] is None:
                        j += 1
                    if positions[j] is not None:
                        entrancePos[tag] = (j, positions[j][0])
                    else:
                        exitPos[tag] = (totalFrames, [0,0])

            if not behaviourAssigned:
                if velocities[mouse] and np.sqrt(velocities[mouse][1]**2 + velocities[mouse][0]**2) > velocity_thresh:
                    # If they are moving and are alone, they are exploring.
                    saveData(["Exploring"], SQL[mouse], files[mouse], 'behaviour')
                elif positions[i] is None:
                    # We have no data for this section.
                    if entrancePos[tag] and exitPos[tag] and entrancePos[tag][0] - exitPos[tag][0] >= 60:
                        # The period of unknown data is longer than 60 frames.
                        # Mice are either Nesting or Clumping. If they are in the
                        # entrance to the nesting area on either their disappearing
                        # or reappearing position, assume they were nesting.
                        if exitPos[tag][1][0] > entranceX and exitPos[tag][1][1] > entranceY:
                            saveData(["Nesting"], SQL[mouse], files[mouse], 'behaviour')
                        elif entrancePos[tag][1][0] > entranceX and entrancePos[tag][1][1] > entranceY:
                            saveData(["Nesting"], SQL[mouse], files[mouse], 'behaviour')
                        else:
                            saveData(["Clumping"], SQL[mouse], files[mouse], 'behaviour')

                    else:
                        saveData(["Untracked"], SQL[mouse], files[mouse], 'behaviour')
                else:
                    saveData(["Stationary"], SQL[mouse], files[mouse], 'behaviour')
                # No other mouse involved, write NULL to "Others Involved"
                saveData(["NULL"], SQL[mouse], files[mouse], 'behaviour')

            if positions[i] is not None:
                # Assign Locations to behaviours (In the corner? By the wall? etc.)
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
                saveData(positions[i][0], SQL[mouse], files[mouse], 'position')
                saveData(positions[i][1:3], SQL[mouse], files[mouse], 'position')
                # Save all the location and pose data with a simple regex.
                for aspect in positions[i][3]:
                    if type(aspect).__name__ == 'tuple':
                        for num in aspect:
                            count += 1
                            if num == None:
                                saveData([0.0], SQL[mouse], files[mouse], 'pose')
                            else:
                                saveData([float(re.sub('[^A-Za-z0-9,.]+', '', str(num)))], SQL[mouse], files[mouse], 'pose')
                    else:
                        count += 1
                        if aspect == None:
                            saveData([0.0], SQL[mouse], files[mouse], 'pose')
                        else:
                            saveData([float(re.sub('[^A-Za-z0-9,.]+', '', str(aspect)))], SQL[mouse], files[mouse], 'pose')
                while count < 16:  # Number of potential positions (i.e head, tail)
                    saveData([0.0], SQL[mouse], files[mouse], 'pose')
                    count += 1
            else:
                # No Location as there was no position
                saveData(["NULL"], SQL[mouse], files[mouse], "behaviour")
                saveData([0, 0, 0, 0], SQL[mouse], files[mouse], 'position')
                table = 'position'
                count = 0
                while count < 16:  # Number of potential positions (i.e head, tail)
                    saveData([0.0], SQL[mouse], files[mouse], 'pose')
                    count += 1
            if velocities[mouse] is not None:
                # Save velocity if it is known
                x, y = velocities[mouse]
                speed = np.sqrt(x**2 + y**2)
                saveData([float(x), float(y), float(speed)], SQL[mouse], files[mouse], 'position')
            else:
                # 0 Otherwise
                saveData([0, 0, 0], SQL[mouse], files[mouse], 'position')
            # Mark the end of this frame with a new line.
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
    print("Saving...")
    for file in files.values():
        file.close()
    # Save all the info to SQL
    for tag, data in SQL.items():
            for i in range(0, len(data['main']) -1):
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
                except Exception as e:
                    print(str(e))
            db.commit()
    db.close()
    print("Done!")

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
