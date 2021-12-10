#!/usr/bin/env python3
"""
Motorhome infotainment project
"""
import math
import sys
import os.path
import configparser
from pathlib import Path
from datetime import datetime

from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QLabel, QPushButton, QToolButton, QHBoxLayout, QVBoxLayout, QGridLayout
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QThread, QTimer, QSize, pyqtSignal

from tires import Tires
from virb import Virb
from ruuvi import Ruuvi
from mqtt_subscriber import MQTT
from searchvirb import SearchVirb

from speedowindow import SpeedoWindow
from camerawindow import CameraWindow
from tpmswindow import TPMSWindow
from gpswindow import GPSWindow
from ruuviwindow import RuuviWindow
from appswindow import AppsWindow
from infowindow import InfoWindow

def poweroff():
    """ power off the system """
    os.system("sudo shutdown -h now")

class InfoBar:
    """ Infobar on top of the screen """
    def __init__(self):
        self.time = datetime.now()
        self.temperature = math.nan
        self.tpmsWarn = False
        self.gpsFix = False
        self.speed = math.nan
        self.recording = False

    def get_temperature(self):
        """ get temperature """
        return self.temperature

    def get_tpms_warn(self):
        """ get TPMS warn status """
        return self.tpmsWarn

    def get_gps_fix(self):
        """ get GPS fix status """
        return self.gpsFix

    def get_speed(self):
        """ get speed """
        return self.speed

    def get_recording(self):
        """ get dashcam recording status """
        return self.recording

class GPS:
    """ GPS container """
    def __init__(self):
        self.lat = math.nan
        self.lon = math.nan
        self.alt = math.nan
        self.course = math.nan
        self.fix = 0
        self.speed = math.nan
        self.src = ""

    def get_speed(self):
        """ get GPS speed """
        return self.speed

    def set_speed(self, value):
        """ set GPS speed """
        self.speed = value

class MainApp(QMainWindow):
    stop_signal = pyqtSignal()
    exit_signal = pyqtSignal()
    set_season = pyqtSignal(int)
    info = pyqtSignal(dict)
    virb_ip = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Motorhome Info")
        self.setStyleSheet(open('res/motorhome.css', 'r').read())

        self.init_gui()

        # start threads
        self.initSensorThread()
        self.initSearchVirbThread()
        #self.initGPSThread()

        self.showFullScreen()
