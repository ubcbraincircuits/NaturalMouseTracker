import io
import os
import datetime as dt
from threading import Thread, Lock
from collections import namedtuple
from math import sin, cos, pi
from time import sleep
from RFIDTagReader import TagReader

import picamera
from picamera import mmal, mmalobj as mo, PiCameraPortDisabled
from PIL import Image, ImageDraw


class ClockSplitter(mo.MMALPythonComponent):
    def __init__(self):
        super(ClockSplitter, self).__init__(name='py.clock', outputs=2)
        self.inputs[0].supported_formats = {mmal.MMAL_ENCODING_I420}
        self._lock = Lock()
        self._clock_image = None
        self._clock_thread = None
        self.seenTags = []
        self.pickup = None
        self.colorMap=[(0,),(85,),(170,),(255,)]
        RFID_kind = 'ID'
        self.time = dt.datetime.now().strftime("%Y-%m-%d_%H-%M")
        self.folder = "/mnt/frameData/" + self.time + "/"
        try:
            os.rmdir(self.folder)
        except FileNotFoundError:
            pass
        os.mkdir(self.folder)
        """
        Setting the timeout to None means we don't return till we have a tag.
        If a timeout is set and no tag is found, 0 is returned.
        """
        RFID_doCheckSum = True
        self.reader0 = TagReader ('/dev/ttyUSB0', RFID_doCheckSum, timeOutSecs = None, kind=RFID_kind)
        self.reader1 = TagReader ('/dev/ttyUSB1', RFID_doCheckSum, timeOutSecs = None, kind=RFID_kind)
        self.reader2 = TagReader ('/dev/ttyUSB2', RFID_doCheckSum, timeOutSecs = None, kind=RFID_kind)
        self.reader3 = TagReader ('/dev/ttyUSB3', RFID_doCheckSum, timeOutSecs = None, kind=RFID_kind)

    def scan(self, reader, readerNum):
        global frameCount, startTime
        mice = []
        while True:
            try:
                Data = reader.readTag()
                if Data > 0:
                    if Data not in self.seenTags:
                        self.seenTags.append(Data)
                    self.pickup = (self.colorMap[self.seenTags.index(Data)], self.colorMap[readerNum])
                    print("pickup", Data, readerNum)
                    sleep(0.1)
                    self.pickup = None
            except Exception as e:
                print(str(e))


    def enable(self):
        super(ClockSplitter, self).enable()
        self._clock_thread = Thread(target=self._clock_run)
        self._clock_thread.daemon = True
        self._clock_thread.start()
        thread0 = Thread(target=self.scan, daemon= True, args=(self.reader0 ,0,))
        thread1 = Thread(target=self.scan, daemon= True, args=(self.reader1, 1,))
        thread2 = Thread(target=self.scan, daemon= True, args=(self.reader2, 2,))
        thread3 = Thread(target=self.scan, daemon= True, args=(self.reader3, 3,))
        thread0.start()
        thread1.start()
        thread2.start()
        thread3.start()

    def disable(self):
        super(ClockSplitter, self).disable()
        if self._clock_thread:
            self._clock_thread.join()
            self._clock_thread = None
            with self._lock:
                self._clock_image = None

    def _clock_run(self):
        # draw the clock face up front (no sense drawing that every time)
        face = Image.new('L', (30,1))
#        draw = ImageDraw.Draw(face)
        while self.enabled:
            # loop round rendering the clock hands on a copy of the face
            img = face.copy()
            if self.pickup is not None:
