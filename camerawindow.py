from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWebKit import *
from PyQt5.QtWebKitWidgets import *
from PyQt5 import QtWidgets, QtCore, QtGui

import time
from datetime import datetime, timedelta
from pathlib import Path

from virb import Virb
from camcorder import Camcorder

class CameraWindow(QWidget):
    stop_preview = pyqtSignal()

    def createWindow(self, virb):
        parent = None
        super(CameraWindow, self).__init__(parent)

        self.virb = virb
        self.previewScale = 80

        self.setStyleSheet("background-color: #323232;")
        self.setWindowTitle("Dashcam")
        self.prefix = str(Path.home()) + "/.motorhome/res/"

        self.recButton = QPushButton("", self)
        self.recButton.setIcon(QIcon(self.prefix + 'rec.png'))
        self.recButton.setIconSize(QSize(64, 64))
        self.recButton.setCheckable(True)
        self.recButton.clicked.connect(self.record)
        self.recButton.setStyleSheet("background-color: darkgrey;"
                                "border-style: outset;"
                                "border-width: 2px;"
                                "border-radius: 10px;"
                                "border-color: beige;"
                                "font: bold 32px;"
                                "color: red;"
                                "min-width: 64px;"
                                "min-height: 64px;"
                                "max-width: 64px;"
                                "max-height: 64px;"
                                "padding: 12px;")

        self.snapshotButton = QPushButton("", self)
        self.snapshotButton.setIcon(QIcon(self.prefix + 'snapshot.png'))
        self.snapshotButton.setIconSize(QSize(64, 64))
        self.snapshotButton.clicked.connect(self.snapshot)
        self.snapshotButton.setStyleSheet("background-color: darkgrey;"
                                     "border-style: outset;"
                                     "border-width: 2px;"
                                     "border-radius: 10px;"
                                     "border-color: beige;"
                                     "font: bold 32px;"
                                     "color: black;"
                                     "min-width: 64px;"
                                     "min-height: 64px;"
                                     "max-width: 64px;"
                                     "max-height: 64px;"
                                     "padding: 12px;")

        self.previewLabel = QLabel("No preview available", self)
        self.previewLabel.setStyleSheet("background-color: black;"
                                        "border-style: outset;"
                                        "border-width: 1px;"
                                        "border-radius: 8px;"
                                        "border-color: beige;"
                                        "font: 16px;"
                                        "color: white;"
                                        "min-width: 565px;"
                                        "min-height: 320px;"
                                        "padding: 4px;")
        self.previewLabel.setAlignment(Qt.AlignCenter)

        if not self.virb.ip:
            self.recButton.setEnabled(False)
            self.snapshotButton.setEnabled(False)

        self.virbBattLabel = QLabel()
        self.virbBattLabel.setText(" VBat " + self.virb.vbat + "%")
        self.virbBattLabel.setStyleSheet("QLabel {color: white; font: bold 16px}")
        self.virbBattLabel.setAlignment(Qt.AlignRight)

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
        self.tpms_warn_off = QPixmap("")
        #self.tpms_warn_off = QPixmap(self.prefix + "tpms_warn_off.png").scaled(32, 32, Qt.KeepAspectRatio)
        self.tpms_warn_on = QPixmap(self.prefix + "tpms_warn_on.png").scaled(32, 32, Qt.KeepAspectRatio)
        self.tpmsWarnLabel = QLabel()
        self.tpmsWarnLabel.setPixmap(self.tpms_warn_off)

        self.updateTime(datetime.now())

        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.tpmsWarnLabel, alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.timeLabel, alignment=Qt.AlignTop|Qt.AlignRight)

        vbox1 = QVBoxLayout()
        vbox1.addWidget(self.recButton, alignment=Qt.AlignCenter)
        vbox1.addWidget(self.snapshotButton, alignment=Qt.AlignCenter)
        vbox1.addWidget(self.virbBattLabel, alignment=Qt.AlignCenter)

        hbox2 = QHBoxLayout()
        hbox2.setSpacing(20)
        hbox2.addLayout(vbox1)
        hbox2.addWidget(self.previewLabel)

        vbox2 = QVBoxLayout()
        vbox2.addLayout(hbox1)
        vbox2.addLayout(hbox2)
        vbox2.addWidget(homeButton, alignment=Qt.AlignCenter)
        self.setLayout(vbox2)

        self.initPreviewThread()

        self.showMaximized()

    def initPreviewThread(self):
        if not self.virb.ip:
            return

        self.previewThread = QThread()
        self.previewWorker = Camcorder(self.virb.ip)
        self.stop_preview.connect(self.previewWorker.stop_preview)
        self.previewWorker.moveToThread(self.previewThread)
        self.previewWorker.finished.connect(self.previewThread.quit)
        self.previewWorker.finished.connect(self.previewWorker.deleteLater)
        self.previewThread.finished.connect(self.previewThread.deleteLater)
        self.previewThread.started.connect(self.previewWorker.live_preview)

        self.previewWorker.image.connect(self.updatePreview)

        self.previewThread.start()

    def initStartRecThread(self):
        if not self.virb.ip:
            return

        self.startRecThread = QThread()
        self.startRecWorker = Camcorder(self.ip)
        self.startRecWorker.moveToThread(self.startRecThread)
        self.startRecWorker.finished.connect(self.startRecThread.quit)
        self.startRecWorker.finished.connect(self.startRecWorker.deleteLater)
        self.startRecThread.finished.connect(self.startRecThread.deleteLater)
        self.startRecThread.started.connect(self.startRecWorker.start_recording)

        self.TabWidget.setTabIcon(self.dc_index, QIcon(self.prefix + 'cam_rec.png'))
        self.TabWidget.setIconSize(QtCore.QSize(32, 32))

        self.startRecThread.start()

        self.recording = True

    def initStopRecThread(self):
        if not self.recording:
            return

        self.stopRecThread = QThread()
        self.stopRecWorker = Camcorder(self.ip)
        self.stopRecWorker.moveToThread(self.stopRecThread)
        self.stopRecWorker.finished.connect(self.stopRecThread.quit)
        self.stopRecWorker.finished.connect(self.stopRecWorker.deleteLater)
        self.stopRecThread.finished.connect(self.stopRecThread.deleteLater)
        self.stopRecThread.started.connect(self.stopRecWorker.stop_recording)

        self.TabWidget.setTabIcon(self.dc_index, QIcon(self.prefix + 'camera.png'))
        self.TabWidget.setIconSize(QtCore.QSize(32, 32))

        self.stopRecThread.start()

    def initSnapshotThread(self, button):
        if not self.virb.ip:
            return

        self.snapshotThread = QThread()
        self.snapshotWorker = Camcorder(self.ip)
        self.snapshotWorker.moveToThread(self.snapshotThread)
        self.snapshotWorker.finished.connect(self.snapshotThread.quit)
        self.snapshotWorker.finished.connect(self.snapshotWorker.deleteLater)
        self.snapshotThread.finished.connect(self.snapshotThread.deleteLater)
        self.snapshotThread.finished.connect(self.updateSnapshotButton)
        self.snapshotThread.started.connect(self.snapshotWorker.snapshot)

        self.snapshotThread.start()

    def record(self):
        if self.recButton.isChecked():
            self.recButton.setIcon(QIcon(self.prefix + 'stop.png'))
            self.recButton.setIconSize(QSize(64, 64))
            self.recButton.setStyleSheet("background-color: #373636;"
                                 "border-style: outset;"
                                 "border-width: 2px;"
                                 "border-radius: 10px;"
                                 "border-color: beige;"
                                 "font: bold 32px;"
                                 "color: red;"
                                 "min-width: 72px;"
                                 "min-height: 72px;"
                                 "padding: 12px;")
            self.initStartRecThread()
        else:
            # set autorecording when moving
            self.recButton.setIcon(QIcon(self.prefix + 'rec.png'))
            self.recButton.setIconSize(QSize(64, 64))
            self.recButton.setStyleSheet("background-color: darkgrey;"
                                 "border-style: outset;"
                                 "border-width: 2px;"
                                 "border-radius: 10px;"
                                 "border-color: beige;"
                                 "font: bold 32px;"
                                 "color: red;"
                                 "min-width: 72px;"
                                 "min-height: 72px;"
                                 "padding: 12px;")
            self.initStopRecThread()

    def snapshot(self):
        self.snapshotButton.setStyleSheet("background-color: #373636;"
                             "border-style: outset;"
                             "border-width: 2px;"
                             "border-radius: 10px;"
                             "border-color: beige;"
                             "font: bold 32px;"
                             "color: red;"
                             "min-width: 72px;"
                             "min-height: 72px;"
                             "padding: 12px;")
        self.snapshotButton.setEnabled(False)
        self.initSnapshotThread(button)

    def updateSnapshotButton(self):
        self.snapshotButton.setEnabled(True)
        self.sanpshotButton.setStyleSheet("background-color: darkgrey;"
                             "border-style: outset;"
                             "border-width: 2px;"
                             "border-radius: 10px;"
                             "border-color: beige;"
                             "font: bold 32px;"
                             "color: black;"
                             "min-width: 72px;"
                             "min-height: 72px;"
                             "padding: 12px;")

    def updatePreview(self, pixmap):
        self.previewLabel.setPixmap(pixmap.scaled(int(704*self.previewScale/100), int(396*self.previewScale/100),
                                                  QtCore.Qt.KeepAspectRatio))

    def setVirbIP(self, ip):
        self.virb.ip = ip
        self.recButton.setEnabled(True)
        self.snapshotButton.setEnabled(True)

        if not self.previewThread.isRunning():
            self.initPreviewThread()

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


