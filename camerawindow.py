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

from virb import Virb
from camcorder import Camcorder

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
        background-color: darkgrey;
        border-style: outset;
        border-width: 2px;
        border-radius: 10px;
        border-color: beige;
        font: bold 32px;
        color: red;
        min-width: 64px;
        min-height: 64px;
        max-width: 64px;
        max-height: 64px;
        padding: 12px;
    }
"""

class CameraWindow(QWidget):
    stop_preview = pyqtSignal()
    recording = pyqtSignal(bool)
    info = pyqtSignal(dict)

    def createWindow(self, infobar, virb):
        parent = None
        super(CameraWindow, self).__init__(parent)

        self.virb = virb
        self.previewScale = 80
        self.rec = infobar.recording

        self.setStyleSheet(stylesheet)
        self.setWindowTitle("Dashcam")
        self.prefix = str(Path.home()) + "/.motorhome/res/"

        self.recButton = QPushButton("", self)
        self.recButton.setCheckable(True)
        self.recButton.clicked.connect(self.record)

        if self.rec:
            self.recButton.setChecked(True)
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
        else:
            self.recButton.setChecked(False)
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

        self.snapshotButton = QPushButton("", self)
        self.snapshotButton.setIcon(QIcon(self.prefix + 'snapshot.png'))
        self.snapshotButton.setIconSize(QSize(64, 64))
        self.snapshotButton.clicked.connect(self.snapshot)

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
        self.virbBattLabel.setText(" N/A %")

        homeButton = QPushButton()
        homeButton.setIcon(QIcon(self.prefix + 'home.png'))
        homeButton.setIconSize(QSize(64, 64))
        homeButton.clicked.connect(self.exit)
        homeButton.setStyleSheet("background: transparent; border: 0px")

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

        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.tpmsWarnLabel, alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.tempWarnLabel, alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.gpsInfoLabel, alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.recInfoLabel, alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.tempInfoLabel, alignment=Qt.AlignTop|Qt.AlignRight)
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

        if self.virb.ip:
            self.updateBatt()
            self.timer=QTimer()
            self.timer.timeout.connect(self.updateBatt)
            self.timer.start(30*1000)

        self.showFullScreen()

    def initPreviewThread(self):
        if not self.virb.ip:
            return
        self.previewLabel.setText("")

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
        self.startRecWorker = Camcorder(self.virb.ip)
        self.startRecWorker.moveToThread(self.startRecThread)
        self.startRecWorker.finished.connect(self.startRecThread.quit)
        self.startRecWorker.finished.connect(self.startRecWorker.deleteLater)
        self.startRecThread.finished.connect(self.startRecThread.deleteLater)
        self.startRecThread.started.connect(self.startRecWorker.start_recording)

        self.startRecThread.start()

    def initStopRecThread(self):
        if not self.recording or not self.virb.ip:
            return

        self.stopRecThread = QThread()
        self.stopRecWorker = Camcorder(self.virb.ip)
        self.stopRecWorker.moveToThread(self.stopRecThread)
        self.stopRecWorker.finished.connect(self.stopRecThread.quit)
        self.stopRecWorker.finished.connect(self.stopRecWorker.deleteLater)
        self.stopRecThread.finished.connect(self.stopRecThread.deleteLater)
        self.stopRecThread.started.connect(self.stopRecWorker.stop_recording)

        self.stopRecThread.start()

    def initSnapshotThread(self, button):
        if not self.virb.ip:
            return

        self.snapshotThread = QThread()
        self.snapshotWorker = Camcorder(self.virb.ip)
        self.snapshotWorker.moveToThread(self.snapshotThread)
        self.snapshotWorker.finished.connect(self.snapshotThread.quit)
        self.snapshotWorker.finished.connect(self.snapshotWorker.deleteLater)
        self.snapshotThread.finished.connect(self.snapshotThread.deleteLater)
        self.snapshotThread.finished.connect(self.updateSnapshotButton)
        self.snapshotThread.started.connect(self.snapshotWorker.snapshot)

        self.snapshotThread.start()

    def record(self):
        if self.recButton.isChecked():
            self.recording.emit(True)
            self.updateRecording(True)
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
            self.recording.emit(False)
            self.updateRecording(False)
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

    def updateBatt(self):
        camera = Virb((self.virb.ip, 80))
        batt = camera.get_batt_status()

        if batt < 5:
            self.virbBattLabel.setStyleSheet("QLabel {color: red; font: 24px}")
        elif batt >= 5 and batt < 20:
            self.virbBattLabel.setStyleSheet("QLabel {color: yellow; font: 24px}")
        else:
            self.virbBattLabel.setStyleSheet("QLabel {color: white; font: 24px}")

        self.virbBattLabel.setText(str(round(batt)) + " %")

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
        self.timer.stop()
        self.stop_preview.emit()
        self.close()


