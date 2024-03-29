from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import QtWidgets, QtCore, QtGui

import time
import math
import cv2
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

def rotate(image, angle):
    row,col = image.shape[:2]

    center = tuple(np.array([row,col])/2)
    rot_mat = cv2.getRotationMatrix2D(center,angle,1.0)
    new_image = cv2.warpAffine(image, rot_mat, (col,row), borderValue=(50,50,50))

    frame = cv2.cvtColor(new_image, cv2.COLOR_BGR2RGB)
    rotated = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)

    return rotated

class GPSWindow(QWidget):
    info = pyqtSignal(dict)

    def createWindow(self, infobar, gps):
        parent = None
        super(GPSWindow, self).__init__(parent)

        self.setStyleSheet(open('res/childs.css', 'r').read())
        self.setWindowTitle("Location")
        self.prefix = str(Path.home()) + "/.motorhome/res/"

        src_label = QLabel("")
        src_label.setStyleSheet("font: bold 24px")

        lat_label = QLabel("Latitude")
        lat_label.setStyleSheet("font: bold 24px")

        lon_label = QLabel("Longitude")
        lon_label.setStyleSheet("font: bold 24px")

        alt_label = QLabel("Altitude")
        alt_label.setStyleSheet("font: bold 24px")

        course_label = QLabel("Heading")
        course_label.setStyleSheet("font: bold 24px")

        self.fix = QLabel()
        self.lat = QLabel()
        self.lon = QLabel()
        self.alt = QLabel()
        self.course = QLabel()

        homeButton = QPushButton()
        homeButton.setIcon(QIcon(self.prefix + 'home.png'))
        homeButton.setIconSize(QSize(64, 64))
        homeButton.clicked.connect(self.exit)

        # time
        self.timeLabel = QLabel()

        # TPMS warn light
        self.tpms_warn_off = QPixmap("")
        self.tpms_warn_on = QPixmap(self.prefix + "tpms_warn_on.png").scaled(32, 32, Qt.KeepAspectRatio)
        self.tpmsWarnLabel = QLabel()

        # GPS fix
        self.gps_disconnected = QPixmap(self.prefix + "no_gps.png").scaled(32, 32, Qt.KeepAspectRatio)
        self.gps_connected = QPixmap("")
        self.gpsInfoLabel = QLabel()
        self.gpsSpeedLabel = QLabel("-- km/h")

        # Ruuvitag
        self.tempInfoLabel = QLabel()

        self.temp_warn_off = QPixmap("")
        self.temp_warn_on = QPixmap(self.prefix + "snowflake.png").scaled(32, 32, Qt.KeepAspectRatio)
        self.tempWarnLabel = QLabel()

        # recording
        self.recInfoLabel = QLabel()
        self.rec_off = QPixmap("")
        self.rec_on = QPixmap(self.prefix + "rec.png").scaled(32, 32, Qt.KeepAspectRatio)

        self.src_label = QLabel()
        self.gps_src_internal = QPixmap(self.prefix + "gps_internal.png").scaled(32, 32, Qt.KeepAspectRatio)
        self.gps_src_garmin = QPixmap(self.prefix + "garmin.png").scaled(32, 32, Qt.KeepAspectRatio)

        # compass
        self.compassLabel = QLabel()
        self.compass = cv2.imread(self.prefix + "compass2.png", cv2.IMREAD_UNCHANGED)

        self.updateTemperature(infobar.temperature)
        self.updateTime(datetime.now())
        self.updateTPMSWarn(infobar.tpmsWarn)
        self.updateFix(gps.fix)
        self.updateRecording(infobar.recording)
        self.updateLocation(gps)

        #infobar
        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.tpmsWarnLabel, alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.tempWarnLabel, alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.gpsInfoLabel, alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.recInfoLabel, alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.gpsSpeedLabel, alignment=Qt.AlignTop|Qt.AlignRight)
        hbox1.addWidget(self.tempInfoLabel, alignment=Qt.AlignTop|Qt.AlignRight)
        hbox1.addWidget(self.timeLabel, alignment=Qt.AlignTop|Qt.AlignRight)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(src_label, alignment=Qt.AlignCenter)
        hbox2.addWidget(lat_label, alignment=Qt.AlignCenter)
        hbox2.addWidget(lon_label, alignment=Qt.AlignCenter)
        hbox2.addWidget(alt_label, alignment=Qt.AlignCenter)
        hbox2.addWidget(course_label, alignment=Qt.AlignCenter)

        hbox3 = QHBoxLayout()
        hbox3.addWidget(self.src_label, alignment=Qt.AlignCenter)
        hbox3.addWidget(self.lat, alignment=Qt.AlignCenter|Qt.AlignTop)
        hbox3.addWidget(self.lon, alignment=Qt.AlignCenter|Qt.AlignTop)
        hbox3.addWidget(self.alt, alignment=Qt.AlignCenter|Qt.AlignTop)
        hbox3.addWidget(self.course, alignment=Qt.AlignCenter|Qt.AlignTop)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
