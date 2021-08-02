"""
Garmin Virb camcorder
"""
import os
import cv2

from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtGui import QPixmap, QImage
from virb import Virb

class Camcorder(QObject):
    """ Garmin Virb camcorder """

    finished = pyqtSignal()
    rec_start_finished = pyqtSignal()
    rec_stop_finished = pyqtSignal()
    snapshot_finished = pyqtSignal()
    preview_finished = pyqtSignal()
    image = pyqtSignal(QPixmap)

    def __init__(self, ip, parent=None):
        QObject.__init__(self, parent=parent)
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;udp"
        self.camera = Virb((ip, 80))
        self.run_video = True

    def start_recording(self):
        """ Start video recording """
        #set autorecord off
        self.camera.set_features('autoRecord', 'off')
        self.camera.set_features('videoLoop', '30')
        self.camera.start_recording()
        print("start recording")
        self.rec_start_finished.emit()

    def stop_recording(self):
        """ Stop video recording """
        self.camera.stop_recording()
        self.camera.set_features('autoRecord', 'off')
        self.camera.set_features('videoLoop', '30')
        print("stop recording")
        self.rec_stop_finished.emit()

    def snapshot(self):
        """ take a snapshot image """
        self.camera.set_features('selfTimer', '2')
        self.camera.snap_picture()
        print("taking a snapshot")
        self.snapshot_finished.emit()

    def live_preview(self):
        """ Show live preview """
        print("setting up camera")

        url = "rtsp://" + self.camera.host[0] + "/livePreviewStream"
        try:
            cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
        except ConnectionError:
            print("video stream unavailable")
            self.preview_finished.emit()
            return

        cap.set(cv2.CAP_PROP_BUFFERSIZE, 0)

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = float(cap.get(cv2.CAP_PROP_FPS))
        print("video: " + str(width) + "x" + str(height) + "@" + str(fps))

        while self.run_video:
            ret, frame = cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(image)
                self.image.emit(pixmap)

        print("video preview stopped")
        cap.release()
        self.preview_finished.emit()

    def stop_preview(self):
        """ Stop video preview """
        print("stopping live preview")
        self.run_video = False
