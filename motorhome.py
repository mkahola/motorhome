#!/usr/bin/env python3

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from datetime import datetime
import cv2
import qimage2ndarray
import qdarkgraystyle
import sys

class MainApp(QWidget):

    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: black;") 
        self.setWindowTitle("Motorhome Info")
        self.video_size = QSize(1280, 720)
        self.setup_ui()
        self.setup_camera()
        self.showFullScreen()

    def setup_ui(self):
        """Initialize widgets."""
        TabWidget = QTabWidget(self)

        page1 = QWidget()
        page1.setGeometry(0, 0, self.video_size.width(), self.video_size.height())
        self.image_label = QLabel()
        self.image_label.setFixedSize(self.video_size)
        vbox1 = QVBoxLayout()
        vbox1.addWidget(self.image_label)
        page1.setLayout(vbox1)

        page2 = QWidget()
        page2.setGeometry(0, 0, self.video_size.width(), self.video_size.height())

        page3 = QWidget()
        page3.setGeometry(0, 0, self.video_size.width(), self.video_size.height())

        self.dc_index = TabWidget.addTab(page1, "Dash Cam")
        self.tp_index = TabWidget.addTab(page2, "Tire Pressure")
        self.warn_index = TabWidget.addTab(page3, "Warnings") 

    def setup_camera(self):
        """Initialize camera"""
        self.timer_init = QTimer()
        self.timer_init.timeout.connect(self.setup_camera)

        self.capture = cv2.VideoCapture(2)

        if (not self.capture.isOpened()):
            self.timer_init.start(5*1000)
            return
        else:
            self.timer_init.stop()

        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.video_size.width())
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.video_size.height())
        self.fps = 30.0
        self.fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.prefix = "dashcam_"
        self.ts = 0

        self.timer = QTimer()
        self.timer.timeout.connect(self.display_video_stream)
        self.timer.start(10)

    def update_file(self, prefix):
        now = datetime.now()
        ts_new = now.timestamp()

        if ((ts_new - self.ts) >= 5*60):
            date_time = now.strftime("%m%d%Y_%H_%M_%S")
            filename=self.prefix + date_time + ".avi"
            self.out = cv2.VideoWriter(filename, self.fourcc, self.fps,
                                       (self.video_size.width(), self.video_size.height()))
            self.ts = ts_new

    def display_video_stream(self):
        """Read frame from camera and repaint QLabel widget"""
        check, frame = self.capture.read()

        if check:
            self.update_file("dashcam_")

            # write the frame
            self.out.write(frame)

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
            image = qimage2ndarray.array2qimage(frame)  #memory leak workaround
            self.image_label.setPixmap(QPixmap.fromImage(image))
        else:
            self.timer.stop()
            self.setup_camera()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.timer.stop()
            self.capture.release()

            try:
                self.out.release()
            except:
                print("camera capture not available")
            self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkgraystyle.load_stylesheet())
    win = MainApp()
    sys.exit(app.exec_())
