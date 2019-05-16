from smbus2 import SMBusWrapper
import time
import RPi.GPIO as GPIO
import decimal
from random import shuffle
from picamera import PiCamera

camera = PiCamera()

Trash_Data = [0,255,255,255,255,255,255,255,255,255,255,255]
ProT = [None]*18

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
            ProT[4]:"1-5",ProT[5]:"1-6",ProT[6]:"2-1",ProT[7]:"2-2",
            ProT[8]:"2-3",ProT[9]:"2-4",ProT[10]:"2-5",ProT[11]:"2-6",
            ProT[12]:"3-1",ProT[13]:"3-2",ProT[14]:"3-3",ProT[15]:"3-4",
            ProT[16]:"3-5",ProT[17]:"3-6"}


ProT_arrange = [i for i in range(0,18)]
#ProT_arrange = [i for i in range(0,6)]
#ProT_arrange = [0,8,6,2,1,7]

def writeNumber (value,address_1):
    try:
        with SMBusWrapper(1) as bus:
            bus.write_byte_data (address_1,0,value)
    except IOError as e:
        print (e)
    return -1

def readNumber(address_1):
    number1 = [] 
    try:
        with SMBusWrapper(1) as bus:
            number1 = bus.read_i2c_block_data(address_1,0,12)
            time.time()
    except IOError as e:
        print (e)
    return number1,time.time()
var = int(1)


camera.capture ('/home/pi/Tracking_system/mouse_cage_tacking_pic_M1_Aug21.jpg')
time.sleep(15)
t0 = time.time()
t = time.time()
for j in range(10):
    camera.start_recording ('/home/pi/Tracking_system/mouse_cage_tacking_vid_M1_Aug21_+'j'+.h264')
    camera.resolution = (500,312)
    camera.framerate = 30
    with open ("RTS_test_M1_Aug21"+j+".txt" , "w") as f:
        f.write (str(t0)+"\n")
        while t-t0<500:
            t=time.time()
            for i in ProT_arrange:
                Data = Trash_Data
                #time.sleep(0.01)
                try:
                    with SMBusWrapper(1) as bus:
                        bus.write_byte_data (ProT[i],0,var)
                        time.sleep (0.123)
                        number1 = bus.read_i2c_block_data(ProT[i],0,12)
                except IOError as e:
                    print (e)
                #writeNumber (var,int(ProT[i]))
                #time.sleep (0.16)
                #[Data,Time] = readNumber (ProT[i])
                #time.sleep  (0.01)
                Time = time.time()
                Data = number1
                if (Data != Trash_Data and Data != []):
                    f.write (str(Data[len(Data)-5:len(Data)])+" "+ProT_Dic[ProT[i]]+" "+str(Time)+"\n")
                    print (ProT_Dic[ProT[i]])
                    print (Data,Time)
                    print

    camera.stop_recording()
