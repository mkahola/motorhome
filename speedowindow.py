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

class SpeedoWindow(QWidget):
    def createWindow(self, temperature):
        parent = None
        super(SpeedoWindow, self).__init__(parent)

        self.setStyleSheet("background-color: #323232;")
        self.setWindowTitle("Speedometer")
        self.prefix = str(Path.home()) + "/.motorhome/res/"

        web = QWebView()
        web.settings().setAttribute(QWebSettings.JavascriptEnabled, True)
        web.settings().setAttribute(QWebSettings.LocalContentCanAccessRemoteUrls, True);
        web.load(QUrl("http://my.dashboard.com"))

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

        # time
        self.timeLabel = QLabel()
        self.timeLabel.setStyleSheet("QLabel {color: white; font: 24px}")
        self.timeLabel.setAlignment(Qt.AlignCenter)

        # TPMS warn light
        #self.tpms_warn_off = QPixmap(self.prefix + "tpms_warn_off.png").scaled(32, 32, Qt.KeepAspectRatio)
        self.tpms_warn_off = QPixmap("")
        self.tpms_warn_on = QPixmap(self.prefix + "tpms_warn_on.png").scaled(32, 32, Qt.KeepAspectRatio)
        self.tpmsWarnLabel = QLabel()
        self.tpmsWarnLabel.setPixmap(self.tpms_warn_off)

        # Ruuvitag
        self.tempInfoLabel = QLabel()
        self.tempInfoLabel.setStyleSheet("QLabel {color: white; font: 24px}")

        self.temp_warn_off = QPixmap("")
        self.temp_warn_on = QPixmap(self.prefix + "snowflake.png").scaled(32, 32, Qt.KeepAspectRatio)
        self.tempWarnLabel = QLabel()

        self.updateTemperature(temperature)
        self.updateTime(datetime.now())

        #infobar
        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.tpmsWarnLabel, alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.tempWarnLabel, alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.tempInfoLabel, alignment=Qt.AlignTop|Qt.AlignRight)
        hbox1.addWidget(self.timeLabel, alignment=Qt.AlignTop|Qt.AlignRight)

        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.tpmsWarnLabel, alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.timeLabel, alignment=Qt.AlignTop|Qt.AlignRight)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addWidget(web)
        vbox.addWidget(homeButton, alignment=Qt.AlignCenter)
        self.setLayout(vbox)

        self.showMaximized()

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

    def exit(self):
        self.close()


