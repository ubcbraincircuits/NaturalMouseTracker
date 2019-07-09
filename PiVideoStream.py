# import the necessary packages
"""
Slightly changed from the imutils package to accomodate this system.
Credit to the authors of imutils.
"""
from picamera.array import PiRGBArray
from picamera import PiCamera
from threading import Thread
from queue import Queue
import cv2

class PiVideoStream:
	def __init__(self, resolution=(320, 240), framerate=80, trialName= "base"):
		# initialize the camera and stream
		self.camera = PiCamera()
		self.trialName = trialName
		self.camera.resolution = resolution
		self.camera.framerate = framerate
		self.camera.exposure_mode="off"
		self.camera.saturation = -100
		self.rawCapture = PiRGBArray(self.camera, size=resolution)
		self.stream = self.camera.capture_continuous(self.rawCapture,
			format="bgr", use_video_port=True)

		# initialize the frame and the variable used to indicate
		# if the thread should be stopped
		self.frame = None
		self.frames = Queue(maxsize = 0)
		self.frameCount = 0
		self.stopped = False

	def start(self):
		# start the thread to read frames from the video stream
		t = Thread(target=self.update, args=())
		t.daemon = True
		t.start()
		self.worker = Thread(target=self.save, args=())
		self.worker.daemon = True
		self.worker.start()
		return self

	def save(self):
		while True:
                        frame, frameCount = self.frames.get()
                        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                        frameName = 'tracking_system' + self.trialName + str(frameCount) + '.jpg'
                        cv2.imwrite("frameData/" + frameName, gray)
                        self.frames.task_done()
                        
	def update(self):
		# keep looping infinitely until the thread is stopped
		for f in self.stream:
			# grab the frame from the stream and clear the stream in
			# preparation for the next frame
			self.frame = f.array
			self.frameCount += 1
			self.frames.put((self.frame, self.frameCount))
			self.rawCapture.truncate(0)

			# if the thread indicator variable is set, stop the thread
			# and resource camera resources
			if self.stopped:
				self.stream.close()
				self.rawCapture.close()
				self.camera.close()
				return

	def read(self):
		# return the frame (number) most recently read
		return (self.frame, self.frameCount)

	def stop(self):
		# indicate that the thread should be stopped
		self.stopped = True
		self.frames.join()
		print("done")

