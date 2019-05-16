# -*- coding: utf-8 -*-
"""
Created on Fri Jul 28 14:23:25 2017

@author: user
"""

# USAGE
# python motion_detector.py
# python motion_detector.py --video videos/example_01.mp4

# import the necessary packages
import argparse
import datetime
import imutils
import time
import cv2
import math
import numpy as np
from collections import deque 
import matplotlib.pyplot as plt
import matplotlib
#from skvideo.io import VideoWriter
from itertools import product
from bisect import bisect_left

ap = argparse.ArgumentParser()
ap.add_argument("-v", "--video", help="path to the video file")
ap.add_argument("-a", "--min-area", type=int, default=1000, help="minimum area size")
ap.add_argument("-b", "--buffer", type=int, default=256, help="max buffer size")
args = vars(ap.parse_args())
pts = deque(maxlen=args["buffer"])

Tags = []
const_dist = 5

File_name = "M1_sep20_0"
filename = "C:/Users/user/Documents/omid/RFID_grid_tracking/data/rerts_vid_pic_tex/vid"+File_name
with open("C:/Users/user/Documents/omid/RFID_grid_tracking/data/rerts_vid_pic_tex/RTS_test_"+File_name+".txt","r") as f:
    T0 = f.readline()
    #T0 = T0 [15:len(T0)-2]
    for line in f:
        f_contents = f.readline ()
        Tag = str(f_contents [1:19]).replace(", ","")
        #Tag = int(Tag)%10000
        #Tag = str (Tag)
        Tags.append (Tag)
    Tags = set (Tags)
    Tags = list(Tags)
f.close()
for Tagg in Tags:
    with open("C:/Users/user/Documents/omid/RFID_grid_tracking/data/rerts_vid_pic_tex/RTS_test_"+File_name+"_post_"+Tagg+".txt", "w") as f_p:
        with open("C:/Users/user/Documents/omid/RFID_grid_tracking/data/rerts_vid_pic_tex/RTS_test_"+File_name+".txt" , "r") as f:
            for line in iter(f):
                Tag = str(line [1:19]).replace(", ","") 
                #Tag = int (Tag)%10000
                #Tag = str (Tag)
                line = Tag + line [20:len(line)]
                if (Tagg == Tag):
                    f_p.write (line)
        f.close()
    f_p.close()


XX = []
YY = []
T = []
for Tagg in Tags:
    with open ("RTS_test_post_"+Tagg+"_VD.txt", "w") as f_VD:
        with open ("C:/Users/user/Documents/omid/RFID_grid_tracking/data/rerts_vid_pic_tex/RTS_test_"+File_name+"_post_"+Tagg+".txt", "r") as f_p:
            for i,line in enumerate(f_p):
                #print (i, line)
                if i == 0:
                    line_0 = line
                    Time_0 = line [15:len(line_0)-2]
                     
                Y0 = int(line_0 [11])
                X0 = int(line_0 [13])
                line_0 = line
                
                Time_1 = line [15:len(line)-2]
                Y1 = int(line [11])
                X1 = int(line [13])
                XX.append (Y1) 
                YY.append (X1)
                T.append (float(Time_1[6:13]))
                d = math.sqrt ((X1-X0)**2 + (Y1-Y0)**2)*int(const_dist)
                if (i > 0):
                    v = d/(float(Time_1)-float(Time_0))
                    f_VD.write (str(d)+" "+str(v)+"\n")
                #print(d)

camera1 = cv2.VideoCapture("C:/Users/user/Documents/omid/RFID_grid_tracking/data/rerts_vid_pic_tex/mouse_cage_tacking_vid_M1_sep20_background_0.h264")                  
firstFrame = None
#firstFrame = cv2.imread ("C:/Users/user/Documents/omid/RFID_grid_tracking/data/rsz_mouse_cage_tacking_pic_m3_1.jpg")


