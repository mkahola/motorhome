from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import QtWidgets, QtCore, QtGui

import time
import math
import configparser
from datetime import datetime, timedelta
import subprocess
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

class AppsWindow(QWidget):
    info = pyqtSignal()

    def createWindow(self, infobar):
        parent = None
        super(AppsWindow, self).__init__(parent)

        size = 64

        self.setStyleSheet(stylesheet)
        self.setWindowTitle("Applications")
        self.prefix = str(Path.home()) + "/.motorhome/res/"

        # apps
        self.autoButton = QToolButton(self)
        self.autoButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.autoButton.setIcon(QIcon(self.prefix + 'android_auto.png'))
        self.autoButton.setText("Android Auto")
        self.autoButton.setIconSize(QSize(size, size))
        self.autoButton.clicked.connect(self.launch_android_auto)

        self.ytmusicButton = QToolButton(self)
        self.ytmusicButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.ytmusicButton.setIcon(QIcon(self.prefix + 'youtube_music.png'))
        self.ytmusicButton.setText("Youtube Music")
        self.ytmusicButton.setIconSize(QSize(size, size))
        self.ytmusicButton.clicked.connect(self.launch_ytmusic)

        self.areenaButton = QToolButton(self)
        self.areenaButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.areenaButton.setIcon(QIcon(self.prefix + 'yle_areena.png'))
        self.areenaButton.setText("Yle Areena")
        self.areenaButton.setIconSize(QSize(size, size))
        self.areenaButton.clicked.connect(self.launch_areena)

        self.netflixButton = QToolButton(self)
        self.netflixButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.netflixButton.setIcon(QIcon(self.prefix + 'netflix.png'))
        self.netflixButton.setText("Netflix")
        self.netflixButton.setIconSize(QSize(size, size))
        self.netflixButton.clicked.connect(self.launch_netflix)

        self.viihdeButton = QToolButton(self)
        self.viihdeButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.viihdeButton.setIcon(QIcon(self.prefix + 'elisa_viihde.png'))
        self.viihdeButton.setText("Elisa Viihde")
        self.viihdeButton.setIconSize(QSize(size, size))
        self.viihdeButton.clicked.connect(self.launch_viihde)

        self.radiotButton = QToolButton(self)
        self.radiotButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.radiotButton.setIcon(QIcon(self.prefix + 'radiot.png'))
        self.radiotButton.setText("Radiot.fi")
        self.radiotButton.setIconSize(QSize(size, size))
        self.radiotButton.clicked.connect(self.launch_radiot)

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

        grid = QGridLayout()
        grid.addWidget(self.autoButton, 0, 0)
        grid.addWidget(self.ytmusicButton, 0, 1)
        grid.addWidget(self.areenaButton, 0, 2)
        grid.addWidget(self.netflixButton, 1, 0)
        grid.addWidget(self.viihdeButton, 1, 1)
        grid.addWidget(self.radiotButton, 1, 2)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addLayout(grid)
        vbox.addWidget(homeButton, alignment=Qt.AlignCenter)

        self.setLayout(vbox)

        self.showFullScreen()

    def launch_android_auto(self):
        print("appswindow: Launching android auto")

        try:
            subprocess.Popen(['/home/pi/openauto/bin/autoapp'])
        except:
            print("unable to launch android auto")

        self.exit()

    def launch_ytmusic(self):
        print("appswindow: Launching Youtube Music")

        try:
            subprocess.Popen(['chromium-browser', '--start-fullscreen', '--app=https://music.youtube.com'])
        except:
            print("unable to launch Youtube Music")

        self.exit()

    def launch_areena(self):
        print("appswindow: Launching Yle Areena")

        try:
            subprocess.Popen(['chromium-browser', '--start-fullscreen', '--app=https://areena.yle.fi'])
        except:
            print("unable to launch Yle Areena")

        self.exit()

    def launch_netflix(self):
        print("appswindow: Launching Netflix")

        try:
            subprocess.Popen(['chromium-browser', '--start-fullscreen', '--app=https://www.netflix.com'])
        except:
            print("unable to launch Netflix")

        self.exit()

    def launch_viihde(self):
        print("appswindow: Launching Elisa Viihde")

        try:
            subprocess.Popen(['chromium-browser', '--start-fullscreen', '--app=https://www.elisaviihde.fi'])
        except:
            print("unable to launch Elisa Viihde")

        self.exit()

    def launch_radiot(self):
        print("appswindow: Launching Radiot.fi")

        try:
            subprocess.Popen(['chromium-browser', '--start-fullscreen', '--app=https://www.radiot.fi'])
        except:
            print("unable to launch Radiot.fi")

        self.exit()

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


