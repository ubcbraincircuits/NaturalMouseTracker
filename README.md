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
When the detection system sees as many objects are there are mice, then the system simply tracks based on Euclidean distance, choosing the closest pairs of detections until all mice and detections are covered. Since the framerate is faster than the mouse movement, this is a reliable method for tracking all mice. When mice are lost, a mouse is removed from the main list and a "dummy mouse" is added in place - so, if two mice are lost, then they are replaced with dummy mice henceforth. Once the mice return, the RFID system is checked continuously. Once we have found a frame in which a mouse has been read by the RFID sensors, the dummy mice are classified and the system is retroactively corrected. In this way, even though we may not be certain of which mouse is which on every frame moving forwards in time, once the system has finished running, all mice movement will have been completely tracked.

## Handling Failure
Since object detection is not perfect, failure happens and identity swaps between mice do occur. This is handled with three methods:

### Preventative Destruction
If a mouse disappears near another mouse, it is possible that the tracking system will perform an identity swap once it reappears in a different location. Thus, if the centroid of one mouse is within a destruction radius of another, then it is also lost and replaced with a "dummy mouse"

### RFID Validation
If an identity swap occurs that is not handled by the preventative destruction method, then there must be countermeasures. Thus, if a mouse identified by the system as tracked walks over an RFID sensor and is shown to be a different tag, then its data must be removed up to the last validation point, i.e. the last point it was confirmed by an RFID sensor. 

### Bundle Averaging
When mice are sleeping and are bundled together, there may be no easy way to segment this bundle into distinct mice. However, since the movement during these periods is minimal, and the mice are not far apart, then the bundles can be averaged to provide the mice with an approximate position for these times.

By combining these methods, we can confirm no identity swaps and an 80%+ coverage rating for this system.

### Sources
- https://github.com/Ebonclaw/Mouse-Wearable-Tech---RFID-and-Localization-Grid-Computer-Vision-Enhancement - original inspiration
- https://github.com/AlexeyAB/darknet - object detection 
