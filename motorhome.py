#!/usr/bin/env python3

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import QtWidgets, QtCore, QtGui

#from PyQt5.QtWebKitWidgets import QWebView, QWebPage
#from PyQt5.QtWebKit import QWebSettings
#from PyQt5.QtNetwork import *

from datetime import datetime
import threading
from threading import Thread
import cv2
import qdarkgraystyle
import socket
import psutil
import os
import sys
import time
import queue
import os.path

camera = 20 #virtual device
prefix = "/home/pi/motorhome"

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: black;")
        self.setWindowTitle("Motorhome Info")
        self.warns = self.Warnings()
        self.warning = "No messages"
        self.resolution = QDesktopWidget().availableGeometry(-1)
        self.setup_ui()
        self.setup_camera()
        self.setup_warns()
#        self.showFullScreen()
        self.showMaximized()

    def setup_ui(self):
        #Initialize widgets
        self.centralWidget = QWidget()

        self.TabWidget = QTabWidget(self)
        self.TabWidget.setFont(QFont("Sanserif", 16))

        pages = [QWidget(), QWidget(), QWidget(), QWidget()]

        pages[0].setGeometry(0, 0, self.resolution.width(), self.resolution.height())
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        vbox1 = QVBoxLayout()
        vbox1.addWidget(self.image_label)
        pages[0].setLayout(vbox1)

        pages[1].setGeometry(0, 0, self.resolution.width(), self.resolution.height())
        pressure = "-- bar"
        temperature = "-- C"
        self.fl_label = QLabel(pressure + "\n" + temperature)
        self.fr_label = QLabel(pressure + "\n" + temperature)
        self.rl_label = QLabel(pressure + "\n" + temperature)
        self.rr_label = QLabel(pressure + "\n" + temperature)

        font = self.fl_label.font()
        font.setPointSize(32)
        font.setBold(True)
        self.fl_label.setFont(font)
        self.fr_label.setFont(font)
        self.rl_label.setFont(font)
        self.rr_label.setFont(font)

        self.fl_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.fr_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.rl_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.rr_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)

        pixmap = QPixmap(prefix + "/res/tire.png").scaled(128, 128, Qt.KeepAspectRatio)

        tire1_label = QLabel()
        tire1_label.setPixmap(pixmap)
        tire1_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        tire2_label = QLabel()
        tire2_label.setPixmap(pixmap)
        tire2_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        tire3_label = QLabel()
        tire3_label.setPixmap(pixmap)
        tire3_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        tire4_label = QLabel()
        tire4_label.setPixmap(pixmap)
        tire4_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        vbox2 = QGridLayout()
        vbox2.addWidget(self.fl_label, 0, 0)
        vbox2.addWidget(tire1_label, 0, 1)
        vbox2.addWidget(tire2_label, 0, 2)
        vbox2.addWidget(self.fr_label, 0, 3)
        vbox2.addWidget(self.rl_label, 1, 0)
        vbox2.addWidget(tire3_label, 1, 1)
        vbox2.addWidget(tire4_label, 1, 2)
        vbox2.addWidget(self.rr_label, 1, 3)
        pages[1].setLayout(vbox2)

        pages[2].setGeometry(0, 0, self.resolution.width(), self.resolution.height())
        self.warn_edit = QTextEdit()
        font = self.warn_edit.font()
        font.setPointSize(16)
        self.warn_edit.setFont(font)
        self.warn_edit.setReadOnly(True)

        font_metrics = QFontMetrics(font)
        RowHeight = font_metrics.lineSpacing()
        self.warn_edit.setFixedHeight(10 * RowHeight)
        self.warn_edit.setAlignment(Qt.AlignVCenter)

        vbox3 = QVBoxLayout()
        vbox3.addWidget(self.warn_edit)
        pages[2].setLayout(vbox3)

        self.timer_warning = QTimer()
        self.timer_warning.timeout.connect(self.update_warnings)
        self.timer_warning.start(100)

        font = self.fl_label.font()
        font.setPointSize(16)
        font.setBold(True)

        centralLayout = QVBoxLayout()
        centralLayout.addWidget(self.TabWidget, 1)

        self.dc_index = self.TabWidget.addTab(pages[0], "Dash Cam")
        self.tp_index = self.TabWidget.addTab(pages[1], "Tire Pressure")
        self.warn_index = self.TabWidget.addTab(pages[2], "Messages")

        self.TabWidget.setStyleSheet('''
            QTabBar::tab:selected {background-color: black;}
            QTabBar::tab:selected {font: 16pt bold}
            ''')

        self.centralWidget.setLayout(centralLayout)
        self.setCentralWidget(self.centralWidget)

    def setup_camera(self):
        #Initialize camera playback
        self.cap = cv2.VideoCapture(camera)

        try:
            self.cap.isOpened()
        except:
            self.cap.release()
            exit('Failure')

        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = float(self.cap.get(cv2.CAP_PROP_FPS))
        print("video: " + str(width) + "x" + str(height) + "@" + str(fps))

        self.timer = QTimer()
        self.timer.timeout.connect(self.display_video_stream)
        self.timer.start(1000/fps)

    def display_video_stream(self):
        scale = 80

        #Read frame from camera
        ret, frame = self.cap.read()

        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            font = cv2.FONT_HERSHEY_DUPLEX
            datestr = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            cv2.putText(frame, datestr, (5, frame.shape[0]-10), font, 1, (255, 255, 0), 2, cv2
.LINE_AA)

            image = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(image).scaled(self.resolution.width()*scale/100,
                                                     self.resolution.height()*scale/100,
                                                     Qt.KeepAspectRatio)
            self.image_label.setPixmap(pixmap)

    def update_warnings(self):
        self.warn_edit.setText(self.warning)
        self.warn_edit.setAlignment(Qt.AlignCenter)
        self.warn_edit.setReadOnly(True)

    def sensor_handler(self, client):
        while True:
            sensor = client.recv(32).decode('utf-8')
            if sensor:
                sensor = sensor.split(',')
                if sensor[0] == 'Stairs':
                    if sensor[1] == '1':
                        self.TabWidget.setCurrentIndex(self.warn_index)
                        self.warning = "Stairs down"
                    else:
                        self.warning = "No warnings"
                elif sensor[0] == 'FL':
                    self.fl_label.setText(sensor[1] + " bar\n" + sensor[2] + " C")
                elif sensor[0] == 'FR':
                    self.fr_label.setText(sensor[1] + " bar\n" + sensor[2] + " C")
                elif sensor[0] == 'RL':
                    self.rl_label.setText(sensor[1] + " bar\n" + sensor[2] + " C")
                elif sensor[0] == 'RR':
                    self.rr_label.setText(sensor[1] + " bar\n" + sensor[2] + " C")
        client.close()

    def get_warns(self):
        # create a local socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            # bind the socket to the port
            sock.bind(('localhost', 5000))
            # listen for incoming connections
            sock.listen(5)
            print("Server started...")

            while True:
                client, addr = sock.accept()
                threading.Thread(target=self.sensor_handler, args=(client,)).start()

    def setup_warns(self):
        # warnings server
        self.warns.worker = Thread(target=self.get_warns, args=())
        self.warns.worker.setDaemon(True)
        self.warns.worker.start()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.cap.release()

            if self.timer.isActive():
                self.timer.stop()

            #ugly but efficient
            system = psutil.Process(os.getpid())
            system.terminate()

    class Warnings:
        def __init__(self, warns=0):
            self.warns = warns
            self.worker = 0

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkgraystyle.load_stylesheet())
    win = MainApp()
    sys.exit(app.exec_())
