import PyQt5
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWebKit import *
from PyQt5.QtWebKitWidgets import *
from PyQt5 import QtWidgets, QtCore, QtGui
from qtwidgets import Toggle, AnimatedToggle

import time
import math
import configparser
from datetime import datetime, timedelta
from pathlib import Path
from tires import Tires
from tpms import TPMS

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

class TPMSWindow(QWidget):
    set_season = pyqtSignal(int)
    info = pyqtSignal(dict)

    def createWindow(self, infobar, tpms):
        parent = None
        super(TPMSWindow, self).__init__(parent)

        self.setStyleSheet(stylesheet)
        self.setWindowTitle("TPMS")
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
        self.updateRecording(infobar.recording)

        #infobar
        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.tpmsWarnLabel, alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.tempWarnLabel, alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.gpsInfoLabel, alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.recInfoLabel, alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.tempInfoLabel, alignment=Qt.AlignTop|Qt.AlignRight)
        hbox1.addWidget(self.timeLabel, alignment=Qt.AlignTop|Qt.AlignRight)
        # === infobar ===

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

        # summer/winter tire selection
        self.tire_sel = AnimatedToggle(
            checked_color="#FF1E90FF",
            pulse_checked_color="#FF1E90FF"
        )
        self.tire_sel.clicked.connect(self.updateSeason)

        tireSelLabel = QLabel("Winter tires")
        tireSelLabel.setStyleSheet("QLabel {background: transparent; color: #1E90FF; font: 16px}")

        self.setTPMS(tpms, "FL")
        self.setTPMS(tpms, "FR")
        self.setTPMS(tpms, "RL")
        self.setTPMS(tpms, "RR")

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

        hbox_tmp = QHBoxLayout()
        hbox_tmp.addWidget(self.tire_sel, alignment=Qt.AlignLeft)
        hbox_tmp.addWidget(tireSelLabel,  alignment=Qt.AlignLeft)
        hbox_tmp.addStretch()

        hbox4 = QHBoxLayout()
        hbox4.addLayout(hbox_tmp)
        hbox4.addWidget(homeButton,    alignment=Qt.AlignCenter)
        hbox4.addStretch()

        vbox5 = QVBoxLayout()
        vbox5.addLayout(hbox1)
        vbox5.addLayout(hbox2)
        vbox5.addLayout(hbox3)
        vbox5.addLayout(hbox4)

        self.setLayout(vbox5)

        self.showFullScreen()

    def updateSeason(self, value):
        self.set_season.emit(value)

        if value:
            print("tpmswindow: season set to winter")
        else:
            print("tpmswindow: season set to summer")

    def setTPMSWarn(self, warn):
        if warn:
            self.tpmsWarnLabel.setPixmap(self.tpms_warn_on)
        else:
            self.tpmsWarnLabel.setPixmap(self.tpms_warn_off)

    def setTPMS(self, tpms, tire):
        if tire == "FL":
            if math.isnan(tpms.FrontLeftPressure):
                self.fl_pressure_label.setText(" -- bar")
                self.fl_pressure_label.setStyleSheet("font: bold 24px;"
                                                "color: #73E420;")

                self.fl_temp_label.setText("--\u2103")
                self.fl_temp_label.setStyleSheet("font: bold 20px;"
                                                 "color: #73E420;")
            else:
                self.fl_pressure_label.setText("{:.1f}".format(round(tpms.FrontLeftPressure,1)) + " bar")
                self.fl_temp_label.setText("{:0d}".format(round(tpms.FrontLeftTemp)) + "\u2103")
                if tpms.FrontLeftWarn:
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
            if math.isnan(tpms.FrontRightPressure):
                self.fr_pressure_label.setText(" -- bar")
                self.fr_pressure_label.setStyleSheet("font: bold 24px;"
                                                     "color: #73E420;")

                self.fr_temp_label.setText("--\u2103")
                self.fr_temp_label.setStyleSheet("font: bold 20px;"
                                                 "color: #73E420;")
            else:
                self.fr_pressure_label.setText("{:.1f}".format(round(tpms.FrontRightPressure,1)) + " bar")
                self.fr_temp_label.setText("{0:d}".format(round(tpms.FrontRightTemp)) + "\u2103")
                if tpms.FrontRightWarn:
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
            if math.isnan(tpms.RearLeftPressure):
                self.rl_pressure_label.setText(" -- bar")
                self.rl_pressure_label.setStyleSheet("font: bold 24px;"
                                                     "color: #73E420;")
                self.rl_temp_label.setText("--\u2103")
                self.rl_temp_label.setStyleSheet("font: bold 20px;"
                                                 "color: #73E420;")

            else:
                self.rl_pressure_label.setText("{:.1f}".format(round(tpms.RearLeftPressure,1)) + " bar")
                self.rl_temp_label.setText("{0:d}".format(round(tpms.RearLeftTemp)) + "\u2103")
                if tpms.RearLeftWarn:
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
            if math.isnan(tpms.RearRightPressure):
                self.rr_pressure_label.setText(" -- bar")
                self.rr_pressure_label.setStyleSheet("font: bold 24px;"
                                                    "color: #73E420;")

                self.rr_temp_label.setText("--\u2103")
                self.rr_temp_label.setStyleSheet("font: bold 20px;"
                                                 "color: #73E420;")
            else:
                self.rr_pressure_label.setText("{:.1f}".format(round(tpms.RearRightPressure,1)) + " bar")
                self.rr_temp_label.setText("{0:d}".format(round(tpms.RearRightTemp)) + "\u2103")
                if tpms.RearRightWarn:
                    self.rr_pressure_label.setStyleSheet("font: bold 24px;"
                                                         "color: #ff9933;")
                    self.rl_temp_label.setStyleSheet("font: bold 20px;"
                                                     "color: #ff9933;")
                else:
                    self.rr_pressure_label.setStyleSheet("font: bold 24px;"
                                                         "color: #73E420;")
                    self.rl_temp_label.setStyleSheet("font: bold 20px;"
                                                     "color: #73E420;")

    def updateInfobar(self, data):
        self.updateTime(data['time'])
        self.updateTemperature(data['temperature'])
        self.updateTPMSWarn(data['tpms'])
        self.updateGPSFix(data['gpsFix'])
        self.updateRecording(data['recording'])

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


