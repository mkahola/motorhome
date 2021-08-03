from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import QtWidgets, QtCore, QtGui

import time
import math
import configparser
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

class InfoWindow(QWidget):
    info = pyqtSignal()

    def createWindow(self, infobar):
        parent = None
        super(InfoWindow, self).__init__(parent)

        self.setStyleSheet(stylesheet)
        self.setWindowTitle("Information")
        self.prefix = str(Path.home()) + "/.motorhome/res/"

        homeButton = QPushButton()
        homeButton.setIcon(QIcon(self.prefix + 'home.png'))
        homeButton.setIconSize(QSize(64, 64))
        homeButton.clicked.connect(self.exit)

        # === infobar ===
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

        self.updateTemperature(infobar.temperature)
        self.updateTPMSWarn(infobar.tpmsWarn)
        self.updateTime(datetime.now())
        self.updateGPSFix(infobar.gpsFix)
        self.updateSpeed(infobar.speed)
        self.updateRecording(infobar.recording)

        #infobar
        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.tpmsWarnLabel, alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.tempWarnLabel, alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.gpsInfoLabel,  alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.recInfoLabel,  alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.gpsSpeedLabel, alignment=Qt.AlignTop|Qt.AlignRight)
        hbox1.addWidget(self.tempInfoLabel, alignment=Qt.AlignTop|Qt.AlignRight)
        hbox1.addWidget(self.timeLabel,     alignment=Qt.AlignTop|Qt.AlignRight)
        # === infobar ===

        conf_file = str(Path.home()) + "/.motorhome/motorhome.conf"
        config = configparser.ConfigParser()

        config.read(conf_file)
        try:
            model = config['Maker']['model']
            year = config['Maker']['year']
            typeLabel = config['Maker']['typeLabel']
            makerLabel = config['Maker']['makerLabel']
            vin = config['Maker']['vin']
        except:
            model = ""
            year = ""
            typeLabel = ""
            makerLabel = ""

        modelLabel = QLabel(model + ", " + year)
        modelLabel.setStyleSheet("QLabel {color: white; font: bold 24px}")
        modelLabel.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)

        try:
            chassisLabel = QLabel(config['Maker']['chassis'])
        except:
            chassisLabel = QLabel()
        chassisLabel.setStyleSheet("QLabel {color: white; font: bold 16px}")
        chassisLabel.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)

        pixmap = QPixmap(typeLabel).scaled(320, 320, Qt.KeepAspectRatio)
        typeLabel = QLabel()
        typeLabel.setPixmap(pixmap)
        typeLabel.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)

        pixmap = QPixmap(makerLabel).scaled(300, 300, Qt.KeepAspectRatio)
        makerLabel = QLabel()
        makerLabel.setPixmap(pixmap)
        makerLabel.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)

        try:
            vinLabel = QLabel("VIN " + config['Maker']['vin'])
        except:
            vinLabel = QLabel()

        vinLabel.setStyleSheet("QLabel {color: white; font: bold 16px}")
        vinLabel.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(typeLabel)
        hbox2.addWidget(makerLabel)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addWidget(modelLabel)
        vbox.addWidget(chassisLabel)
        vbox.addWidget(vinLabel)
        vbox.addLayout(hbox2)
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
        if temperature < 3.0:
            self.tempWarnLabel.setPixmap(self.temp_warn_on)
        elif temperature > 3.2:
            self.tempWarnLabel.setPixmap(self.temp_warn_off)

        self.tempInfoLabel.setText("{0:d}".format(round(temperature)) + "\u2103")

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


