from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWebKit import *
from PyQt5.QtWebKitWidgets import *
from PyQt5 import QtWidgets, QtCore, QtGui

import time
import math
from datetime import datetime, timedelta
from pathlib import Path

stylesheet = """
    QWidget {
        background: #323232;
    }
    QLabel {
        background: transparent;
        color: white;
        font: 24px;
    }
    QToolButton {
        background: rgba(192, 192, 192, 170);
        border-style: outset;
        border-width: 2px;
        border-radius: 10px;
        border-color: beige;
        font: 16px;
        color: black;
        min-width: 64px;
        min-height: 64px;
        max-width: 128px;
        max-height: 128px;
        padding: 12px;
    }
    QPushButton {
        background: transparent;
        border: 0px;
    }
"""

class GPSWindow(QWidget):
    def createWindow(self, infobar, gps):
        parent = None
        super(GPSWindow, self).__init__(parent)

        self.setStyleSheet(stylesheet)
        self.setWindowTitle("Location")
        self.prefix = str(Path.home()) + "/.motorhome/res/"

        lat_label = QLabel("Latitude")
        lat_label.setStyleSheet("font: bold 24px")

        lon_label = QLabel("Longitude")
        lon_label.setStyleSheet("font: bold 24px")

        alt_label = QLabel("Altitude")
        alt_label.setStyleSheet("font: bold 24px")

        self.fix = QLabel()
        self.lat = QLabel()
        self.lon = QLabel()
        self.alt = QLabel()

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

        # Ruuvitag
        self.tempInfoLabel = QLabel()

        self.temp_warn_off = QPixmap("")
        self.temp_warn_on = QPixmap(self.prefix + "snowflake.png").scaled(32, 32, Qt.KeepAspectRatio)
        self.tempWarnLabel = QLabel()

        # recording
        self.recInfoLabel = QLabel()
        self.rec_off = QPixmap("")
        self.rec_on = QPixmap(self.prefix + "rec.png").scaled(32, 32, Qt.KeepAspectRatio)

        self.updateTemperature(infobar.temperature)
        self.updateTime(datetime.now())
        self.updateTPMSWarn(infobar.tpmsWarn)
        self.updateFix(infobar.gpsFix)
        self.updateRecording(infobar.recording)
        self.updateLocation(gps)

        #infobar
        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.tpmsWarnLabel, alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.tempWarnLabel, alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.gpsInfoLabel, alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.recInfoLabel, alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.tempInfoLabel, alignment=Qt.AlignTop|Qt.AlignRight)
        hbox1.addWidget(self.timeLabel, alignment=Qt.AlignTop|Qt.AlignRight)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(lat_label, alignment=Qt.AlignCenter)
        hbox2.addWidget(lon_label, alignment=Qt.AlignCenter)
        hbox2.addWidget(alt_label, alignment=Qt.AlignCenter)

        hbox3 = QHBoxLayout()
        hbox3.addWidget(self.lat, alignment=Qt.AlignCenter|Qt.AlignTop)
        hbox3.addWidget(self.lon, alignment=Qt.AlignCenter|Qt.AlignTop)
        hbox3.addWidget(self.alt, alignment=Qt.AlignCenter|Qt.AlignTop)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addWidget(self.fix)
        vbox.addLayout(hbox2)
        vbox.addLayout(hbox3)
        vbox.addWidget(homeButton, alignment=Qt.AlignCenter)
        self.setLayout(vbox)

        self.showFullScreen()

    def updateTime(self, t):
        self.timeLabel.setText("{:02d}".format(t.hour) + ":" + "{:02d}".format(t.minute))

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

#        if self.updateAddress:
#            self.address.setText(geolocation.get_address((location[0], location[1])))
#
#        self.gps_ts = datetime.now()

    def updateTPMSWarn(self, warn):
        if warn:
            self.tpmsWarnLabel.setPixmap(self.tpms_warn_on)
        else:
            self.tpmsWarnLabel.setPixmap(self.tpms_warn_off)

    def updateGPSFix(self, fix):
        if fix > 1:
            self.gpsInfoLabel.setPixmap(self.gps_connected)
        else:
            self.gpsInfoLabel.setPixmap(self.gps_disconnected)

        if fix <= 1:
            self.fix.setText("Fix: None")
        elif fix == 2:
            self.fix.setText("Fix: 2D")
        else:
            self.fix.setText("Fix: 3D")

    def updateRecording(self, recording):
        if recording:
            self.recInfoLabel.setPixmap(self.rec_on)
        else:
            self.recInfoLabel.setPixmap(self.rec_off)

    def exit(self):
        self.close()