import PyQt5
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import QtWidgets, QtCore, QtGui

import time
import math
import configparser
import paho.mqtt.client as mqtt
from datetime import datetime, timedelta
from pathlib import Path
from tires import Tires

# The callback for when the client receives a CONNACK response from the MQTT se>
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker with result code " + str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("$SYS/#")

class TPMSWindow(QWidget):
    set_season = pyqtSignal(int)
    info = pyqtSignal(dict)

    def createWindow(self, infobar, tpms):
        parent = None
        super(TPMSWindow, self).__init__(parent)

        self.setStyleSheet(open('res/childs.css', 'r').read())
        self.setWindowTitle("TPMS")
        self.prefix = str(Path.home()) + "/.motorhome/res/"

        mqttBroker = 'localhost'
        self.client = mqtt.Client("TPMS_window")
        self.client.on_connect = on_connect
        self.client.connect(mqttBroker)

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
        self.updateTime(datetime.now())
        self.updateTPMSWarn(infobar.tpmsWarn)
        self.updateGPSFix(infobar.gpsFix)
        self.updateSpeed(infobar.speed)
        self.updateRecording(infobar.recording)

        #infobar
        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.tpmsWarnLabel, alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.tempWarnLabel, alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.gpsInfoLabel, alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.recInfoLabel, alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.gpsSpeedLabel, alignment=Qt.AlignTop|Qt.AlignRight)
        hbox1.addWidget(self.tempInfoLabel, alignment=Qt.AlignTop|Qt.AlignRight)
        hbox1.addWidget(self.timeLabel, alignment=Qt.AlignTop|Qt.AlignRight)
        # === infobar ===

        front_left = QLabel("Front Left")
        front_left.setStyleSheet("font: bold 20px;")

        front_right = QLabel("Front Right")
        front_right.setStyleSheet("font: bold 20px;")

        rear_left = QLabel("Rear Left")
        rear_left.setStyleSheet("font: bold 20px;")

        rear_right = QLabel("Rear Right")
        rear_right.setStyleSheet("font: bold 20px;")

        self.spear = QLabel()
        self.spear.setStyleSheet("font: bold 18px;")

        self.fl_pressure_label = QLabel()
        self.fl_pressure_label.setStyleSheet("font: bold 28px;")

        self.fr_pressure_label = QLabel()
        self.fr_pressure_label.setStyleSheet("font: bold 28px;")

        self.rl_pressure_label = QLabel()
        self.rl_pressure_label.setStyleSheet("font: bold 28px;")

        self.rr_pressure_label = QLabel()
        self.rr_pressure_label.setStyleSheet("font: bold 28px;")

        self.fl_temp_label = QLabel()
        self.fl_temp_label.setStyleSheet("font: bold 20px;")

        self.fr_temp_label = QLabel()
        self.fr_temp_label.setStyleSheet("font: bold 20px;")

        self.rl_temp_label = QLabel()
        self.rl_temp_label.setStyleSheet("font: bold 20px;")

        self.rr_temp_label = QLabel()
        self.rr_temp_label.setStyleSheet("font: bold 20px;")

        pixmap = QPixmap(self.prefix + "tire.png").scaled(128, 128, Qt.KeepAspectRatio)

        tire_fl_label = QLabel()
        tire_fl_label.setPixmap(pixmap)

        tire_fr_label = QLabel()
        tire_fr_label.setPixmap(pixmap)

        tire_rl_label = QLabel()
        tire_rl_label.setPixmap(pixmap)

        tire_rr_label = QLabel()
        tire_rr_label.setPixmap(pixmap)

        tireSelLabel = QLabel("Winter tires")
        tireSelLabel.setStyleSheet("QLabel {background: transparent; color: #1E90FF; font: 16px}")

        self.setTPMS(tpms, "FL")
        self.setTPMS(tpms, "FR")
        self.setTPMS(tpms, "RL")
        self.setTPMS(tpms, "RR")
        self.setTPMS(tpms, "Spear")

        vbox1 = QVBoxLayout()
        vbox1.addWidget(front_left, alignment=Qt.AlignCenter|Qt.AlignBottom)
        vbox1.addWidget(self.fl_pressure_label, alignment=Qt.AlignCenter|Qt.AlignBottom)
        vbox1.addWidget(self.fl_temp_label, alignment=Qt.AlignCenter|Qt.AlignTop)

        vbox2 = QVBoxLayout()
        vbox2.addWidget(front_right, alignment=Qt.AlignCenter|Qt.AlignBottom)
        vbox2.addWidget(self.fr_pressure_label,alignment=Qt.AlignCenter|Qt.AlignBottom)
        vbox2.addWidget(self.fr_temp_label, alignment=Qt.AlignCenter|Qt.AlignTop)

        hbox2 = QHBoxLayout()
        hbox2.addLayout(vbox1)
        hbox2.addWidget(tire_fl_label, alignment=Qt.AlignLeft)
        hbox2.addWidget(tire_fr_label, alignment=Qt.AlignRight)
        hbox2.addLayout(vbox2)

        vbox3 = QVBoxLayout()
        vbox3.addWidget(rear_left, alignment=Qt.AlignCenter|Qt.AlignBottom)
        vbox3.addWidget(self.rl_pressure_label, alignment=Qt.AlignCenter|Qt.AlignBottom)
        vbox3.addWidget(self.rl_temp_label, alignment=Qt.AlignCenter|Qt.AlignTop)

        vbox4 = QVBoxLayout()
        vbox4.addWidget(rear_right, alignment=Qt.AlignCenter|Qt.AlignBottom)
        vbox4.addWidget(self.rr_pressure_label, alignment=Qt.AlignCenter|Qt.AlignBottom)
        vbox4.addWidget(self.rr_temp_label, alignment=Qt.AlignCenter|Qt.AlignTop)

        hbox3 = QHBoxLayout()
        hbox3.addLayout(vbox3)
        hbox3.addWidget(tire_rl_label, alignment=Qt.AlignLeft)
        hbox3.addWidget(tire_rr_label, alignment=Qt.AlignRight)
        hbox3.addLayout(vbox4)

        hbox4 = QHBoxLayout()
        hbox4.addWidget(self.spear, alignment=Qt.AlignLeft)

        hbox5 = QHBoxLayout()
        hbox5.addWidget(homeButton, alignment=Qt.AlignCenter)

        vbox5 = QVBoxLayout()
        vbox5.addLayout(hbox1)
        vbox5.addLayout(hbox2)
        vbox5.addLayout(hbox3)
        vbox5.addLayout(hbox4)
        vbox5.addLayout(hbox5)

        self.setLayout(vbox5)

        self.showFullScreen()

    def setTPMSWarn(self, warn):
        if warn:
            self.tpmsWarnLabel.setPixmap(self.tpms_warn_on)
        else:
            self.tpmsWarnLabel.setPixmap(self.tpms_warn_off)

    def setTPMS(self, tpms, tire):
        if tire == "FL":
            if math.isnan(tpms.front_left.pressure):
                self.fl_pressure_label.setText(" -- bar")
                self.fl_temp_label.setText("--\u2103")
            else:
                self.fl_pressure_label.setText("{:.1f}".format(round(tpms.front_left.pressure, 1)) + " bar")
                self.fl_temp_label.setText("{:0d}".format(round(tpms.front_left.temperature)) + "\u2103")
                if tpms.front_left.warn:
                    self.fl_pressure_label.setStyleSheet("font: bold 24px;"
                                                         "color: #ff9933;")
                    self.fl_temp_label.setStyleSheet("font: bold 20px;"
                                                     "color: #ff9933;")
                else:
                    self.fl_pressure_label.setStyleSheet("font: bold 24px;"
                                                         "color: #73E420;")
                    self.fl_temp_label.setStyleSheet("font: bold 20px;"
                                                     "color: #73E420;")
        elif tire == "FR":
            if math.isnan(tpms.front_right.pressure):
                self.fr_pressure_label.setText(" -- bar")
                self.fr_temp_label.setText("--\u2103")
            else:
                self.fr_pressure_label.setText("{:.1f}".format(round(tpms.front_right.pressure, 1)) + " bar")
                self.fr_temp_label.setText("{0:d}".format(round(tpms.front_right.temperature)) + "\u2103")
                if tpms.front_right.warn:
                    self.fr_pressure_label.setStyleSheet("font: bold 24px;"
                                                         "color: #ff9933;")
                    self.fr_temp_label.setStyleSheet("font: bold 20px;"
                                                     "color: #ff9933;")
                else:
                    self.fr_pressure_label.setStyleSheet("font: bold 24px;"
                                                         "color: #73E420;")
                    self.fr_temp_label.setStyleSheet("font: bold 20px;"
                                                     "color: #73E420;")
        elif tire == "RL":
            if math.isnan(tpms.rear_left.pressure):
                self.rl_pressure_label.setText(" -- bar")
                self.rl_temp_label.setText("--\u2103")
            else:
                self.rl_pressure_label.setText("{:.1f}".format(round(tpms.rear_left.pressure, 1)) + " bar")
                self.rl_temp_label.setText("{0:d}".format(round(tpms.rear_left.temperature)) + "\u2103")
                if tpms.rear_left.warn:
                    self.rl_pressure_label.setStyleSheet("font: bold 24px;"
                                                         "color: #ff9933;")
                    self.rl_temp_label.setStyleSheet("font: bold 20px;"
                                                     "color: #ff9933;")
                else:
                    self.rl_pressure_label.setStyleSheet("font: bold 24px;"
                                                         "color: #73E420;")
                    self.rl_temp_label.setStyleSheet("font: bold 20px;"
                                                     "color: #73E420;")
        elif tire == "RR":
            if math.isnan(tpms.rear_right.pressure):
                self.rr_pressure_label.setText(" -- bar")
                self.rr_temp_label.setText("--\u2103")
            else:
                self.rr_pressure_label.setText("{:.1f}".format(round(tpms.rear_right.pressure, 1)) + " bar")
                self.rr_temp_label.setText("{0:d}".format(round(tpms.rear_right.temperature)) + "\u2103")
                if tpms.rear_right.warn:
                    self.rr_pressure_label.setStyleSheet("font: bold 24px;"
                                                         "color: #ff9933;")
                    self.rr_temp_label.setStyleSheet("font: bold 20px;"
                                                     "color: #ff9933;")
                else:
                    self.rr_pressure_label.setStyleSheet("font: bold 24px;"
                                                         "color: #73E420;")
                    self.rr_temp_label.setStyleSheet("font: bold 20px;"
                                                     "color: #73E420;")
        elif tire == "Spear":
            if not math.isnan(tpms.spear.pressure):
                self.spear.setText("Spear     {:.1f}".format(round(tpms.spear.pressure, 1)) + " bar / {0:d}".format(round(tpms.spear.temperature)) + "\u2103")

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
        self.client.disconnect()
        self.close()