#                img = img.convert('RGB')
                draw = ImageDraw.Draw(img)
                draw.line(((0,0),(9,0)), fill=(255,))
                draw.line(((10,0), (19,0)), fill=self.pickup[0])
                draw.line(((20,0), (29,0)), fill=self.pickup[1])
            # assign the rendered image to the internal variable
            with self._lock:
                self._clock_image = img
            sleep(0.2)

    def _handle_frame(self, port, buf):
        try:
            out1 = self.outputs[0].get_buffer(False)
            out2 = self.outputs[1].get_buffer(False)
        except PiCameraPortDisabled:
            return True
        if out1:
            # copy the input frame to the first output buffer
            out1.copy_from(buf)
            with out1 as data:
                # construct an Image using the Y plane of the output
                # buffer's data and tell PIL we can write to the buffer
                img = Image.frombuffer('L', port.framesize, data, 'raw', 'L', 0, 1)
                img.readonly = False
                with self._lock:
                    if self._clock_image:
                        img.paste(self._clock_image, (0, 0))
            # if we've got a second output buffer replicate the first
            # buffer into it (note the difference between replicate and
            # copy_from)
            if out2:
                out2.replicate(out1)
            try:
                self.outputs[0].send_buffer(out1)
            except PiCameraPortDisabled:
                return True
        if out2:
            try:
                self.outputs[1].send_buffer(out2)
            except PiCameraPortDisabled:
                return True
        return False


def main(output_filename):
    camera = mo.MMALCamera()
    preview = mo.MMALRenderer()
    encoder = mo.MMALVideoEncoder()
    clock = ClockSplitter()
    target = mo.MMALPythonTarget(clock.folder + output_filename)

    # Configure camera output 0
#    print(camera.outputs[0])
    camera.outputs[0].framesize = (912, 720)
    camera.outputs[0].framerate = 15
    camera.outputs[0].commit()
    mp = camera.control.params[mmal.MMAL_PARAMETER_EXPOSURE_MODE]
    mp.value = mmal.MMAL_PARAM_EXPOSUREMODE_OFF
    camera.outputs[0].commit()

    # Configure H.264 encoder
    encoder.outputs[0].format = mmal.MMAL_ENCODING_H264
    encoder.outputs[0].bitrate = 2000000
    encoder.outputs[0].commit()
    p = encoder.outputs[0].params[mmal.MMAL_PARAMETER_PROFILE]
    p.profile[0].profile = mmal.MMAL_VIDEO_PROFILE_H264_HIGH
    p.profile[0].level = mmal.MMAL_VIDEO_LEVEL_H264_41
    encoder.outputs[0].params[mmal.MMAL_PARAMETER_PROFILE] = p
    encoder.outputs[0].params[mmal.MMAL_PARAMETER_VIDEO_ENCODE_INLINE_HEADER] = True
    encoder.outputs[0].params[mmal.MMAL_PARAMETER_INTRAPERIOD] = 30
    encoder.outputs[0].params[mmal.MMAL_PARAMETER_VIDEO_ENCODE_INITIAL_QUANT] = 22
    encoder.outputs[0].params[mmal.MMAL_PARAMETER_VIDEO_ENCODE_MAX_QUANT] = 22
    encoder.outputs[0].params[mmal.MMAL_PARAMETER_VIDEO_ENCODE_MIN_QUANT] = 22

    # Connect everything up and enable everything (no need to enable capture on
    # camera port 0)
    clock.inputs[0].connect(camera.outputs[0])
    preview.inputs[0].connect(clock.outputs[0])
    encoder.inputs[0].connect(clock.outputs[1])
    target.inputs[0].connect(encoder.outputs[0])
    target.connection.enable()
    encoder.connection.enable()
    preview.connection.enable()
    clock.connection.enable()
    target.enable()
    encoder.enable()
    preview.enable()
    clock.enable()
    try:
	#30 min recording max
        sleep(18000)
    except KeyboardInterrupt:
        pass
    finally:
        # Disable everything and tear down the pipeline
        target.disable()
        encoder.disable()
        preview.disable()
        clock.disable()
        target.inputs[0].disconnect()
        encoder.inputs[0].disconnect()
        preview.inputs[0].disconnect()
        clock.inputs[0].disconnect()
        with open (clock.folder + "/RTS_test.txt" , "w") as f:
            for tag in clock.seenTags:
                f.write(str(tag) + "\n")


if __name__ == '__main__':
    main('tracking.h264')
