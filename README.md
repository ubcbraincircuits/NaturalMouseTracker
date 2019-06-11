# MouseTrackingSystem
A system for using RFID tags and computer vision to track multiple mouse movement within a small environment.

## RFID System
Uses 18 ProTrinkets to interface with their own ID-20LA RFID tag
reader, which then interface with the Raspberry Pi over I2C.
The tag readers are set up in a 3x6 grid, and cannot be used at the same time unless they are a minimum distance away, lest they interfere.

## Overhead Camera
Records data in discrete frames. When all mice are distinct from one another (far apart), then the RFID system is pulsed over each mouse's location. This serves as verification for object detection.

## YOLO
A object detection system using https://pjreddie.com/darknet/yolo/. Stands for "You Only Look Once" - this system is very fast and accurate, and only fails when mice climb completely atop one another, or are obscured from the camera's vision. The information from the object detection system feeds into the Mouse Trackers.

## Mouse Trackers
When the detection system sees as many objects are there are mice, then the system simply tracks based on Euclidean distance. Since the framerate is faster than the mouse movement, this is a reliable method for tracking all mice. When mice are lost, a mouse is removed from the main list and a "dummy mouse" is added in place - so, if two mice are lost, then they are replaced with dummy mice henceforth. Once the mice return, the RFID system is checked periodically. Once a reliable reading has been established, these dummy mice can be identifed, and the system returns to full accuracy.

### Sources
- https://github.com/Ebonclaw/Mouse-Wearable-Tech---RFID-and-Localization-Grid-Computer-Vision-Enhancement
- https://github.com/AlexeyAB/darknet
