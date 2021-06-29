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
from ruuvi import RuuviTag, Ruuvi

class RuuviWindow(QWidget):
    def createWindow(self, ruuvi):
        parent = None
        super(RuuviWindow, self).__init__(parent)

        self.setStyleSheet("background-color: #323232;")
        self.setWindowTitle("Ruuvitag")
        self.prefix = str(Path.home()) + "/.motorhome/res/"

        outdoor = QLabel("OUTDOOR:")
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
        homeButton.setStyleSheet("background-color: #323232;"
                                 "border-style: outset;"
                                 "border-width: 0px;"
                                 "border-radius: 0px;"
                                 "border-color: #323232;"
                                 "font: 16px;"
                                 "color: black;"
                                 "min-width: 64px;"
                                 "min-height: 64px;"
                                 "max-width: 64px;"
                                 "max-height: 64px;"
                                 "padding: 0px;")
        homeButton.clicked.connect(self.exit)

        self.timeLabel = QLabel()
        self.timeLabel.setStyleSheet("QLabel {color: white; font: 24px}")

        # TPMS warn light
        #self.tpms_warn_off = QPixmap(self.prefix + "tpms_warn_off.png").scaled(32, 32, Qt.KeepAspectRatio)
        self.tpms_warn_off = QPixmap("")
        self.tpms_warn_on = QPixmap(self.prefix + "tpms_warn_on.png").scaled(32, 32, Qt.KeepAspectRatio)
        self.tpmsWarnLabel = QLabel()
        self.tpmsWarnLabel.setPixmap(self.tpms_warn_off)

        self.tempInfoLabel = QLabel()
        self.tempInfoLabel.setStyleSheet("QLabel {color: white; font: 24px}")

        self.temp_warn_off = QPixmap("")
        self.temp_warn_on = QPixmap(self.prefix + "snowflake.png").scaled(32, 32, Qt.KeepAspectRatio)
        self.tempWarnLabel = QLabel()

        self.updateTemperature(ruuvi.temperature)
        self.updateHumidity(ruuvi.humidity)
        self.updatePressure(ruuvi.pressure)
        self.updateRuuviBatt(ruuvi.vbatt)
        self.updateTime(datetime.now())

        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.tpmsWarnLabel, alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.tempWarnLabel, alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.tempInfoLabel, alignment=Qt.AlignTop|Qt.AlignRight)
        hbox1.addWidget(self.timeLabel, alignment=Qt.AlignTop|Qt.AlignRight)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addWidget(outdoor, alignment=Qt.AlignLeft|Qt.AlignVCenter)
        vbox.addWidget(self.temperatureLabel, alignment=Qt.AlignCenter|Qt.AlignVCenter)
        vbox.addWidget(self.humidityLabel, alignment=Qt.AlignCenter|Qt.AlignVCenter)
        vbox.addWidget(self.pressureLabel, alignment=Qt.AlignCenter|Qt.AlignVCenter)
        vbox.addWidget(self.voltageLabel, alignment=Qt.AlignRight)
        vbox.addWidget(homeButton, alignment=Qt.AlignCenter)

        self.setLayout(vbox)

        self.showMaximized()

    def updateTemperature(self, temperature):
        if math.isnan(temperature):
            self.temperatureLabel.setText("--\u2103")
            return
        if temperature < 3.0:
            self.tempWarnLabel.setPixmap(self.temp_warn_on)
        elif temperature > 3.2:
            self.tempWarnLabel.setPixmap(self.temp_warn_off)

        self.tempInfoLabel.setText("{0:d}".format(round(temperature)) + "\u2103")
        self.temperatureLabel.setText("{:.1f}".format(round(temperature, 1)) + "\u2103")

    def updateHumidity(self, humidity):
        if math.isnan(humidity):
            self.humidityLabel.setText("-- %")
            return
        self.humidityLabel.setText("{:.0f}".format(round(humidity)) + " %")

    def updatePressure(self, pressure):
        if math.isnan(pressure):
            self.pressureLabel.setText("-- hPa")
            return
        self.pressureLabel.setText("{:.0f}".format(round(pressure)) + " hPa")

    def updateRuuviBatt(self, vbatt):
        if math.isnan(vbatt):
            return
        if vbatt < 2.75:
            self.voltageLabel.setText("low batt: " + "{:.2f}".format(round(vbatt/1000, 2)) + " V")

    def updateTime(self, t):
        self.timeLabel.setText("{:02d}".format(t.hour) + ":" + "{:02d}".format(t.minute))

    def exit(self):
        self.close()
