"""
Window implemetation for dashcam
"""
import math
import subprocess
from datetime import datetime
from pathlib import Path

from PyQt5.QtWidgets import QWidget, QFrame, QLabel, QPushButton, QSizePolicy, QHBoxLayout, QVBoxLayout
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QThread, QTimer, QSize, pyqtSignal

from virb import Virb
from camcorder import Preview, StartRec, StopRec, Snapshot

STYLESHEET = """
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

def ping_ok(ip):
    """ Check if we can ping to ip """
    try:
        cmd = "ping -c 1 " + ip
        output = subprocess.check_output(cmd, shell=True)
    except Exception as e:
        return False

    return True

class CameraWindow(QWidget):
    """ window implementation for dashcam """
    stop_preview = pyqtSignal()
    recording = pyqtSignal(bool)
    info = pyqtSignal(dict)

    def createWindow(self, infobar, virb):
        """ create window for dashcam """
        parent = None
        super(CameraWindow, self).__init__(parent)

        self.virb = virb
        self.previewScale = 80
        self.rec = infobar.recording

        self.setStyleSheet(STYLESHEET)
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
        self.virbBattLabel.setStyleSheet("font: 18px")

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

        # battery status
        self.batt_status = QLabel()
        self.batt_100 = QPixmap(self.prefix + "batt_100.png").scaled(64, 64, Qt.KeepAspectRatio)
        self.batt_80 = QPixmap(self.prefix + "batt_80.png").scaled(64, 64, Qt.KeepAspectRatio)
        self.batt_60 = QPixmap(self.prefix + "batt_60.png").scaled(64, 64, Qt.KeepAspectRatio)
        self.batt_40 = QPixmap(self.prefix + "batt_40.png").scaled(64, 64, Qt.KeepAspectRatio)
        self.batt_20 = QPixmap(self.prefix + "batt_20.png").scaled(64, 64, Qt.KeepAspectRatio)

        self.updateTemperature(infobar.temperature)
        self.updateTime(datetime.now())
        self.updateTPMSWarn(infobar.tpmsWarn)
        self.updateGPSFix(infobar.gpsFix)
        self.updateSpeed(infobar.speed)
        self.updateRecording(infobar.recording)

        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.tpmsWarnLabel, alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.tempWarnLabel, alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.gpsInfoLabel, alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.recInfoLabel, alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.gpsSpeedLabel, alignment=Qt.AlignTop|Qt.AlignRight)
        hbox1.addWidget(self.tempInfoLabel, alignment=Qt.AlignTop|Qt.AlignRight)
        hbox1.addWidget(self.timeLabel, alignment=Qt.AlignTop|Qt.AlignRight)

        batt = QHBoxLayout()
        batt.setSpacing(0)
        batt.addWidget(self.batt_status, alignment=Qt.AlignRight)
        batt.addWidget(self.virbBattLabel, alignment=Qt.AlignLeft)

        vbox1 = QVBoxLayout()
        vbox1.addWidget(self.recButton, alignment=Qt.AlignCenter)
        vbox1.addWidget(self.snapshotButton, alignment=Qt.AlignCenter)
        vbox1.addLayout(batt)

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
            self.camera = Virb((self.virb.ip, 80))
            self.timer = QTimer()
            self.timer.timeout.connect(self.updateBatt)
            self.timer.start(30*1000)
            self.updateBatt()

        self.showFullScreen()

    def initPreviewThread(self):
        """ intialize preview thread """
        if not self.virb.ip:
            return
        self.previewLabel.setText("Checking connection...")
        if not ping_ok(self.virb.ip):
            self.previewLabel.setText("Connection failed")
            return

        self.previewThread = QThread()
        self.previewWorker = Preview(self.virb.ip)
        self.stop_preview.connect(self.previewWorker.stop_preview)
        self.previewWorker.moveToThread(self.previewThread)
        self.previewWorker.preview_finished.connect(self.previewThread.quit)
        self.previewWorker.preview_finished.connect(self.previewWorker.deleteLater)
        self.previewThread.finished.connect(self.previewThread.deleteLater)
        self.previewThread.finished.connect(self.updatePreviewText)
        self.previewThread.started.connect(self.previewWorker.live_preview)

        self.previewWorker.image.connect(self.updatePreview)

        self.previewThread.start()

    def initStartRecThread(self):
        """ initialize to start recording thread """
        if not self.virb.ip:
            return

        self.stop_preview.emit()

        self.startRecThread = QThread()
        self.startRecWorker = StartRec(self.virb.ip)
        self.startRecWorker.moveToThread(self.startRecThread)
        self.startRecWorker.finished.connect(self.startRecThread.quit)
        self.startRecWorker.finished.connect(self.startRecWorker.deleteLater)
        self.startRecThread.finished.connect(self.startRecThread.deleteLater)
        self.startRecThread.finished.connect(self.initPreviewThread)
        self.startRecThread.started.connect(self.startRecWorker.start_recording)

        self.startRecThread.start()

    def initStopRecThread(self):
        """ initialize to stop recording thread """
        if not self.recording or not self.virb.ip:
            return

        self.stop_preview.emit()

        self.stopRecThread = QThread()
        self.stopRecWorker = StopRec(self.virb.ip)
        self.stopRecWorker.moveToThread(self.stopRecThread)
        self.stopRecWorker.finished.connect(self.stopRecThread.quit)
        self.stopRecWorker.finished.connect(self.stopRecWorker.deleteLater)
        self.stopRecThread.finished.connect(self.stopRecThread.deleteLater)
        self.stopRecThread.finished.connect(self.initPreviewThread)
        self.stopRecThread.started.connect(self.stopRecWorker.stop_recording)

        self.stopRecThread.start()

    def initSnapshotThread(self):
        """ initialize snapshot thread """
        if not self.virb.ip:
            return

        self.stop_preview.emit()

        self.snapshotThread = QThread()
        self.snapshotWorker = Snapshot(self.virb.ip)
        self.snapshotWorker.moveToThread(self.snapshotThread)
        self.snapshotWorker.finished.connect(self.snapshotThread.quit)
        self.snapshotWorker.finished.connect(self.snapshotWorker.deleteLater)
        self.snapshotThread.finished.connect(self.snapshotThread.deleteLater)
        self.snapshotThread.finished.connect(self.updateSnapshotButton)
        self.snapshotThread.finished.connect(self.initPreviewThread)
        self.snapshotThread.started.connect(self.snapshotWorker.snapshot)

        self.snapshotThread.start()

    def record(self):
        """ start/stop recording """
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

        if self.previewThread.isRunning():
            print("preview running")
        else:
            print("preview not running")

    def snapshot(self):
        """ take a snapshot """
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
        self.initSnapshotThread()

    def updateSnapshotButton(self):
        """ update snapshot button status """
        self.snapshotButton.setEnabled(True)
        self.snapshotButton.setStyleSheet("background-color: darkgrey;"
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
        """ update preview """
        self.previewLabel.setPixmap(pixmap.scaled(int(704*self.previewScale/100), int(396*self.previewScale/100),
                                                  Qt.KeepAspectRatio))

    def updatePreviewText(self):
        self.previewLabel.setText("Stream unavailable")
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

    def setVirbIP(self, ip):
        """ set Garmin Virb ip """
        self.virb.ip = ip
        self.recButton.setEnabled(True)
        self.snapshotButton.setEnabled(True)

        if not self.previewThread.isRunning():
            self.initPreviewThread()

    def updateBatt(self):
        """ update Garmin Virb battery status """
        try:
            batt = self.camera.get_batt_status()
            self.virbBattLabel.setStyleSheet("QLabel {color: white; font: 18px}")

            if batt < 5:
                self.batt_status.setPixmap(self.batt_20)
                self.virbBattLabel.setStyleSheet("QLabel {color: red; font: 18px}")
            elif 5 <= batt <= 20:
                self.batt_status.setPixmap(self.batt_20)
                self.virbBattLabel.setStyleSheet("QLabel {color: yellow; font: 18px}")
            elif 20 < batt <= 40:
                self.batt_status.setPixmap(self.batt_40)
            elif 40 < batt <= 60:
                self.batt_status.setPixmap(self.batt_60)
            elif 60 < batt <= 80:
                self.batt_status.setPixmap(self.batt_80)
            else:
                self.batt_status.setPixmap(self.batt_100)

            self.virbBattLabel.setText(str(round(batt)) + " %")

        except:
            print("camerawindow: Garmin Virb battery info not available")

    def updateInfobar(self, data):
        """ update infobar """
        self.updateTime(data['time'])
        self.updateTemperature(data['temperature'])
        self.updateTPMSWarn(data['tpms'])
        self.updateGPSFix(data['gpsFix'])
        self.updateSpeed(data['speed'])
        self.updateRecording(data['recording'])

    def updateTime(self, t):
        """ update time """
        self.timeLabel.setText("{:02d}".format(t.hour) + ":" + "{:02d}".format(t.minute))

    def updateSpeed(self, speed):
        """ update speed """
        if math.isnan(speed):
            return
        self.gpsSpeedLabel.setText("{:d}".format(round(3.6*speed)) + " km/h")

    def updateTemperature(self, temperature):
        """ update temperature """
        if math.isnan(temperature):
            return

        if temperature < 3.0:
            self.tempWarnLabel.setPixmap(self.temp_warn_on)
        elif temperature > 3.2:
            self.tempWarnLabel.setPixmap(self.temp_warn_off)

        self.tempInfoLabel.setText("{0:d}".format(round(temperature)) + "\u2103")

    def updateTPMSWarn(self, warn):
        """ update TPMS status """
        if warn:
            self.tpmsWarnLabel.setPixmap(self.tpms_warn_on)
        else:
            self.tpmsWarnLabel.setPixmap(self.tpms_warn_off)

    def updateGPSFix(self, fix):
        """ update GPS fix """
        if fix:
            self.gpsInfoLabel.setPixmap(self.gps_connected)
        else:
            self.gpsInfoLabel.setPixmap(self.gps_disconnected)

    def updateRecording(self, recording):
        """ update recording status """
        if recording:
            self.recInfoLabel.setPixmap(self.rec_on)
        else:
            self.recInfoLabel.setPixmap(self.rec_off)

    def exit(self):
        """ exit window """
        self.timer.stop()
        self.stop_preview.emit()
        self.close()