camera = cv2.VideoCapture("C:/Users/user/Documents/omid/RFID_grid_tracking/data/mouse_cage_tacking_vid_"+File_name+".h264")
#fourcc = cv2.VideoWriter_fourcc(*'mp4v')
#CODEC = cv2.CV_FOURCC('P','I','M','1') # MPEG-1
#CODEC = cv2.CV_FOURCC('D','I','V','X') # MPEG-4 = MPEG-1
#out = cv2.VideoWriter("C:/Users/user/Documents/omid/RFID_grid_tracking/data/mouse_cage_tacking_vid_"+File_name+".mp4", fourcc, 20.0, (640,480))
for i in range(10):
    (_,firstFrame) = camera1.read()
firstFrame = cv2.resize(firstFrame,(500,400))
firstFrame = cv2.cvtColor(firstFrame, cv2.COLOR_BGR2GRAY)
firstFrame = cv2.GaussianBlur(firstFrame, (31,31),10)
#firstFrame = np.ones((400,500),dtype="uint8")*255
Y = np.shape (firstFrame)[0]
X = np.shape (firstFrame)[1]
R_Y = Y/3
R_X = X/6
cage_X = 280
cage_Y = 180
pix_X = cage_X / X
pix_Y = cage_Y / Y

R_pos = {11:(R_X/2,R_Y/2),12:(R_X*1.5,R_Y/2),13:(R_X*2.5,R_Y/2),14:(R_X*3.5,R_Y/2),15:(R_X*4.5,R_Y/2),16:(R_X*5.5,R_Y/2),
         21:(R_X/2,R_Y*1.5),22:(R_X*1.5,R_Y*1.5),23:(R_X*2.5,R_Y*1.5),24:(R_X*3.5,R_Y*1.5),25:(R_X*4.5,R_Y*1.5),26:(R_X*5.5,R_Y*1.5),
         31:(R_X/2,R_Y*2.5),32:(R_X*1.5,R_Y*2.5),33:(R_X*2.5,R_Y*2.5),34:(R_X*3.5,R_Y*2.5),35:(R_X*4.5,R_Y*2.5),36:(R_X*5.5,R_Y*2.5)}
R = [11,12,13,14,15,16,21,22,23,24,25,26,31,32,33,34,35,36]

Pos_deq = deque (maxlen = len ( XX ) )
T_deq = deque (maxlen = len ( XX ) )
R_Pos_deq = deque (maxlen = len ( XX ) )
for i in range(1,len(XX)):
    Pos_deq.append ((XX[i],YY[i]))
    T_trunc = str(float(T[i])-float(T[1]))
    T_deq.append (T_trunc[0:5])
    T [i] = T[i]-T[0]
