from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import QtCore, QtGui

import os
import cv2
from virb import Virb

class Camcorder(QObject):
    global virb_addr

    finished = pyqtSignal()
    image = pyqtSignal(QIcon)
    stop_preview = pyqtSignal()

    def __init__(self, ip, parent=None):
        QObject.__init__(self, parent=parent)
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;udp"
        self.camera = Virb((ip, 80))
        self.runVideo = True

    def start_recording(self):
        #set autorecord off
        self.camera.set_features('autoRecord', 'whenMoving')
        self.camera.set_features('videoLoop', '30')
        self.camera.start_recording()
        print("start recording")
        self.finished.emit()

    def stop_recording(self):
        self.camera.stop_recording()
        self.camera.set_features('autoRecord', 'whenMoving')
        self.camera.set_features('videoLoop', '30')
        print("stop recording")
        self.finished.emit()

    def snapshot(self):
        self.camera.set_features('selfTimer', '2')
        self.camera.snap_picture()
        print("taking a snapshot")
        self.finished.emit()

    def live_preview(self):
        print("setting up camera")

        url = "rtsp://" + self.camera.host[0] + "/livePreviewStream"
        try:
            cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
        except:
            print("video stream unavailable")
            self.finished.emit()
            return

        cap.set(cv2.CAP_PROP_BUFFERSIZE, 10)

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = float(cap.get(cv2.CAP_PROP_FPS))
        print("video: " + str(width) + "x" + str(height) + "@" + str(fps))

        scale = 100
        while self.runVideo:
            ret, frame = cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(image).scaled(int(width*scale/100),
                                                         int(height*scale/100),
                                                         Qt.KeepAspectRatio)
                self.image.emit(QIcon(pixmap))

        print("video preview stopped")
        cap.release()
        self.finished.emit()

    def stop_preview(self):
        print("stopping live preview")
        self.runVideo = False