#        self.showMaximized()


    def init_gui(self):
        """ initialize GUI """
        self.prefix = str(Path.home()) + "/.motorhome/res/"

        # create infotainment windows
        self.speedoWindow = SpeedoWindow(parent=self)
        self.cameraWindow = CameraWindow(parent=self)
        self.tpmsWindow = TPMSWindow(parent=self)
        self.gpsWindow = GPSWindow(parent=self)
        self.ruuviWindow = RuuviWindow(parent=self)
        self.appsWindow = AppsWindow(parent=self)
        self.infoWindow = InfoWindow(parent=self)

        self.infobar = InfoBar()
        self.gps = GPS()

        self.virb = Virb()
        self.tpms = Tires()
        self.ruuvi = Ruuvi()
        self.centralWidget = QWidget()
        size = 64

        #speedometer
        speedoButton = QToolButton(self)
        speedoButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        speedoButton.setIcon(QIcon(self.prefix + 'speedo.png'))
        speedoButton.setText("Speedo")
        speedoButton.setIconSize(QSize(size, size))
        speedoButton.clicked.connect(self.createSpeedoWindow)

        # dashcam
        self.cameraButton = QToolButton(self)
        self.cameraButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.cameraButton.setIcon(QIcon(self.prefix + 'dashcam.png'))
        self.cameraButton.setText("Dashcam")
        self.cameraButton.setIconSize(QSize(size, size))
        self.cameraButton.clicked.connect(self.createCameraWindow)
        self.cameraButton.setEnabled(False)

        # tpms
        tpmsButton = QToolButton(self)
        tpmsButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        tpmsButton.setIcon(QIcon(self.prefix + 'tpms.png'))
        tpmsButton.setText("TPMS")
        tpmsButton.setIconSize(QSize(size, size))
        tpmsButton.clicked.connect(self.createTPMSWindow)

        # Navit
        navitButton = QToolButton(self)
        navitButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        navitButton.setIcon(QIcon(self.prefix + 'navit.png'))
        navitButton.setText("Navigation")
        navitButton.setIconSize(QSize(size, size))
        navitButton.clicked.connect(self.startNavigation)

        # GPS
        gpsButton = QToolButton(self)
        gpsButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        gpsButton.setIcon(QIcon(self.prefix + 'compass.png'))
        gpsButton.setText("Compass")
        gpsButton.setIconSize(QSize(size, size))
        gpsButton.clicked.connect(self.createGPSWindow)

        # ruuvitag
        ruuviButton = QToolButton(self)
        ruuviButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        ruuviButton.setIcon(QIcon(self.prefix + 'ruuvi.png'))
        ruuviButton.setText("Ruuvitag")
        ruuviButton.setIconSize(QSize(size, size))
        ruuviButton.clicked.connect(self.createRuuviWindow)

        # apps
        self.appsButton = QToolButton(self)
        self.appsButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.appsButton.setIcon(QIcon(self.prefix + 'apps.png'))
        self.appsButton.setText("Apps")
        self.appsButton.setIconSize(QSize(size, size))
        self.appsButton.clicked.connect(self.createAppsWindow)
        self.appsButton.setEnabled(False)

        # vehicle info
        infoButton = QToolButton(self)
        infoButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        infoButton.setIcon(QIcon(self.prefix + 'info_128x128.png'))
        infoButton.setText("Info")
        infoButton.setIconSize(QSize(size, size))
        infoButton.clicked.connect(self.createInfoWindow)

        # poweroff
        powerButton = QPushButton("", self)
        powerButton.setIcon(QIcon(self.prefix + 'power.png'))
        powerButton.setIconSize(QSize(32, 32))
        powerButton.clicked.connect(poweroff)

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

        self.datetimer = QTimer()
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
        self.gpsSpeedLabel = QLabel("-- km/h")

        #infobar
        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.tpmsWarnLabel, alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.tempWarnLabel, alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.gpsInfoLabel, alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.recInfoLabel, alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.gpsSpeedLabel, alignment=Qt.AlignTop|Qt.AlignRight)
        hbox1.addWidget(self.tempInfoLabel, alignment=Qt.AlignTop|Qt.AlignRight)
        hbox1.addWidget(self.timeLabel, alignment=Qt.AlignTop|Qt.AlignRight)

        grid = QGridLayout()
        grid.addWidget(speedoButton, 0, 0)
        grid.addWidget(self.cameraButton, 0, 1)
        grid.addWidget(tpmsButton, 0, 2)

        grid.addWidget(navitButton, 1, 0)
        grid.addWidget(gpsButton, 1, 1)
        grid.addWidget(ruuviButton, 1, 2)

        grid.addWidget(self.appsButton, 2, 0)
        grid.addWidget(infoButton, 2, 1)

        grid.setSpacing(10)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addLayout(grid)
        vbox.addWidget(powerButton, alignment=Qt.AlignRight)

        self.centralWidget.setLayout(vbox)
        self.setCentralWidget(self.centralWidget)

    def createSpeedoWindow(self):
        """ create window for speedometer """
        self.speedoWindow.create_window(self.infobar)
        self.info.connect(self.speedoWindow.update_infobar)
        self.speedoWindow.show()

    def createCameraWindow(self):
        """ create window for dashcam """
        self.cameraWindow.createWindow(self.infobar, self.virb)
        self.cameraWindow.recording.connect(self.getRecSignal)
        self.info.connect(self.cameraWindow.updateInfobar)
        self.cameraWindow.show()

    def createTPMSWindow(self):
        """ create window for tire pressure monitor system """
        self.tpmsWindow.createWindow(self.infobar, self.tpms)
        self.info.connect(self.tpmsWindow.updateInfobar)
        self.tpmsWindow.show()

    def startNavigation(self):
        """ Navit navigation """
        print("motorhome: Launching Navit navigation")
        try:
            os.system('/usr/bin/navit')
        except:
            print("motorhome: unable to launch Navit navigation")

    def createGPSWindow(self):
        """ create window for GPS data """
        self.gpsWindow.createWindow(self.infobar, self.gps)
        self.info.connect(self.gpsWindow.updateInfobar)
        self.gpsWindow.show()

    def createRuuviWindow(self):
        """ create window for Ruuvitag data """
        self.ruuviWindow.createWindow(self.infobar, self.ruuvi)
        self.info.connect(self.ruuviWindow.updateInfobar)
        self.ruuviWindow.show()

    def createAppsWindow(self):
        """ create window for 3rd party apps """
        self.appsWindow.createWindow(self.infobar)
        self.info.connect(self.appsWindow.updateInfobar)
        self.appsWindow.show()

    def createInfoWindow(self):
        """ create window for system information """
        self.infoWindow.createWindow(self.infobar, self.virb.ip)
        self.info.connect(self.infoWindow.updateInfobar)
        self.infoWindow.show()

    def getRecSignal(self, data):
        """ get dashcam recording status """
        self.infobar.recording = data
        self.updateRecording(self.infobar.recording)

    def updateTime(self):
        """ update date and time """
        t = datetime.now()
        self.timeLabel.setText("{:02d}".format(t.hour) + ":" + "{:02d}".format(t.minute))
        self.infobar.time = t

        data = dict(time=self.infobar.time,
                    temperature=self.infobar.temperature,
                    tpms=self.infobar.tpmsWarn,
                    gpsFix=self.infobar.gpsFix,
                    speed=self.infobar.speed,
                    recording=self.infobar.recording)
        self.info.emit(data)

    def initSearchVirbThread(self):
        """ initialize search for Garmin Virb ip """
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
        """ set Garmin Virb ip """
        self.virb.ip = ip
        self.virb_ip.emit(self.virb.ip)

        self.cameraButton.setEnabled(True)

        if self.virb.ip != "192.168.0.1":
            print("enabling apps button")
            self.appsButton.setEnabled(True)


        try:
            self.cameraWindow.setVirbIP(ip)
        except AttributeError:
            pass

    def setTPMSWarn(self, warn):
        """ Set TPMS warn on/off """
        if warn:
            self.infobar.tpmsWarn = True
            self.tpmsWarnLabel.setPixmap(self.tpms_warn_on)
        else:
            self.infobar.tpmsWarn = False
            self.tpmsWarnLabel.setPixmap(self.tpms_warn_off)

        try:
            self.tpmsWindow.setTPMSWarn(warn)
        except AttributeError:
            pass

    def setTPMS(self, sensor):
        """ set TPMS data """
        tire = sensor[0]
        self.tpms.set_pressure(tire, sensor[1])
        self.tpms.set_temperature(tire, sensor[2])
        self.tpms.set_warn(tire, sensor[3])

        try:
            self.tpmsWindow.setTPMS(self.tpms, tire)
        except AttributeError:
            pass

    def initSensorThread(self):
        """ initialize MQTT thread """
        self.sensorThread = QThread()
        self.sensorWorker = MQTT()
        self.exit_signal.connect(self.sensorWorker.stop)
        self.sensorWorker.moveToThread(self.sensorThread)

        self.sensorWorker.finished.connect(self.sensorThread.quit)
        self.sensorWorker.finished.connect(self.sensorWorker.deleteLater)
        self.sensorThread.finished.connect(self.sensorThread.deleteLater)

        self.sensorThread.started.connect(self.sensorWorker.run)
        self.sensorWorker.exit_signal.connect(self.sensorWorker.stop)

        """ ruuvitag signals """
        self.sensorWorker.temperature.connect(self.updateTemperature)
        self.sensorWorker.humidity.connect(self.updateHumidity)
        self.sensorWorker.pressure.connect(self.updatePressure)
        self.sensorWorker.ruuvi_batt.connect(self.updateRuuviBatt)

        """ tpms signals """
        self.sensorWorker.tpms.connect(self.setTPMS)
        self.sensorWorker.tpms_warn.connect(self.setTPMSWarn)

        """ gps signals """
        self.sensorWorker.gpsFix.connect(self.updateGPSFix)
        self.sensorWorker.gpsLocation.connect(self.updateLocation)

        self.sensorThread.started.connect(self.sensorWorker.run)

        self.sensorThread.start()

    def updateTemperature(self, temperature):
        """ update temperature """
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
        """ update humidity """
        if math.isnan(humidity):
            return
        self.ruuvi.humidity = humidity
        try:
            self.ruuviWindow.updateHumidity(self.ruuvi.humidity)
        except AttributeError:
            pass

    def updatePressure(self, pressure):
        """ update air pressure """
        if math.isnan(pressure):
            return

        self.ruuvi.pressure = pressure
        try:
            self.ruuviWindow.updatePressure(self.ruuvi.pressure)
        except AttributeError:
            pass

    def updateRuuviBatt(self, voltage):
        """ update Ruuvitag battery voltage """
        if math.isnan(voltage):
            return

        self.ruuvi.vbatt = voltage
        try:
            self.ruuviWindow.updateRuuviBatt(self.ruuvi.vbatt)
        except AttributeError:
            pass

    def updateGPSFix(self, fix):
        """ Update GPS fix status """
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
        """ update location """
        self.gps.lat = location[0]
        self.gps.lon = location[1]
        self.gps.alt = location[2]
        self.gps.speed = location[3]
        self.gps.course = location[4]
        self.gps.src = location[5]

        self.infobar.speed = self.gps.speed

        try:
            self.gpsWindow.updateLocation(self.gps)
        except AttributeError:
            pass

        self.gpsSpeedLabel.setText("{:d}".format(round(self.infobar.speed*3.6)) + " km/h")

    def updateRecording(self, recording):
        """ Update recording info on infobar """
        if recording:
            self.recInfoLabel.setPixmap(self.rec_on)
        else:
            self.recInfoLabel.setPixmap(self.rec_off)

    def keyPressEvent(self, event):
        """ check if ESC is pressed """
        if event.key() == Qt.Key_Escape:
            self.exit_signal.emit()
            self.datetimer.stop()
            sys.exit()

if __name__ == "__main__":
    APP = QApplication(sys.argv)
    WIN = MainApp()
    sys.exit(APP.exec_())
