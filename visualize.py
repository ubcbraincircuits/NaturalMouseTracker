import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
import cv2
import json
from MouseTracker import MouseTracker
from time import sleep


darkFile = open("processed.json", "r")
darkData = json.loads(darkFile.read())

plt.show()
fig = plt.figure()
img = mpimg.imread("ref.jpg")
plt.imshow(img)
plt.axis((0, 640, 0, 480))
for datum in darkData.values():
    x = list(map(lambda l : int(l[0]*640/416), datum))
    y = list(map(lambda l : int(l[1]*640/416), datum))
    plt.plot(x, y)
plt.show()
trialName = "base_tracking"
frameCount = input("Input your desired validation frame number")
if int(frameCount) > -1:
    fig = plt.figure()
    frameName = "frameData/tracking_system" + trialName + str(frameCount) + ".png"
    img = cv2.imread(frameName)
    plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    for (tag, datum) in darkData.items():
        for position in datum:
            if position[2]==frameName:
                plt.text(position[0]*640/416, position[1]*480/416, tag, color="r")
    plt.show()