#        vbox.addWidget(self.fix, alignment=Qt.AlignCenter|Qt.AlignTop)
        vbox.addLayout(hbox2)
        vbox.addLayout(hbox3)
        vbox.addWidget(self.compassLabel, alignment=Qt.AlignCenter)
        vbox.addWidget(homeButton, alignment=Qt.AlignCenter)
        self.setLayout(vbox)

        self.showFullScreen()

    def updateInfobar(self, data):
        self.updateTime(data['time'])
        self.updateTemperature(data['temperature'])
        self.updateTPMSWarn(data['tpms'])
        self.updateGPSFix(data['gpsFix'])
        self.updateSpeed(data['speed'])
        self.updateRecording(data['recording'])

    def updateTime(self, t):
        self.timeLabel.setText("{:02d}".format(t.hour) + ":" + "{:02d}".format(t.minute))

    def updateSpeed(self, speed):
        if math.isnan(speed):
            return
        self.gpsSpeedLabel.setText("{:d}".format(round(3.6*speed)) + " km/h")

    def updateTemperature(self, temperature):
        if math.isnan(temperature):
            return

        self.tempInfoLabel.setText("{0:d}".format(round(temperature)) + "\u2103")
        if temperature < 3.0:
            self.tempWarnLabel.setPixmap(self.temp_warn_on)
        elif temperature > 3.2:
            self.tempWarnLabel.setPixmap(self.temp_warn_off)

    def updateFix(self, fix):
        if fix == 1:
            self.fix.setText("Fix: None")
        elif fix == 2:
            self.fix.setText("Fix: 2D")
        elif fix == 3:
            self.fix.setText("Fix: 3D")

    def updateLocation(self, gps):
#        geolocation = Geolocation("motorhome")

        if gps.src == "internal":
            self.src_label.setPixmap(self.gps_src_internal)
        elif gps.src == "garmin":
            self.src_label.setPixmap(self.gps_src_garmin)

        if not math.isnan(gps.lat):
            self.lat.setText("{:.5f}".format(round(gps.lat, 5)))
        else:
            self.lat.setText("--")

        if not math.isnan(gps.lon):
            self.lon.setText("{:.5f}".format(round(gps.lon, 5)))
        else:
            self.lon.setText("--")

        if not math.isnan(gps.alt):
            self.alt.setText("{0:d}".format(round(gps.alt)))
        else:
            self.alt.setText("--")

        if not math.isnan(gps.course):
            self.course.setText("{0:d}".format(round(gps.course)) + "\u00b0")
            self.compassLabel.setPixmap(QPixmap.fromImage(rotate(self.compass, gps.course)))
        else:
            self.course.setText("--\u00b0")

    def updateTPMSWarn(self, warn):
        if warn:
            self.tpmsWarnLabel.setPixmap(self.tpms_warn_on)
        else:
            self.tpmsWarnLabel.setPixmap(self.tpms_warn_off)

    def updateGPSFix(self, fix):
        if fix:
            self.gpsInfoLabel.setPixmap(self.gps_connected)
        else:
            self.gpsInfoLabel.setPixmap(self.gps_disconnected)

    def updateRecording(self, recording):
        if recording:
            self.recInfoLabel.setPixmap(self.rec_on)
        else:
            self.recInfoLabel.setPixmap(self.rec_off)

    def exit(self):
        self.close()