T.pop(0)
T.insert (0,0)
sum_d = []
Pos_dum = (0,0)
counter = 0
d = 0
sumd = 0
counter_2  = 0
frames = []
T_frame = 1/30
T_frames = []
evrey_frames = 100
video_1 = cv2.VideoWriter(filename+".avi", cv2.VideoWriter_fourcc(*'XVID'), 30,(X, Y))
video_2 = cv2.VideoWriter(filename+"gray.avi", cv2.VideoWriter_fourcc(*'XVID'), 30,(X, Y))
video_3 = cv2.VideoWriter(filename+"delta.avi", cv2.VideoWriter_fourcc(*'XVID'), 30,(X, Y))
while True:  
    
    
    if len(pts) >0:
        counter += 1
    (grabbed, frame) = camera.read()
    text = ""

    if not grabbed:
        break
    
    
    
    frame = imutils.resize (frame, width=500)
    gray = cv2.cvtColor (frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur (gray, (21, 21), 0)
      
    frameDelta = cv2.absdiff(firstFrame, gray)
    thresh = cv2.threshold(frameDelta,80, 225, cv2.THRESH_BINARY)[1]


    #thresh = cv2.dilate(thresh, None, 1)
    #thresh = cv2.erode(thresh, None, 50)
    (im,cnts,heir) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    for i in range(5):
            for j in range(2):
                cv2.line(frame,(int(X),int((j+1)*R_Y)),(0,int((j+1)*R_Y)), (0,0,0), 2)
                cv2.line(frame,(int((i+1)*R_X),int(Y)),(int((i+1)*R_X),0), (0,0,0), 2)
    for c in cnts:
        if cv2.contourArea(c) < args["min_area"]:
            continue
        counter_2 += 1
        (x, y, w, h) = cv2.boundingRect(c)
        pts.appendleft ((x + int(w/3), y + int(h/3)))
        dis = []
        for num , pos in enumerate (R,start=1):
            dis.append(math.sqrt ( ( R_pos [pos][0]-(x+int(w/2)) )**2 + ( R_pos [pos][1]-(y+int(h/2)) )**2 ))
        
        min_pos = min (dis)
        inx = dis.index (min_pos)
        sort_dis = sorted (dis)
        min1_inx = dis.index (sort_dis[0])
        min2_inx = dis.index (sort_dis[1])
        min1 = R [min1_inx]
        min2 = R [min2_inx]
        flag = False
        #print(inx)
        #R_pre = R [inx]
        
        if len(R_Pos_deq) == 0:
            R_Pos_deq.appendleft (str(min1))
        if Pos_deq [0]!=[] and Pos_deq [1]!=[]: 
                #T_deq.append([])            
            if str(Pos_deq[0][0])+str(Pos_deq[0][1]) == str(min1):
                flag  = True
                cv2.circle (frame, (int(R_pos[R [inx]][0]),int(R_pos[R [inx]][1])), 10, (255,100,90),10 )
                R_Pos_deq.appendleft (str(min1))
                #if Pos_deq [1] == Pos_deq [0]:
                    #print(True)
                    #print(Pos_deq [0])
                    #T_deq.append([])
                    #cv2.putText(frame, str(T_deq[0]).format(text), (10,20),
                                #cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)
                #else:
                    #cv2.putText(frame, str(T_deq[0]).format(text), (10,20),
                                #cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)                
                Pos_dum = Pos_deq[0] 
                
                #print(Pos_dum )
                Pos_deq.append([])
                T_deq.append([])
                #print(Pos_deq[0] )
            if str(Pos_deq[0][0])+str(Pos_deq[0][1]) == str(min2): 
                cv2.circle (frame, (int(R_pos[R [inx]][0]),int(R_pos[R [inx]][1])), 10, (255,100,90),10 )
                R_Pos_deq.appendleft (str(min2))
                #if Pos_deq [1] == Pos_deq [0]:
                    #T_deq.append([])
                    #Pos_deq.append([])
                    #cv2.putText(frame, str(T_deq[0]).format(text), (10,20),
                                #cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)
                #else:
                    #cv2.putText(frame, str(T_deq[0]).format(text), (10,20),
                                #cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)
                Pos_dum = Pos_deq[0]       
                
                #print(Pos_dum )
                Pos_deq.append([])
                T_deq.append([])
                #print(Pos_deq[0] )
            else:
                cv2.circle (frame, ( int(R_pos[int( R_Pos_deq [0]) ][0]),int(R_pos[int( R_Pos_deq [0]) ][1]) ), 3, (0,255,0),10 )
                #cv2.putText(frame, str(T_deq[0]).format(text), (10,20),
                            #cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2) 
                            
        for i in range (1,len(R_Pos_deq)):
            if R_Pos_deq[i-1] is None and R_Pos_deq[i] is None:
                continue
            
            cv2.line (frame, ( int(R_pos[int( R_Pos_deq [i-1]) ][0]),int(R_pos[int( R_Pos_deq [i-1]) ][1]) ),
                      ( int(R_pos[int( R_Pos_deq [i]) ][0]),int(R_pos[int( R_Pos_deq [i]) ][1]) ), (255,0,0), 5)
        
            #cv2.line (frame, )
        #if len (R_Pos_deq) == 1:
            #cv2.circle (frame, (int(R_pos[R [inx]][0]),int(R_pos[R [inx]][1])), 10, (255,100,90),5 )
        #d = []
        for k in range (1,len (R_Pos_deq)):
            if pts[i - 1] is None:
                continue
            #cv2.line (frame)
        
        for i in np.arange(1, len(pts)):
            if pts[i - 1] is None or pts[i] is None:
                continue
            #thickness = int(np.sqrt(args["buffer"] / float(i + 1)) * 2.5)
            cv2.line(frame, pts[i - 1], pts[i], (140, 70, 100), 2)
        if counter_2 % evrey_frames == 0 and len(pts) > evrey_frames:
            X_pre = pts [0][0]
            Y_pre = pts [0][1]
            d =  math.sqrt ((float(pts [0][0]) - float(pts [evrey_frames][0]))**2 + (float(pts [0][1]) - float(pts [evrey_frames][1]))**2) 
            sumd += d 
            sum_d.append (sumd*(math.sqrt(pix_X**2+pix_Y**2))) 
            T_frames.append ( T_frame*counter )
            #print(sum_d)
            #counter_2 += 1
             #print(counter)
        
            
        
        
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        text = ""
        cv2.putText(frame, Tag[-2:].format(text), (x + int(w/2), y + int(h/2)),
        cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)
        #cv2.putText(frame, str(T[0]).format(text), (10,20),
        #cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)
      #cv2.putText(frame, " {} ".format(text), (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
	#cv2.putText(frame, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
		#(10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
 
    cv2.imshow("1", frame)
    cv2.imshow("Thresh", thresh)
    cv2.imshow("Frame Delta", frameDelta)
    key = cv2.waitKey(1) & 0xFF
    #time.sleep(0.01)
    if key == ord("q"):
        break
    video_1.write(frame)
    video_2.write(thresh)
    video_3.write(frameDelta)





camera.release()
camera1.release()
video_1.release()
video_2.release()
video_3.release()
cv2.destroyAllWindows()
d_XY = []
d_XY_sum = []
T_frames_inx = []
T_inx = []
t_dum = []
inx = []
inx_i = []
inx_j = []
T_len = len (T_frames)
#for i in range(T_len):
    #t_dum = (sorted(product(T_frames,T), key=lambda t: abs(t[0]-t[1]))[i])
    #T_frames_inx.append( T_frames.index (t_dum[0]) )
    #T_inx.append( T.index (t_dum[1]) )
    #T_frames.remove (t_dum[0])
    #T.remove (t_dum[1])
    #print(t_dum)
#t_dum = sorted (t_dum)   

for i in range(len(T)):
    for j in range(len(T_frames)):
        if abs(T[i] - T_frames[j]) < 0.9:
            inx_i.append (int(i))
            inx_j.append (int(j))

        
for i in range(1,len(XX)):
    
    d_XY.append (math.sqrt ( ( XX[i-1]-XX[i] )**2 + ( YY[i-1]-YY[i] )**2 ) * (cage_X/6**2+cage_Y/3**2)) 
    d_XY_sum.append ( sum(d_XY) )

xx = np.arange(0,counter_2,evrey_frames)
fig1 = plt.figure()
i_list = []
j_list = []
for j in inx_j:
    j_list.append (np.unique(sum_d[j]))
for i in inx_i[0:-1]:
    i_list.append (np.unique(d_XY_sum[i]))
#for i,XY_ij in enumerate(inx_i):  
plt.plot (i_list,j_list[0:-1],"*")
plt.plot ([0,3000],[0,3000])
plt.xlim ((0,3000))
plt.ylim ((0,3000))
fig1.savefig ("C:/Users/user/Documents/omid/RFID_grid_tracking/data/rerts_vid_pic_tex/RTS_test_bothTracking_every100frames"+File_name+".jpg", format='jpg', dpi=1000)
plt.close(fig1)

xx = np.arange(0,counter_2,evrey_frames)
fig2 = plt.figure()
plt.plot ([x/30 for x in xx[1:-1]],sum_d)
fig2.savefig ("C:/Users/user/Documents/omid/RFID_grid_tracking/data/rerts_vid_pic_tex/RTS_test_every100frames"+File_name+".jpg", format='jpg', dpi=1000)
plt.close(fig2)


