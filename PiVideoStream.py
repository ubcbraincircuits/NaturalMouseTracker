# import the necessary packages
"""
Slightly changed from the imutils package to accomodate this system.
Credit to the authors of imutils.
"""
#import gc
from picamera.array import PiRGBArray
import datetime
from time import sleep, time
from picamera import PiCamera
import signal
from multiprocessing import Process
from multiprocessing import JoinableQueue
from threading import Thread
from os import listdir
import numpy as np
import os
import sys
import cv2
import warnings

class PiVideoStream:
	def __init__(self, resolution=(912,720), framerate=15, trialName= "base"):
		# initialize the camera and stream
		signal.signal(signal.SIGINT, signal.SIG_IGN) ################### Catch keyboard interrupts and run save function
		self.camera = PiCamera()
		self.trialName = trialName
		self.camera.resolution = resolution
		resolution = self.camera.resolution
		self.camera.exposure_mode = "off"
		self.camera.color_effects = (128,128)
		self.camera.framerate = framerate
		self.lastTime = 0.0
		self.frameCount = 0
		self.time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
		self.folder = "/mnt/frameData/" + self.time
		try:
			os.rmdir(self.folder)
		except FileNotFoundError:
			pass
		os.mkdir(self.folder)
		'''
		except:
			print('file exists')
			onlyfiles = [f for f in listdir("/mnt/frameData/")]
			count=0
			for i in onlyfiles:     
				if i[:19] == datetime.datetime.now().strftime("%Y-%m-%d_%H-%M"):
					count=+1
				else:
					pass
				os.mkdir(self.folder+'_'+str(count))
                self.folder=self.folder+'_'+str(count)
               '''
#		self.camera.start_recording(self.folder + '/tracking_system' + self.trialName + ".h264", quality=1)
		self.rawCapture = PiRGBArray(self.camera, size=resolution)
		self.stream = self.camera.capture_continuous(self.rawCapture,
			format="bgr", use_video_port=True)
#		self.hdf5 = None
#		self.frameStore = None
		# initialize the frame and the variable used to indicate
		# if the thread should be stopped
		self.frame = None
		self.frames = JoinableQueue(maxsize = 75)
		self.stopped = False
	def start(self, goodEvent, badEvent):
		# start the thread to read frames from the video stream
		t = Thread(target=self.update, args=(goodEvent, badEvent))
		t.daemon = True
		t.start()
		self.worker = Process(target=self.save, args=())
		self.worker.daemon = True
		self.worker.start()
		self.worker1 = Process(target=self.save, args=())
		self.worker1.daemon = True
		self.worker1.start()
		self.worker2 = Process(target=self.save, args=())
		self.worker2.daemon = True
		self.worker2.start()
		print("started")
		return self
	def save(self):
		#Ignore keyboard interrupt, we want this to continue until done
		while True:
			frame, frameCount = self.frames.get()
			#gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
			frameName = 'tracking_system' + self.trialName + str(frameCount) + '.jpg'
			cv2.imwrite(self.folder + "/" + frameName, frame)
			if frameCount % 100 == 0:
				print("save", frameCount)
			del frame
			if frameCount % 500 == 0:
				os.system("echo 1 > /proc/sys/vm/drop_caches")
			self.frames.task_done()
	def update(self, goodEvent, badEvent):
		# keep looping infinitely until the thread is stopped
		"""
		while True:
			if self.camera.timestamp > self.lastTime:
				self.frameCount += 1
				selcf.lastTime = self.camera.timestamp
			sleep(0.02)
			if self.stopped:
				self.camera.stop_recording()
				return
		"""
		for f in self.stream:

			# grab the frame from the stream and clear the stream in
			# preparation for the next frame
			start = time()
			self.frame = f.array
			self.frameCount += 1
			if self.frameCount % 100 ==0:
				print(self.frameCount)
			self.rawCapture.truncate(0)
			self.frames.put((self.frame, self.frameCount))
			self.frame = None
			sleep(max(0.5/(self.camera.framerate) - time(), 0))
			if self.frames.full():
				self.worker.terminate()
				self.worker1.terminate()
				self.worker2.terminate()
				self.frames = JoinableQueue()
				self.frames.close()
				badEvent.set()
				print("fired event")
			if goodEvent.isSet() or badEvent.isSet():
				self.stream.close()
				self.rawCapture.close()
				self.camera.close()
				self.stop()
				gc.collect()
				return
	def read(self):
		# return the frame (number) most recently read
		return self.frameCount

	def stopHandler(self, signal, frame):
		print('interrupt', signal, frame)
		self.stop()

	def stop(self):
		# indicate that the thread should be stopped
		self.stopped = True
		sleep(1)
#		self.camera.stop_recording()
#		self.camera.close()
		self.frames.join()
#		self.hdf5.close()
#		os.system("sudo mv " + self.folder + "/mnt/frameData/" + self.time)
		print("done")
		sys.exit(0)

