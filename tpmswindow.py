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
from tires import Tires
from tpms import TPMS

class TPMSWindow(QWidget):
    def createWindow(self, tpms):
        parent = None
        super(TPMSWindow, self).__init__(parent)

        self.setStyleSheet("background-color: #323232;")
        self.setWindowTitle("TPMS")
        self.prefix = str(Path.home()) + "/.motorhome/res/"

        homeButton = QPushButton()
        homeButton.setIcon(QIcon(self.prefix + 'home.png'))
        homeButton.setIconSize(QSize(64, 64))
        homeButton.setStyleSheet("background-color: #323232;"
                                 "border: 0px;"
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

        self.fl_pressure_label = QLabel()
        self.fl_pressure_label.setStyleSheet("font: bold 28px;"
                                             "color: #73E420;")

        self.fr_pressure_label = QLabel()
        self.fr_pressure_label.setStyleSheet("font: bold 28px;"
                                             "color: #73E420;")

        self.rl_pressure_label = QLabel()
        self.rl_pressure_label.setStyleSheet("font: bold 28px;"
                                             "color: #73E420;")

        self.rr_pressure_label = QLabel()
        self.rr_pressure_label.setStyleSheet("font: bold 28px;"
                                             "color: #74E420;")

        self.fl_temp_label = QLabel()
        self.fl_temp_label.setStyleSheet("font: bold 20px;"
                                         "color: #74E420;")
        self.fr_temp_label = QLabel()
        self.fr_temp_label.setStyleSheet("font: bold 20px;"
                                         "color: #74E420;")
        self.rl_temp_label = QLabel()
        self.rl_temp_label.setStyleSheet("font: bold 20px;"
                                         "color: #74E420;")
        self.rr_temp_label = QLabel()
        self.rr_temp_label.setStyleSheet("font: bold 20px;"
                                         "color: #74E420;")

        pixmap = QPixmap(self.prefix + "tire.png").scaled(128, 128, Qt.KeepAspectRatio)

        tire_fl_label = QLabel()
        tire_fl_label.setPixmap(pixmap)

        tire_fr_label = QLabel()
        tire_fr_label.setPixmap(pixmap)

        tire_rl_label = QLabel()
        tire_rl_label.setPixmap(pixmap)

        tire_rr_label = QLabel()
        tire_rr_label.setPixmap(pixmap)

        #self.tpms_warn_off = QPixmap(self.prefix + "tpms_warn_off.png").scaled(32, 32, Qt.KeepAspectRatio)
        self.tpms_warn_off = QPixmap("")
        self.tpms_warn_on = QPixmap(self.prefix + "tpms_warn_on.png").scaled(32, 32, Qt.KeepAspectRatio)
        self.tpmsWarnLabel = QLabel()
        self.tpmsWarnLabel.setPixmap(self.tpms_warn_off)

        self.updateTime(datetime.now())
        self.setTPMS(tpms)

        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.tpmsWarnLabel, alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.timeLabel, alignment=Qt.AlignTop|Qt.AlignRight)

        vbox1 = QVBoxLayout()
        vbox1.addWidget(self.fl_pressure_label, alignment=Qt.AlignCenter|Qt.AlignBottom)
        vbox1.addWidget(self.fl_temp_label, alignment=Qt.AlignCenter|Qt.AlignTop)

        vbox2 = QVBoxLayout()
        vbox2.addWidget(self.fr_pressure_label,alignment=Qt.AlignCenter|Qt.AlignBottom)
        vbox2.addWidget(self.fr_temp_label, alignment=Qt.AlignCenter|Qt.AlignTop)

        hbox2 = QHBoxLayout()
        hbox2.addLayout(vbox1)
        hbox2.addWidget(tire_fl_label, alignment=Qt.AlignLeft)
        hbox2.addWidget(tire_fr_label, alignment=Qt.AlignRight)
        hbox2.addLayout(vbox2)

        vbox3 = QVBoxLayout()
        vbox3.addWidget(self.rl_pressure_label, alignment=Qt.AlignCenter|Qt.AlignBottom)
        vbox3.addWidget(self.rl_temp_label, alignment=Qt.AlignCenter|Qt.AlignTop)

        vbox4 = QVBoxLayout()
        vbox4.addWidget(self.rr_pressure_label, alignment=Qt.AlignCenter|Qt.AlignBottom)
        vbox4.addWidget(self.rr_temp_label, alignment=Qt.AlignCenter|Qt.AlignTop)

        hbox3 = QHBoxLayout()
        hbox3.addLayout(vbox3)
        hbox3.addWidget(tire_rl_label, alignment=Qt.AlignLeft)
        hbox3.addWidget(tire_rr_label, alignment=Qt.AlignRight)
        hbox3.addLayout(vbox4)

        vbox5 = QVBoxLayout()
        vbox5.addLayout(hbox1)
        vbox5.addLayout(hbox2)
        vbox5.addLayout(hbox3)
        vbox5.addWidget(homeButton, alignment=Qt.AlignCenter)

        self.setLayout(vbox5)

        self.showMaximized()

    def setTPMSWarn(self, warn):
        if warn:
            self.tpmsWarnLabel.setPixmap(self.tpms_warn_on)
        else:
            self.tpmsWarnLabel.setPixmap(self.tpms_warn_off)

    def setTPMS(self, tpms):
        flp = False
        frp = False
        rlp = False
        rrp = False
        flt = False
        frt = False
        rlt = False
        rrt = False

        if math.isnan(tpms.FrontLeftPressure):
            self.fl_pressure_label.setText(" -- bar")
            self.fl_pressure_label.setStyleSheet("font: bold 24px;"
                                                "color: #73E420;")
            flp = True
        if math.isnan(tpms.FrontRightPressure):
            self.fr_pressure_label.setText(" -- bar")
            self.fr_pressure_label.setStyleSheet("font: bold 24px;"
                                                "color: #73E420;")
            frp = True

        if math.isnan(tpms.RearLeftPressure):
            self.rl_pressure_label.setText(" -- bar")
            self.rl_pressure_label.setStyleSheet("font: bold 24px;"
                                                "color: #73E420;")
            rlp = True
        if math.isnan(tpms.RearRightPressure):
            self.rr_pressure_label.setText(" -- bar")
            self.rr_pressure_label.setStyleSheet("font: bold 24px;"
                                                "color: #73E420;")
            rrp = True
        if math.isnan(tpms.FrontLeftTemp):
            self.fl_temp_label.setText("--\u2103")
            self.fl_temp_label.setStyleSheet("font: bold 18px;"
                                             "color: #73E420;")
            flt = True
        if math.isnan(tpms.FrontRightTemp):
            self.fr_temp_label.setText("--\u2103")
            self.fr_temp_label.setStyleSheet("font: bold 18px;"
                                             "color: #73E420;")
            frt = True
        if math.isnan(tpms.RearLeftTemp):
            self.rl_temp_label.setText("--\u2103")
            self.rl_temp_label.setStyleSheet("font: bold 18px;"
                                             "color: #73E420;")
            rlt = True
        if math.isnan(tpms.RearRightTemp):
            self.rr_temp_label.setText("--\u2103")
            self.rr_temp_label.setStyleSheet("font: bold 18px;"
                                             "color: #73E420;")
            rrt = True

        #pressure
        if not flp:
            self.fl_pressure_label.setText("{:.1f}".format(round(tpms.FrontLeftPressure,1)) + " bar")
            if tpms.FrontLeftWarn:
                self.fl_pressure_label.setStyleSheet("font: bold 24px;"
                                                    "color: #ff9933;")
            else:
                self.fl_pressure_label.setStyleSheet("font: bold 24px;"
                                                    "color: #73E420;")

        if not frp:
            self.fr_pressure_label.setText("{:.1f}".format(round(tpms.FrontRightPressure,1)) + " bar")
            if tpms.FrontRightWarn:
                self.fr_pressure_label.setStyleSheet("font: bold 24px;"
                                                 "color: #ff9933;")
            else:
                self.fr_pressure_label.setStyleSheet("font: bold 24px;"
                                                 "color: #73E420;")

        if not rlp:
            self.rl_pressure_label.setText("{:.1f}".format(round(tpms.RearLeftPressure,1)) + " bar")
            if tpms.RearLeftWarn:
                self.rl_pressure_label.setStyleSheet("font: bold 24px;"
                                                     "color: #ff9933;")
            else:
                self.rl_pressure_label.setStyleSheet("font: bold 24px;"
                                                     "color: #73E420;")

        if not rrp:
            self.rr_pressure_label.setText("{:.1f}".format(round(tpms.RearRightPressure,1)) + " bar")
            if tpms.RearRightWarn:
                self.rr_pressure_label.setStyleSheet("font: bold 24px;"
                                                     "color: #ff9933;")
            else:
                self.rr_pressure_label.setStyleSheet("font: bold 24px;"
                                                     "color: #73E420;")

        #temperature
        if not flt:
            self.fl_temp_label.setText("{:0d}".format(round(tpms.FrontLeftTemp)) + "\u2103")
            if tpms.FrontLeftWarn:
                self.fl_temp_label.setStyleSheet("font: bold 18px;"
                                               "color: #ff9933;")
            else:
                self.fl_temp_label.setStyleSheet("font: bold 18px;"
                                                 "color: #73E420;")

        if not frt:
            self.fr_temp_label.setText("{0:d}".format(round(tpms.FrontRightTemp)) + "\u2103")
            if tpms.FrontRightWarn:
                self.fr_temp_label.setStyleSheet("font: bold 18px;"
                                                 "color: #ff9933;")
            else:
                self.fr_temp_label.setStyleSheet("font: bold 18px;"
                                                 "color: #73E420;")

        if not rlt:
            self.rl_temp_label.setText("{0:d}".format(round(tpms.RearLeftTemp)) + "\u2103")
            if tpms.RearLeftWarn:
                self.rl_temp_label.setStyleSheet("font: bold 18px;"
                                                 "color: #ff9933;")
            else:
                self.rl_temp_label.setStyleSheet("font: bold 18px;"
                                                 "color: #73E420;")

        if not rrt:
            self.rr_temp_label.setText("{0:d}".format(round(tpms.RearRightTemp)) + "\u2103")
            if tpms.RearRightWarn:
                self.rl_temp_label.setStyleSheet("font: bold 18px;"
                                                 "color: #ff9933;")
            else:
                self.rl_temp_label.setStyleSheet("font: bold 18px;"
                                                 "color: #73E420;")

    def updateTime(self, t):
        self.timeLabel.setText("{:02d}".format(t.hour) + ":" + "{:02d}".format(t.minute))

    def updateTemperature(self, temperature):
        if temperature < 3.0:
            self.tempWarnLabel.setPixmap(self.temp_warn_on)
        elif temperature > 3.2:
            self.tempWarnLabel.setPixmap(self.temp_warn_off)

        self.tempInfoLabel.setText("{0:d}".format(round(temperature)) + "\u2103")
        self.temperatureLabel.setText("{:.1f}".format(round(temperature, 1)) + "\u2103")


    def exit(self):
        self.close()


