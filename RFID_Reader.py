from smbus import SMBus
import time
import RPi.GPIO as GPIO
import decimal
from random import shuffle
from picamera import PiCamera
from picamera.array import PiRGBArray
from PiVideoStream import PiVideoStream
import imutils
from imutils.video import FPS
import argparse
from RFIDTagReader import TagReader
import threading
from shutil import copyfile
import cv2

##readerMap = [
##    (103, 170), (177, 160), (274, 145), (390, 140), (475, 138), (542, 145), #1-(1-6) [y-x]
##    (105, 253), (183, 250), (278, 248), (393, 237), (487, 235), (550, 230), #2-(1-6) [y-x]
##    (118, 330), (190, 336), (288, 332), (401, 326), (496, 320), (556, 305)  #3-(1-5) [y-x]
##]
readerMap = [(103,310),(525, 120), (525, 310), (103, 120)]
#Hex I2C Addresses of all ProTrinkets
'''
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
'''
#ProT [13] = 0x52
#ProT [14] = 0x53
#ProT [15] = 0x54
#ProT [16] = 0x55
#ProT [17] = 0x56
#ProT_Dic = {ProT[0]:"1-1",ProT[1]:"1-2",ProT[2]:"1-3",ProT[3]:"1-4",
#            ProT[4]:"1-5",ProT[5]:"1-6", ProT[6]:"2-1",ProT[7]:"2-2",
#            ProT[8]:"2-3",ProT[9]:"2-4",ProT[10]:"2-5",ProT[11]:"2-6",
#            ProT[12]:"3-1",ProT[13]:"3-2",ProT[14]:"3-3",ProT[15]:"3-4",
#            ProT[16]:"3-5",ProT[17]:"3-6"}
#Adapted from ENPH 479 report by Yuan Tian, Ziyue Hu, and Becky Lin
# Essentially, only readers at least 4 apart can be turned on simultaneously.
# From testing, this unfortnuately leaves the middle units without a pair.
#Mapping_Dic = { 0: [0, 4], 1: [1, 5], 2: [6, 10], 3:[7, 11],
                #4: [12, 16], 5: [13, 17], 6: [14], 7: [15],
                #8: [8], 9:[9], 10: [2], 11:[3]}
#Mapping_Dic = { 0:[0,17]}
#ProT_arrange = [i for i in range(0,18)]
#ProT_arrange = [i for i in range(0,8)]
#ProT_arrange = [i for i in range(0,12)]
#ProT_arrange = [0]


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
frameCount = 0

def scan(reader, f, readerNum):
    global frameCount
    mice = []
    try:
        Data = reader.readTag()
        if f is not False and Data > 0:
            frameName = 'tracking_system' + trialName + str(frameCount) + '.png'
            f.write (str(Data)+";"+str(readerMap[readerNum])+";"+frameName+"\n")
    finally:
        return

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
    global frameCount
    RFID_serialPort = '/dev/ttyUSB0'
    #RFID_serialPort = '/dev/serial0'
    #RFID_serialPort='/dev/cu.usbserial-AL00ES9A'
    RFID_kind = 'ID'
    """
    Setting to timeout to None means we don't return till we have a tag.
    If a timeout is set and no tag is found, 0 is returned.
    """
    RFID_timeout = 0.015
    RFID_doCheckSum = True
    reader0 = TagReader ('/dev/ttyUSB1', RFID_doCheckSum, timeOutSecs = None, kind=RFID_kind)
    reader1 = TagReader ('/dev/ttyUSB2', RFID_doCheckSum, timeOutSecs = None, kind=RFID_kind)
    reader2 = TagReader ('/dev/ttyUSB3', RFID_doCheckSum, timeOutSecs = None, kind=RFID_kind)
    reader3 = TagReader ('/dev/ttyUSB0', RFID_doCheckSum, timeOutSecs = None, kind=RFID_kind)
    vs = PiVideoStream(resolution=(640,480), trialName=trialName).start()
    with open (vs.folder + "/RTS_test.txt" , "w") as f:
        time.sleep(0.25)
        needPulse = False
        time.sleep(2)
        startTime = time.time()
        thread0 = threading.Thread(target=scan, daemon= True, args=(reader0, f, 0))
        thread1 = threading.Thread(target=scan, daemon= True, args=(reader1, f, 1))
        thread2 = threading.Thread(target=scan, daemon= True, args=(reader2, f, 2))
        thread3 = threading.Thread(target=scan, daemon= True, args=(reader3, f, 3))
        thread0.start()
        thread1.start()
        thread2.start()
        thread3.start()
        while True:
            try:
                time.sleep(0.03)
                frame, frameCount = vs.read()
                #cv2.imshow("Mouse Tracking", frame)
                key = cv2.waitKey(1)& 0xFF
                if not thread0.is_alive():
                    thread0 = threading.Thread(target=scan, daemon= True, args=(reader0, f, 0))
                    thread0.start()
                if not thread1.is_alive():
                    thread1 = threading.Thread(target=scan, daemon= True, args=(reader1, f, 1))
                    thread1.start()
                if not thread2.is_alive():
                    thread2 = threading.Thread(target=scan, daemon= True, args=(reader2, f, 2))
                    thread2.start()
                if not thread3.is_alive():
                    thread3 = threading.Thread(target=scan, daemon= True, args=(reader3, f, 3))
                    thread3.start()
            except KeyboardInterrupt:
               break
        cv2.destroyAllWindows()
        vs.stop()

if __name__=="__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-t", "--text", help="path to the text file")
    ap.add_argument("-n", "--name", default ="base_tracking", help="trial name")
    ap.add_argument("-c", "--count", default =1, help="initial count")
    args = vars(ap.parse_args())
    if args.get("text", None) is not None:
        fileName = args.get('text')
        open(fileName, "w+").close()
        copyfile('RTS_test.txt','/home/pi/Documents/MouseTrackingSystem/RTS_test.txt')
    trialName = args.get("name")
    frameCount = args.get("count")
    record()
