#!/usr/bin/env python3
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWebKit import *
from PyQt5.QtWebKitWidgets import *
from PyQt5 import QtWidgets, QtCore, QtGui

from datetime import datetime, timedelta
import time
import math
import psutil
import sys
import os.path
import subprocess
import configparser
import nmap3
from pathlib import Path
from netifaces import interfaces, ifaddresses, AF_INET

from tires import Tires
from tpms import TPMS
from virb import Virb
from camcorder import Camcorder
from gps import Location
from warns import Warnings
from geolocation import Geolocation
from ruuvi import RuuviTag, Ruuvi
from searchvirb import SearchVirb

from speedowindow import SpeedoWindow
from camerawindow import CameraWindow
from tpmswindow import TPMSWindow
from gpswindow import GPSWindow
from ruuviwindow import RuuviWindow
from infowindow import InfoWindow

stylesheet = """
    QMainWindow {
        border-image: url(res/background.png) 0 0 0 0 stretch stretch;
        background-repeat: no-repeat;
        background-position: center;
    }
    QLabel {
        background: transparent;
        color: white;
        font: 24px
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

class InfoBar:
    def __init__(self):
        self.temperature = math.nan
        self.tpmsWarn = False
        self.gpsFix = False
        self.recording = False

class GPS:
    def __init__(self):
        self.lat = math.nan
        self.lon = math.nan
        self.alt = math.nan
        self.fix = 0
        self.speed = math.nan

class MainApp(QMainWindow):
    stop_signal = pyqtSignal()
    exit_signal = pyqtSignal()
    set_season = pyqtSignal(int)

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Motorhome Info")
        self.setStyleSheet(stylesheet)
        self.resolution = QDesktopWidget().availableGeometry(-1)
        self.prefix = str(Path.home()) + "/.motorhome/res/"

        self.infobar = InfoBar()
        self.gps = GPS()

        self.virb = Virb()
        self.tpms = Tires()
        self.ruuvi = Ruuvi()

        self.centralWidget = QWidget()

        #speedometer
        self.speedoButton = QToolButton(self)
        self.speedoButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.speedoButton.setIcon(QIcon(self.prefix + 'speedo.png'))
        self.speedoButton.setText("Speedo")
        self.speedoButton.setIconSize(QSize(104, 104))
        self.speedoButton.clicked.connect(self.createSpeedoWindow)

        # dashcam
        self.cameraButton = QToolButton(self)
        self.cameraButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.cameraButton.setIcon(QIcon(self.prefix + 'dashcam.png'))
        self.cameraButton.setText("Dashcam")
        self.cameraButton.setIconSize(QSize(104, 104))
        self.cameraButton.clicked.connect(self.createCameraWindow)

        # tpms
        self.tpmsButton = QToolButton(self)
        self.tpmsButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.tpmsButton.setIcon(QIcon(self.prefix + 'tpms.png'))
        self.tpmsButton.setText("TPMS")
        self.tpmsButton.setIconSize(QSize(104, 104))
        self.tpmsButton.clicked.connect(self.createTPMSWindow)

        # GPS
        self.gpsButton = QToolButton(self)
        self.gpsButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.gpsButton.setIcon(QIcon(self.prefix + 'location.png'))
        self.gpsButton.setText("Location")
        self.gpsButton.setIconSize(QSize(104, 104))
        self.gpsButton.clicked.connect(self.createGPSWindow)

        # ruuvitag
        self.ruuviButton = QToolButton(self)
        self.ruuviButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.ruuviButton.setIcon(QIcon(self.prefix + 'ruuvi.png'))
        self.ruuviButton.setText("Ruuvitag")
        self.ruuviButton.setIconSize(QSize(104, 104))
        self.ruuviButton.clicked.connect(self.createRuuviWindow)

        # vehicle info
        self.infoButton = QToolButton(self)
        self.infoButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.infoButton.setIcon(QIcon(self.prefix + 'info_128x128.png'))
        self.infoButton.setText("Info")
        self.infoButton.setIconSize(QSize(104, 104))
        self.infoButton.clicked.connect(self.createInfoWindow)

        # poweroff
        powerButton = QPushButton("", self)
        powerButton.setIcon(QIcon(self.prefix + 'power.png'))
        powerButton.setIconSize(QSize(32, 32))
        powerButton.clicked.connect(self.poweroff)

        # time
        self.timeLabel = QLabel()

        # TPMS warn light
        self.tpms_warn_off = QPixmap("")
        self.tpms_warn_on = QPixmap(self.prefix + "tpms_warn_on.png").scaled(32, 32, Qt.KeepAspectRatio)
        self.tpmsWarnLabel = QLabel()
        self.tpmsWarnLabel.setPixmap(self.tpms_warn_off)

        # Ruuvitag
        self.tempInfoLabel = QLabel()

        self.temp_warn_off = QPixmap("")
        self.temp_warn_on = QPixmap(self.prefix + "snowflake.png").scaled(32, 32, Qt.KeepAspectRatio)
        self.tempWarnLabel = QLabel()

        self.updateTemperature(self.ruuvi.temperature)

        self.datetimer=QTimer()
        self.datetimer.timeout.connect(self.updateTime)
        self.datetimer.start(1000)

        # recording
        self.recInfoLabel = QLabel()
        self.rec_off = QPixmap("")
        self.rec_on = QPixmap(self.prefix + "rec.png").scaled(32, 32, Qt.KeepAspectRatio)
        self.updateRecording(self.infobar.recording)

        # gps
        self.gpsInfoLabel = QLabel()
        self.gps_connected = QPixmap("")
        self.gps_disconnected = QPixmap(self.prefix + "no_gps.png").scaled(32, 32, Qt.KeepAspectRatio)
        self.updateGPSFix(self.infobar.gpsFix)

        #infobar
        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.tpmsWarnLabel, alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.tempWarnLabel, alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.gpsInfoLabel,  alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.recInfoLabel,  alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.tempInfoLabel, alignment=Qt.AlignTop|Qt.AlignRight)
        hbox1.addWidget(self.timeLabel,     alignment=Qt.AlignTop|Qt.AlignRight)

        grid = QGridLayout()
        grid.addWidget(self.speedoButton, 0, 0)
        grid.addWidget(self.cameraButton, 0, 1)
        grid.addWidget(self.tpmsButton,   0, 2)

        grid.addWidget(self.gpsButton,    1, 0)
        grid.addWidget(self.ruuviButton,  1, 1)
        grid.addWidget(self.infoButton,   1, 2)

        grid.setSpacing(10)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addLayout(grid)
        vbox.addWidget(powerButton, alignment=Qt.AlignRight)

        self.centralWidget.setLayout(vbox)
        self.setCentralWidget(self.centralWidget)

        # start threads
        self.initTPMSThread()
        self.initSearchVirbThread()
        self.initRuuvitagThread()
        self.initGPSThread()

        self.showFullScreen()
#        self.showMaximized()

    def createSpeedoWindow(self):
        self.speedoWindow = SpeedoWindow(parent=self)
        self.speedoWindow.createWindow(self.infobar)
        self.speedoWindow.show()

    def createCameraWindow(self):
        self.cameraWindow = CameraWindow(parent=self)
        self.cameraWindow.createWindow(self.infobar, self.virb)
        self.cameraWindow.recording.connect(self.getRecSignal)
        self.cameraWindow.show()

    def createTPMSWindow(self):
        self.tpmsWindow = TPMSWindow(parent=self)
        self.tpmsWindow.createWindow(self.infobar, self.tpms)
        self.tpmsWindow.show()

    def createGPSWindow(self):
        self.gpsWindow = GPSWindow(parent=self)
        self.gpsWindow.createWindow(self.infobar, self.gps)
        self.gpsWindow.show()

    def createRuuviWindow(self):
        self.ruuviWindow = RuuviWindow(parent=self)
        self.ruuviWindow.createWindow(self.infobar, self.ruuvi)
        self.ruuviWindow.show()

    def createInfoWindow(self):
        self.infoWindow = InfoWindow(parent=self)
        self.infoWindow.createWindow(self.infobar)
        self.infoWindow.show()

    def getRecSignal(self, data):
        self.infobar.recording = data
        self.updateRecording(self.infobar.recording)

    def updateTime(self):
        t = datetime.now()
        self.timeLabel.setText("{:02d}".format(t.hour) + ":" + "{:02d}".format(t.minute))

        try:
            self.speedoWindow.updateTPSMWarn(self.infobar.tpsmWarn)
            self.speedoWindow.updateGPSFix(self.infobar.gpsFix)
            self.speedoWindow.updateTemperature(self.infobar.temperature)
            self.speedoWindow.updateRecording(infobar.recording)
            self.speedoWindow.updateTime(t)
        except:
            pass

        try:
            self.cameraWindow.updateTPSMWarn(self.infobar.tpsmWarn)
            self.cameraWindow.updateGPSFix(self.infobar.gpsFix)
            self.cameraWindow.updateTemperature(self.infobar.temperature)
            self.cameraWindow.updateRecording(infobar.recording)
            self.cameraWindow.updateTime(t)
        except AttributeError:
            pass

        try:
            self.tpmsWindow.updateTPSMWarn(self.infobar.tpsmWarn)
            self.tpmsWindow.updateGPSFix(self.infobar.gpsFix)
            self.tpmsWindow.updateTemperature(self.infobar.temperature)
            self.tpmsWindow.updateRecording(infobar.recording)
            self.tpmsWindow.updateTime(t)
        except AttributeError:
            pass

        try:
            self.gpsWindow.updateTPSMWarn(self.infobar.tpsmWarn)
            self.gpsWindow.updateGPSFix(self.gps.fix)
            self.gpsWindow.updateTemperature(self.infobar.temperature)
            self.gpsWindow.updateRecording(infobar.recording)
            self.gpsWindow.updateTime(t)
        except AttributeError:
            pass

        try:
            self.ruuviWindow.updateTPSMWarn(self.infobar.tpsmWarn)
            self.ruuviWindow.updateGPSFix(self.infobar.gpsFix)
            self.ruuviWindow.updateTemperature(self.infobar.temperature)
            self.ruuviWindow.updateRecording(infobar.recording)
            self.ruuviWindow.updateTime(t)
        except AttributeError:
            pass

        try:
            self.infoWindow.updateTPSMWarn(self.infobar.tpsmWarn)
            self.infoWindow.updateGPSFix(self.infobar.gpsFix)
            self.infoWindow.updateTemperature(self.infobar.temperature)
            self.infoWindow.updateRecording(infobar.recording)
            self.infoWindow.updateTime(t)
        except AttributeError:
            pass

    def initSearchVirbThread(self):
        self.virbThread = QThread()
        self.virbWorker = SearchVirb()
        self.exit_signal.connect(self.virbWorker.stop)
        self.virbWorker.moveToThread(self.virbThread)
        self.virbWorker.finished.connect(self.virbThread.quit)
        self.virbWorker.finished.connect(self.virbWorker.deleteLater)
        self.virbThread.finished.connect(self.virbThread.deleteLater)
        self.virbThread.started.connect(self.virbWorker.run)

        self.virbWorker.ip.connect(self.setVirbIP)

        self.virbThread.start()

    def setVirbIP(self, ip):
        self.virb.ip = ip
        try:
            self.cameraWindow.setVirbIP(ip)
        except AttributeError:
            pass

    def initTPMSThread(self):
        self.tpmsThread = QThread()
        self.tpmsWorker = TPMS()
        self.exit_signal.connect(self.tpmsWorker.stop)
        self.set_season.connect(self.tpmsWorker.update_season)
        self.tpmsWorker.moveToThread(self.tpmsThread)
        self.tpmsWorker.finished.connect(self.tpmsThread.quit)
        self.tpmsWorker.finished.connect(self.tpmsWorker.deleteLater)
        self.tpmsThread.finished.connect(self.tpmsThread.deleteLater)
        self.tpmsThread.started.connect(self.tpmsWorker.run)

        self.tpmsWorker.tpms.connect(self.setTPMS)
        self.tpmsWorker.tpms_warn.connect(self.setTPMSWarn)

        self.tpmsThread.start()

    def initGPSThread(self):
        self.gpsThread =  QThread()
        self.gpsWorker = Location()
        self.exit_signal.connect(self.gpsWorker.stop)
        self.gpsWorker.moveToThread(self.gpsThread)
        self.gpsWorker.finished.connect(self.gpsThread.quit)
        self.gpsWorker.finished.connect(self.gpsWorker.deleteLater)
        self.gpsThread.finished.connect(self.gpsThread.deleteLater)
        self.gpsThread.started.connect(self.gpsWorker.run)

        self.gpsWorker.gpsFix.connect(self.updateGPSFix)
        self.gpsWorker.gpsLocation.connect(self.updateLocation)

        self.gpsThread.start()

    def setTPMSWarn(self, warn):
        if warn:
            self.infobar.tpmsWarn = True
            self.tpmsWarnLabel.setPixmap(self.tpms_warn_on)
        else:
            self.infobar.tpmsWarn = False
            self.tpmsWarnLabel.setPixmap(self.tpms_warn_off)

        try:
            self.tpmsWindow.setTPMSWarn(warn)
        except:
            print("Error sending tpms warn to tpms")

    def setTPMS(self, sensor):
        tire = sensor[0]
        self.tpms.setPressure(tire, sensor[1])
        self.tpms.setTemperature(tire, sensor[2])
        self.tpms.setWarn(tire, sensor[3])

        try:
            self.tpmsWindow.setTPMS(self.tpms, tire)
        except AttributeError:
            pass

    def initRuuvitagThread(self):
        conf_file = str(Path.home()) + "/.motorhome/motorhome.conf"
        config = configparser.ConfigParser()

        try:
            config.read(conf_file)
            mac = config['RuuviTag']['mac']
        except:
            return

        self.ruuviThread =  QThread()
        self.ruuviWorker = RuuviTag(mac)
        self.exit_signal.connect(self.ruuviWorker.stop)
        self.ruuviWorker.moveToThread(self.ruuviThread)

        self.ruuviWorker.finished.connect(self.ruuviThread.quit)
        self.ruuviWorker.finished.connect(self.ruuviWorker.deleteLater)
        self.ruuviThread.finished.connect(self.ruuviThread.deleteLater)

        self.ruuviThread.started.connect(self.ruuviWorker.run)

        self.ruuviWorker.exit_signal.connect(self.ruuviWorker.stop)

        self.ruuviWorker.temperature.connect(self.updateTemperature)
        self.ruuviWorker.humidity.connect(self.updateHumidity)
        self.ruuviWorker.pressure.connect(self.updatePressure)
        self.ruuviWorker.ruuvi_batt.connect(self.updateRuuviBatt)

        self.ruuviThread.started.connect(self.ruuviWorker.run)

        self.ruuviThread.start()

    def updateTemperature(self, temperature):
        if math.isnan(temperature):
            return

        self.infobar.temperature = temperature
        self.ruuvi.temperature = temperature

        try:
            self.ruuviWindow.updateTemperature(self.ruuvi.temperature)
        except AttributeError:
            pass

        if self.ruuvi.temperature < 3.0:
            self.tempWarnLabel.setPixmap(self.temp_warn_on)
        elif self.ruuvi.temperature > 3.2:
            self.tempWarnLabel.setPixmap(self.temp_warn_off)

        self.tempInfoLabel.setText("{0:d}".format(round(self.ruuvi.temperature)) + "\u2103")

    def updateHumidity(self, humidity):
        if math.isnan(humidity):
            return
        self.ruuvi.humidity = humidity
        try:
            self.ruuviWindow.updateHumidity(self.ruuvi.humidity)
        except AttributeError:
            pass

    def updatePressure(self, pressure):
        if math.isnan(pressure):
            return

        self.ruuvi.pressure = pressure
        try:
            self.ruuviWindow.updatePressure(self.ruuvi.pressure)
        except AttributeError:
            pass

    def updateRuuviBatt(self, voltage):
        if math.isnan(voltage):
            return

        self.ruuvi.vbatt = voltage
        try:
            self.ruuviWindow.updateRuuviBatt(self.ruuvi.vbatt)
        except AttributeError:
            pass

    def updateGPSFix(self, fix):
        if fix <= 1:
            self.infobar.gpsFix = False
        else:
            self.infobar.gpsFix = True

        self.gps.fix = fix

        if self.infobar.gpsFix:
            self.gpsInfoLabel.setPixmap(self.gps_connected)
        else:
            self.gpsInfoLabel.setPixmap(self.gps_disconnected)

        try:
            self.gpsWindow.updateFix(self.gps.fix)
        except AttributeError:
            pass

    def updateLocation(self, location):
        self.gps.lat = location[0]
        self.gps.lon = location[1]
        self.gps.alt = location[2]

        try:
            self.gpsWindow.updateLocation(self.gps)
        except AttributeError:
            pass

    def updateRecording(self, recording):
        if recording:
            self.recInfoLabel.setPixmap(self.rec_on)
        else:
            self.recInfoLabel.setPixmap(self.rec_off)

    def poweroff(self):
        os.system("sudo shutdown -h now")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.exit_signal.emit()
#            self.virbThread.join()
#            self.TPMSThread.join()
            self.datetimer.stop()
            sys.exit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainApp()
    sys.exit(app.exec_())

