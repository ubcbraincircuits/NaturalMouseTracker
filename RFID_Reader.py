from smbus import SMBus
import time
import RPi.GPIO as GPIO
import decimal
from random import shuffle
from picamera import PiCamera
from picamera.array import PiRGBArray
import argparse
import cv2

Trash_Data = [0,255,255,255,255,255,255,255,255,255,255,255]
ProT = [None]*18

readerMap = [
    (103, 170), (177, 160), (274, 145), (390, 140), (475, 138), (542, 145), #1-(1-6) [y-x]
    (105, 253), (183, 250), (278, 248), (393, 237), (487, 235), (550, 230), #2-(1-6) [y-x]
    (118, 330), (190, 336), (288, 332), (401, 326), (496, 320), (556, 305)  #3-(1-5) [y-x]
]

#Hex I2C Addresses of all ProTrinkets
ProT [0] = 0x11
ProT [1] = 0x12
ProT [2] = 0x13
ProT [3] = 0x14
ProT [4] = 0x15
ProT [5] = 0x16
ProT [6] = 0x31
ProT [7] = 0x32
ProT [8] = 0x33
ProT [9] = 0x34
ProT [10] = 0x35
ProT [11] = 0x36
ProT [12] = 0x51
ProT [13] = 0x52
ProT [14] = 0x53
ProT [15] = 0x54
ProT [16] = 0x55
ProT [17] = 0x56
ProT_Dic = {ProT[0]:"1-1",ProT[1]:"1-2",ProT[2]:"1-3",ProT[3]:"1-4",
            ProT[4]:"1-5",ProT[5]:"1-6", ProT[6]:"2-1",ProT[7]:"2-2",
            ProT[8]:"2-3",ProT[9]:"2-4",ProT[10]:"2-5",ProT[11]:"2-6",
            ProT[12]:"3-1",ProT[13]:"3-2",ProT[14]:"3-3",ProT[15]:"3-4",
            ProT[16]:"3-5",ProT[17]:"3-6"}
#Adapted from ENPH 479 report by Yuan Tian, Ziyue Hu, and Becky Lin
# Essentially, only readers at least 4 apart can be turned on simultaneously.
# From testing, this unfortnuately leaves the middle units without a pair.
#Mapping_Dic = { 0: [0, 4], 1: [1, 5], 2: [6, 10], 3:[7, 11],
                #4: [12, 16], 5: [13, 17], 6: [14], 7: [15],
                #8: [8], 9:[9], 10: [2], 11:[3]}
Mapping_Dic = { 0:[0,17]}
#ProT_arrange = [i for i in range(0,18)]
#ProT_arrange = [i for i in range(0,8)]
#ProT_arrange = [i for i in range(0,12)]
ProT_arrange = [0]

"""
Write a number over the I2C bus.
Used to get a reading from the tag reader into the
ProTrinket buffer.
"""
def writeNumber (value,address_1):
    try:
        #with SMBus(1) as bus:
        bus = SMBus(1)
        bus.write_byte_data (address_1,0,value)
    except IOError as e:
        print (e)
    return -1

"""
Gets the last full tag in the ProTrinket serial buffer.
Converts this into a readable string.
"""
def readNumber(address_1):
    number1 = []
    try:
        #with SMBus(1) as bus:
        bus = SMBus(1)
        flag = False
        for i in range (0, 16):
            if flag:
                number1.append(chr(bus.read_byte(address_1)))
            else:
                x = bus.read_byte(address_1)
                if x is 2:
                    flag = True

    except IOError as e:
        print (e)
    return number1,time.time()

"""
Scans all readers based on their position in the map.
If any mice detected, save their tag and position with the frame number.
"""
def scan(f = False, frame = 0):
    mice = []
    for i in ProT_arrange:
        Data = Trash_Data
        #time.sleep(0.01)

        for x in Mapping_Dic[i]:
            writeNumber(int(1), ProT[x])
        time.sleep (0.02)
        for x in Mapping_Dic[i]:
            [Data,Time] = readNumber (ProT[x])
            Time = time.time()
            #Data = number1
            if '\r' not in Data:
                Data = []
            if (Data != Trash_Data and Data != []):
                try:
                    number =  ''.join(Data)
                    #The tag is always 10 characters long
                    number = number[0:10]
                    mice.append((int(number, 16), x))
                    if f is not False:
                        f.write (str(int(number, 16))+";"+str(readerMap[x])+";"+str(frame)+"\n")
                except Exception as e:
                    print(str(e))
    return mice


def readTag(tagID):
    writeNumber(int(1), ProT[tagID])
    time.sleep (0.13)
    [Data,Time] = readNumber (ProT[tagID])
    number =  ''.join(Data)
    #The tag is always 10 characters long
    number = number[0:10]
    if number == '':
        return False
    try:
        return (int(number, 16), tagID)
    except Exception as e:
        return False

def record():
    with open ("RTS_test.txt" , "w") as f:
        #Set up the camera for constant exposure
        camera = PiCamera()
        camera.resolution = (640, 480)
        camera.framerate = 30
        camera.iso =600
        camera.exposure_mode="off"
        rawCapture = PiRGBArray(camera, size=(640, 480))

        time.sleep(0.25)
        firstFrame = cv2.imread("ref.jpg")
        firstFrame = cv2.cvtColor(firstFrame, cv2.COLOR_BGR2GRAY)
        #firstFrame = cv2.GaussianBlur(firstFrame, (21,21), 0)
        startUpIterations = 100
        diffFrameCount = 0
        frameCount = 0
        needPulse = False
        for rawFrame in camera.capture_continuous(rawCapture, format = "bgr", use_video_port=True):
            try:
                frameName = "tracking_system" + trialName + str(frameCount) + ".png"
                frameCount += 1
                frame = rawFrame.array
                rawFrame.truncate(0)
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                cv2.imshow("Mouse Tracking", gray)
                key = cv2.waitKey(1)& 0xFF
                cv2.imwrite("frameData/" + frameName, gray)
                mice = scan(f, frameName)
            except KeyboardInterrupt:
                break

if __name__=="__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-t", "--text", help="path to the text file")
    ap.add_argument("-n", "--name", default ="base_tracking", help="trial name")
    args = vars(ap.parse_args())

    if args.get("text", None) is not None:
        fileName = args.get('text')
        open(fileName, "w+").close()
    trialName = args.get("name")
    record()
