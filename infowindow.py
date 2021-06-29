from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWebKit import *
from PyQt5.QtWebKitWidgets import *
from PyQt5 import QtWidgets, QtCore, QtGui

import time
import math
import configparser
from datetime import datetime, timedelta
from pathlib import Path

class InfoWindow(QWidget):
    def createWindow(self, temperature):
        parent = None
        super(InfoWindow, self).__init__(parent)

        self.setStyleSheet("background-color: #323232;")
        self.setWindowTitle("Dashcam")
        self.prefix = str(Path.home()) + "/.motorhome/res/"

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

        self.tempInfoLabel = QLabel()
        self.tempInfoLabel.setStyleSheet("QLabel {color: white; font: 24px}")

        self.temp_warn_off = QPixmap("")
        self.temp_warn_on = QPixmap(self.prefix + "snowflake.png").scaled(32, 32, Qt.KeepAspectRatio)
        self.tempWarnLabel = QLabel()

        self.updateTemperature(temperature)
        self.updateTime(datetime.now())

        # TPMS warn light
        #self.tpms_warn_off = QPixmap(self.prefix + "tpms_warn_off.png").scaled(32, 32, Qt.KeepAspectRatio)
        self.tpms_warn_off = QPixmap("")
        self.tpms_warn_on = QPixmap(self.prefix + "tpms_warn_on.png").scaled(32, 32, Qt.KeepAspectRatio)
        self.tpmsWarnLabel = QLabel()
        self.tpmsWarnLabel.setPixmap(self.tpms_warn_off)

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

        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.tpmsWarnLabel, alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.timeLabel, alignment=Qt.AlignTop|Qt.AlignRight)

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

        self.showMaximized()

    def updateTime(self, t):
        self.timeLabel.setText("{:02d}".format(t.hour) + ":" + "{:02d}".format(t.minute))

    def updateTemperature(self, temperature):
        if math.isnan(temperature):
            return
        if temperature < 3.0:
            self.tempWarnLabel.setPixmap(self.temp_warn_on)
        elif temperature > 3.2:
            self.tempWarnLabel.setPixmap(self.temp_warn_off)

        self.tempInfoLabel.setText("{0:d}".format(round(temperature)) + "\u2103")
        self.temperatureLabel.setText("{:.1f}".format(round(temperature, 1)) + "\u2103")

    def exit(self):
        self.close()


