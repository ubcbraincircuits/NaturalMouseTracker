# MouseTrackingSystem
A system for using RFID tags and a overhead camera to track mouse movement.

To some degree, adapted from https://github.com/Ebonclaw/Mouse-Wearable-Tech---RFID-and-Localization-Grid-Computer-Vision-Enhancement

##RFID System
Uses 18 ProTrinkets to interface with their own ID-20LA RFID tag
reader, which then interface with the Raspberry Pi over I2C.
The tag readers are set up in a 3x6 grid, and cannot be used at the same time unless they are a minimum distance away, lest they interfere.

##Overhead Camera
Tracks mice through motion detection, and handles overlapping by referencing the RFID system upon the end of an overlap.
