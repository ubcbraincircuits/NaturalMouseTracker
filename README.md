# MouseTrackingSystem
A system for using RFID tags and computer vision to track multiple mouse movement within a small environment.

## RFID System
Uses 2 ProTrinkets to interface with their own ID-20LA RFID tag
reader, which then interface with the Raspberry Pi over I2C.
The tag readers are set up in opposite corners of the cage, to minimize electromagnetic interference. This system is constantly running in parallel with the Overhead Camera, recording each tag read with respect to frames of the video.

## Overhead Camera
Records data in discrete frames, converts to grayscale, and saves for use in the object detection system.

## YOLO
An object detection system trained in-house using https://pjreddie.com/darknet/yolo/. Stands for "You Only Look Once" - this system is very fast and accurate, and only fails when mice climb completely atop one another, or are obscured from the camera's vision. The information from the object detection system feeds into the Mouse Trackers.

## Mouse Trackers
When the detection system sees as many objects are there are mice, then the system simply tracks based on Euclidean distance. Since the framerate is faster than the mouse movement, this is a reliable method for tracking all mice. When mice are lost, a mouse is removed from the main list and a "dummy mouse" is added in place - so, if two mice are lost, then they are replaced with dummy mice henceforth. Once the mice return, the RFID system is checked continuously. Once we have found a frame in which a mouse has been read by the RFID sensors, the dummy mice are classified and the system is retroactively corrected. In this way, even though we may not be certain of which mouse is which on every frame moving forwards in time, once the system has finished running, all mice movement will have been completely tracked.

### Sources
- https://github.com/Ebonclaw/Mouse-Wearable-Tech---RFID-and-Localization-Grid-Computer-Vision-Enhancement
- https://github.com/AlexeyAB/darknet
