from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import QtWidgets, QtCore, QtGui

import time
import math
from datetime import datetime, timedelta
from pathlib import Path
from ruuvi import Ruuvi

class RuuviWindow(QWidget):
    info = pyqtSignal(dict)

    def createWindow(self, infobar, ruuvi):
        parent = None
        super(RuuviWindow, self).__init__(parent)

        self.setStyleSheet(open('res/childs.css', 'r').read())
        self.setWindowTitle("Ruuvitag")
        self.prefix = str(Path.home()) + "/.motorhome/res/"

        outdoor = QLabel("OUTDOOR")
        outdoor.setStyleSheet("font: bold 32px;"
                              "color: white;")

        self.temperatureLabel = QLabel()
        self.temperatureLabel.setStyleSheet("font: bold 48px;"
                                            "color: white;")

        self.humidityLabel = QLabel()
        self.humidityLabel.setStyleSheet("font: bold 48px;"
                                         "color: white;")

        self.pressureLabel = QLabel()
        self.pressureLabel.setStyleSheet("font: bold 48px;"
                                         "color: white;")

        self.voltageLabel = QLabel()
        self.voltageLabel.setStyleSheet("font: bold 24px;"
                                        "color: yellow")

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

        self.updateTime(datetime.now())
        self.updateTPMSWarn(infobar.tpmsWarn)
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

        self.updateTemperature(ruuvi.temperature)
        self.updateHumidity(ruuvi.humidity)
        self.updatePressure(ruuvi.pressure)
        self.updateRuuviBatt(ruuvi.vbatt)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addWidget(outdoor, alignment=Qt.AlignLeft|Qt.AlignVCenter)
        vbox.addWidget(self.temperatureLabel, alignment=Qt.AlignCenter|Qt.AlignVCenter)
        vbox.addWidget(self.humidityLabel, alignment=Qt.AlignCenter|Qt.AlignVCenter)
        vbox.addWidget(self.pressureLabel, alignment=Qt.AlignCenter|Qt.AlignVCenter)
        vbox.addWidget(self.voltageLabel, alignment=Qt.AlignRight)
        vbox.addWidget(homeButton, alignment=Qt.AlignCenter)

        self.setLayout(vbox)

        self.showFullScreen()

    def updateTemperature(self, temperature):
        if math.isnan(temperature):
            self.temperatureLabel.setText("--\u2103")
            return
        if temperature < 3.0:
            self.tempWarnLabel.setPixmap(self.temp_warn_on)
        elif temperature > 3.2:
            self.tempWarnLabel.setPixmap(self.temp_warn_off)

        self.tempInfoLabel.setText("{0:d}".format(round(temperature)) + "\u2103")
        self.temperatureLabel.setText("{:.2f}".format(round(temperature, 2)) + "\u2103")

    def updateHumidity(self, humidity):
        if math.isnan(humidity):
            self.humidityLabel.setText("-- %")
            return
        self.humidityLabel.setText("{:.2f}".format(round(humidity, 2)) + " %")

    def updatePressure(self, pressure):
        if math.isnan(pressure):
            self.pressureLabel.setText("-- hPa")
            return
        self.pressureLabel.setText("{:.2f}".format(round(pressure, 2)) + " hPa")

    def updateRuuviBatt(self, vbatt):
        if math.isnan(vbatt):
            return
        if vbatt < 2.75:
            self.voltageLabel.setText("low batt: " + "{:.2f}".format(round(vbatt, 2)) + " V")

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
