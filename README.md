# MouseTrackingSystem
A system for using RFID tags and a overhead camera to track mouse movement.

Base CV code modified from https://github.com/Ebonclaw/Mouse-Wearable-Tech---RFID-and-Localization-Grid-Computer-Vision-Enhancement

## RFID System
Uses 18 ProTrinkets to interface with their own ID-20LA RFID tag
reader, which then interface with the Raspberry Pi over I2C.
The tag readers are set up in a 3x6 grid, and cannot be used at the same time unless they are a minimum distance away, lest they interfere.

## Overhead Camera
Records data in discrete frames. When all mice are distinct from one another (far apart), then the RFID system is pulsed over each mouse's location. This serves as verification for:

## YOLO
A object detection system using https://pjreddie.com/darknet/yolo/. Stands for "You Only Look Once" - this system is very fast and accurate, and only fails when mice climb completely atop one another, or are obscured from the camera's vision. Main code for this system has been imported from https://github.com/AlexeyAB/darknet, and the API has been used to complete the tracking.
