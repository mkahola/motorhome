#!/usr/bin/env python3

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import QtWidgets, QtCore, QtGui

from datetime import datetime
import cv2
import qdarkgraystyle
import psutil
import sys
import os.path
import subprocess
import configparser
from pathlib import Path

from tires import Tires
from virb import Virb
from camcorder import Camcorder
from gps import GPS
from warns import Warnings

messages = ['Tire pressure low on front left tire',
            'Tire pressure low on front right tire',
            'Tire pressure low on rear left tire',
            'Tire pressure low on rear right tire',
            'Stairs down']

class MainApp(QMainWindow):
    stop_signal = pyqtSignal()
    start_signal = pyqtSignal()
    exit_signal = pyqtSignal()
    stop_preview = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: black;")
        self.setWindowTitle("Motorhome Info")
        self.warning = "No messages"
        self.resolution = QDesktopWidget().availableGeometry(-1)

        ssid = subprocess.check_output(['sudo', 'iwgetid']).decode("utf-8").split('"')[1]
        if ssid == "VIRB-6267":
            self.ip = "192.168.0.1"
        else:
            self.ip = "192.168.100.15"

        self.setup_ui()

        # GPS data receiving thread
        self.initGPSThread()

        self.initWarnsThread()
        self.getTPMSwarn()
#        self.showFullScreen()
        self.showMaximized()

    def setup_ui(self):
        global messages

        self.tire = Tires()
        self.tpmsFLflag = False
        self.tpmsFRflag = False
        self.tpmsRLflag = False
        self.tpmsRRflag = False
        self.speed = -1
        self.camera_connected = False

        #Initialize widgets
        self.centralWidget = QWidget()

        self.TabWidget = QTabWidget(self)
        self.TabWidget.setFont(QFont("Sanserif", 16))

        self.pages = [QWidget(), QWidget(), QWidget(), QWidget(), QWidget(), QWidget()]

        #initialize pages
        self.init_gps_ui(self.pages[0])
        self.init_dashcam_ui(self.pages[1])
        self.init_tpms_ui(self.pages[2])
        self.init_msg_ui(self.pages[3])
        self.init_settings_ui(self.pages[4])

        # warn lights
        prefix = str(Path.home()) + "/.motorhome/res/"
        self.tpms_warn_off = QPixmap(prefix + "tpms_warn_off.png").scaled(32, 32, Qt.KeepAspectRatio)
        self.tpms_warn_on = QPixmap(prefix + "tpms_warn_on.png").scaled(32, 32, Qt.KeepAspectRatio)
        self.tpmsWarnLabel = QLabel()
        self.tpmsWarnLabel.setPixmap(self.tpms_warn_off)
        self.tpmsWarnLabel.setAlignment(Qt.AlignVCenter)

        self.virbBattLabel = QLabel()
        self.virbBattLabel.setText(" -- %")
        self.virbBattLabel.setStyleSheet("QLabel {color: white; font: bold 16px}")
        self.virbBattLabel.setAlignment(Qt.AlignRight)

        powerButton = QPushButton("", self)
        powerButton.setIcon(QIcon(prefix + 'power.png'))
        powerButton.setIconSize(QSize(32, 32))
        powerButton.clicked.connect(self.poweroff)
        powerButton.setStyleSheet("background-color: black;"
                                  "border-style: outset;"
                                  "border-width: 2px;"
                                  "border-radius: 6px;"
                                  "border-color: black;"
                                  "font: bold 32px;"
                                  "color: black;"
                                  "min-width: 32px;"
                                  "max-width: 32px;"
                                  "min-height: 28px;"
                                  "max-height: 28px;"
                                  "padding: 1px;")

        warnLayout = QHBoxLayout()
        warnLayout.addWidget(self.tpmsWarnLabel)
        warnLayout.addWidget(self.virbBattLabel)
        warnLayout.addWidget(powerButton)

        centralLayout = QVBoxLayout()
        centralLayout.addWidget(self.TabWidget, 1)
        centralLayout.addLayout(warnLayout)

        size = 32
        self.gps_index = self.TabWidget.addTab(self.pages[0], "")
        self.TabWidget.setTabIcon(self.gps_index, QIcon(prefix + 'gps.png'))
        self.TabWidget.setIconSize(QtCore.QSize(size, size))

        self.dc_index = self.TabWidget.addTab(self.pages[1], "")
        self.TabWidget.setTabIcon(self.dc_index, QIcon(prefix + 'camera.png'))
        self.TabWidget.setIconSize(QtCore.QSize(size, size))

        self.tp_index = self.TabWidget.addTab(self.pages[2], "")
        self.TabWidget.setTabIcon(self.tp_index, QIcon(prefix + 'tpms_warn_off.png'))
        self.TabWidget.setIconSize(QtCore.QSize(size, size))

        self.warn_index = self.TabWidget.addTab(self.pages[3], "")
        self.TabWidget.setTabIcon(self.warn_index, QIcon(prefix + 'messages.png'))
        self.TabWidget.setIconSize(QtCore.QSize(size, size))

        self.settings_index = self.TabWidget.addTab(self.pages[4], "")
        self.TabWidget.setTabIcon(self.settings_index, QIcon(prefix + 'settings.png'))
        self.TabWidget.setIconSize(QtCore.QSize(size, size))
        self.TabWidget.setStyleSheet('''
            QTabBar::tab { height: 32px; width: 64px; color: #000000;}
            QTabBar::tab:selected {background-color: #373636;}
            QTabBar::tab:selected {font: 16pt bold; color: #000000}
            QTabBar::tab {margin: 0px;}
            ''')

        self.centralWidget.setLayout(centralLayout)
        self.setCentralWidget(self.centralWidget)

    def init_dashcam_ui(self, page):
        prefix = str(Path.home()) + "/.motorhome/res/"

        page.setGeometry(0, 0, self.resolution.width(), self.resolution.height())

        recButton = QPushButton("", self)
        recButton.setIcon(QIcon(prefix + 'rec.png'))
        recButton.setIconSize(QSize(64, 64))
        recButton.setCheckable(True)
        recButton.clicked.connect(lambda: self.record(recButton))
        recButton.setStyleSheet("background-color: darkgrey;"
                                "border-style: outset;"
                                "border-width: 2px;"
                                "border-radius: 10px;"
                                "border-color: beige;"
                                "font: bold 32px;"
                                "color: red;"
                                "min-width: 72px;"
                                "min-height: 72px;"
                                "padding: 12px;")

        snapshotButton = QPushButton("", self)
        snapshotButton.setIcon(QIcon(prefix + 'snapshot.png'))
        snapshotButton.setIconSize(QSize(64, 64))
        snapshotButton.clicked.connect(lambda: self.snapshot(snapshotButton))
        snapshotButton.setStyleSheet("background-color: darkgrey;"
                                     "border-style: outset;"
                                     "border-width: 2px;"
                                     "border-radius: 10px;"
                                     "border-color: beige;"
                                     "font: bold 32px;"
                                     "color: black;"
                                     "min-width: 72px;"
                                     "min-height: 72px;"
                                     "padding: 12px;")

        pixmap = QPixmap(int(704/2), int(396/2))
        pixmap.fill(QColor("black"))
        icon = QIcon(pixmap)

        self.previewButton = QPushButton("Preview", self)
        self.previewButton.setCheckable(True)
        self.previewButton.resize(int(704/2), int(396/2))
        self.previewButton.clicked.connect(self.setup_camera)

        self.previewButton.setIcon(icon)
        self.previewButton.setIconSize(pixmap.rect().size())
        self.previewButton.setText("Preview")
        self.previewButton.setStyleSheet("background-color: darkgrey;"
                                         "border-style: outset;"
                                         "border-width: 2px;"
                                         "border-radius: 10px;"
                                         "border-color: beige;"
                                         "font: bold 32px;"
                                         "color: black;"
                                         "min-width: 352px;"
                                         "min-width: 198px;"
                                         "padding: 12px;")

        vbox = QVBoxLayout()
        vbox.setAlignment(Qt.AlignCenter)
        vbox.addWidget(recButton)
        vbox.addWidget(snapshotButton)

        hbox = QHBoxLayout()
        hbox.setSpacing(40)
        hbox.addLayout(vbox)
        hbox.setAlignment(Qt.AlignCenter)
        hbox.addWidget(self.previewButton)

        page.setLayout(hbox)

    def init_gps_ui(self, page):
        page.setGeometry(0, 0, self.resolution.width(), self.resolution.height())

        self.lat_title_label = QLabel("Latitude")
        self.lat_title_label.setFont(QFont("Sanserif", 12))
        self.lat_title_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)

        self.lon_title_label = QLabel("Longitude")
        self.lon_title_label.setFont(QFont("Sanserif", 12))
        self.lon_title_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)

        self.alt_title_label = QLabel("Altitude (m)")
        self.alt_title_label.setFont(QFont("Sanserif", 12))
        self.alt_title_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)

        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.lat_title_label)
        hbox1.addWidget(self.lon_title_label)
        hbox1.addWidget(self.alt_title_label)

        self.lat_label = QLabel("--")
        self.lat_label.setFont(QFont("Sanserif", 32))
        self.lat_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)

        self.lon_label = QLabel("--")
        self.lon_label.setFont(QFont("Sanserif", 32))
        self.lon_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)

        self.alt_label = QLabel("--")
        self.alt_label.setFont(QFont("Sanserif", 32))
        self.alt_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.lat_label)
        hbox2.addWidget(self.lon_label)
        hbox2.addWidget(self.alt_label)

        self.speed_title_label = QLabel("km/h")
        self.speed_title_label.setFont(QFont("Sanserif", 12))
        self.speed_title_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)

        hbox3 = QHBoxLayout()
        hbox3.addWidget(self.speed_title_label)

        self.speed_label = QLabel("--")
        self.speed_label.setFont(QFont("Sanserif", 128))
        self.speed_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)

        hbox4 = QHBoxLayout()
        hbox4.addWidget(self.speed_label)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        vbox.addLayout(hbox3)
        vbox.addLayout(hbox4)
        page.setLayout(vbox)

    def init_tpms_ui(self, page):
        page.setGeometry(0, 0, self.resolution.width(), self.resolution.height())
        pressure = "-- bar"
        temperature = "-- C"
        self.fl_label = QLabel(pressure + "\n" + temperature)
        self.fr_label = QLabel(pressure + "\n" + temperature)
        self.rl_label = QLabel(pressure + "\n" + temperature)
        self.rr_label = QLabel(pressure + "\n" + temperature)

        font = self.fl_label.font()
        font.setPointSize(32)
        font.setBold(True)
        self.fl_label.setFont(font)
        self.fr_label.setFont(font)
        self.rl_label.setFont(font)
        self.rr_label.setFont(font)

        self.fl_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.fr_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.rl_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.rr_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)

        prefix = str(Path.home()) + "/.motorhome/res/"
        pixmap = QPixmap(prefix + "tire.png").scaled(128, 128, Qt.KeepAspectRatio)

        tire1_label = QLabel()
        tire1_label.setPixmap(pixmap)
        tire1_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        tire2_label = QLabel()
        tire2_label.setPixmap(pixmap)
        tire2_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        tire3_label = QLabel()
        tire3_label.setPixmap(pixmap)
        tire3_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        tire4_label = QLabel()
        tire4_label.setPixmap(pixmap)
        tire4_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        vbox = QGridLayout()
        vbox.addWidget(self.fl_label, 0, 0)
        vbox.addWidget(tire1_label, 0, 1)
        vbox.addWidget(tire2_label, 0, 2)
        vbox.addWidget(self.fr_label, 0, 3)
        vbox.addWidget(self.rl_label, 1, 0)
        vbox.addWidget(tire3_label, 1, 1)
        vbox.addWidget(tire4_label, 1, 2)
        vbox.addWidget(self.rr_label, 1, 3)
        page.setLayout(vbox)

    def init_msg_ui(self, page):
        # messages
        page.setGeometry(0, 0, self.resolution.width(), self.resolution.height())
        self.msg_list = QListWidget()
        self.msg_list.setFont(QFont("Sanserif", 16))
        self.msg_model = QStandardItemModel(self.msg_list)
        vbox = QVBoxLayout()
        vbox.addWidget(self.msg_list)
        page.setLayout(vbox)

        font = self.fl_label.font()
        font.setPointSize(16)
        font.setBold(True)

    def init_settings_ui(self, page):
        # Tire pressure warnig level
        page.setGeometry(0, 0, self.resolution.width(), self.resolution.height())
        self.low_pressure = QSlider(Qt.Horizontal, self)
        self.low_pressure.setFocusPolicy(Qt.NoFocus)
        self.low_pressure.setRange(10, 50)
        self.low_pressure.setPageStep(1)
        self.low_pressure.valueChanged.connect(self.changePressureLevel)
        self.low_pressure.sliderReleased.connect(self.updateConfig)
        self.ptitle_label = QLabel("TPMS warn level", self)
        self.ptitle_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.ptitle_label.setFont(QFont("Sanserif", 32))
        self.pslider_label = QLabel(" 1 bar", self)
        self.pslider_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.pslider_label.setMinimumWidth(60)
        self.pslider_label.setFont(QFont("Sanserif", 32))
        self.low_pressure.setStyleSheet('''
            QSlider::handle:horizontal { width: 32px; }
            QSlider::groove:horizontal { height: 8px; }
            QSlider::handle:vertical { height: 32px; }
            ''')

        vbox = QHBoxLayout()
        vbox.addWidget(self.ptitle_label)
        vbox.addSpacing(10)
        vbox.addWidget(self.low_pressure)
        vbox.addSpacing(10)
        vbox.addWidget(self.pslider_label)
        page.setLayout(vbox)

    def initStartRecThread(self):
        self.startRecThread = QThread()
        self.startRecWorker = Camcorder(self.ip)
        self.startRecWorker.moveToThread(self.startRecThread)
        self.startRecWorker.finished.connect(self.startRecThread.quit)
        self.startRecWorker.finished.connect(self.startRecWorker.deleteLater)
        self.startRecThread.finished.connect(self.startRecThread.deleteLater)
        self.startRecThread.started.connect(self.startRecWorker.start_recording)

        self.startRecThread.start()

    def initStopRecThread(self):
        self.stopRecThread = QThread()
        self.stopRecWorker = Camcorder(self.ip)
        self.stopRecWorker.moveToThread(self.stopRecThread)
        self.stopRecWorker.finished.connect(self.stopRecThread.quit)
        self.stopRecWorker.finished.connect(self.stopRecWorker.deleteLater)
        self.stopRecThread.finished.connect(self.stopRecThread.deleteLater)
        self.stopRecThread.started.connect(self.stopRecWorker.stop_recording)

        self.stopRecThread.start()

    def initSnapshotThread(self, button):
        self.snapshotThread = QThread()
        self.snapshotWorker = Camcorder(self.ip)
        self.snapshotWorker.moveToThread(self.snapshotThread)
        self.snapshotWorker.finished.connect(self.snapshotThread.quit)
        self.snapshotWorker.finished.connect(self.snapshotWorker.deleteLater)
        self.snapshotThread.finished.connect(self.snapshotThread.deleteLater)
        self.snapshotThread.finished.connect(lambda: self.updateSnapshotButton(button))
        self.snapshotThread.started.connect(self.snapshotWorker.snapshot)

        self.snapshotThread.start()

    def initPreviewThread(self):
        self.previewThread = QThread()
        self.previewWorker = Camcorder(self.ip)
        self.stop_preview.connect(self.previewWorker.stop_preview)
        self.previewWorker.moveToThread(self.previewThread)
        self.previewWorker.finished.connect(self.previewThread.quit)
        self.previewWorker.finished.connect(self.previewWorker.deleteLater)
        self.previewThread.finished.connect(self.previewThread.deleteLater)
        self.previewThread.started.connect(self.previewWorker.live_preview)
        #self.previewWorker.stop_preview.connect(self.previewWorker.stop_preview)

        self.previewWorker.image.connect(self.updatePreview)

        self.previewThread.start()

    def initWarnsThread(self):
        self.warnsThread = QThread()
        self.warnsWorker = Warnings()
        self.exit_signal.connect(self.warnsWorker.stop)
        self.warnsWorker.moveToThread(self.warnsThread)
        self.warnsWorker.finished.connect(self.warnsThread.quit)
        self.warnsWorker.finished.connect(self.warnsWorker.deleteLater)
        self.warnsThread.finished.connect(self.warnsThread.deleteLater)
        self.warnsThread.started.connect(self.warnsWorker.get_warns)

        self.warnsWorker.data.connect(self.setTPMS)

        self.warnsThread.start()

    def initGPSThread(self):
        self.thread =  QThread()
        self.worker = GPS(self.ip)
        self.stop_signal.connect(self.worker.halt)
        self.start_signal.connect(self.worker.get_status)
        self.exit_signal.connect(self.worker.stop)
        self.worker.moveToThread(self.thread)

        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.started.connect(self.worker.run)

        self.worker.start_signal.connect(self.worker.get_status)
        self.worker.stop_signal.connect(self.worker.halt)
        self.worker.exit_signal.connect(self.worker.stop)

        self.worker.gpsSpeed.connect(self.updateSpeed)
        self.worker.gpsLat.connect(self.updateLat)
        self.worker.gpsLon.connect(self.updateLon)
        self.worker.gpsAlt.connect(self.updateAlt)
        self.worker.gpsBatt.connect(self.updateBatt)
        self.thread.started.connect(self.worker.run)

        self.thread.start()

    def record(self, button):
        prefix = str(Path.home()) + "/.motorhome/res/"

        if button.isChecked():
            button.setIcon(QIcon(prefix + 'stop.png'))
            button.setIconSize(QSize(64, 64))
            button.setStyleSheet("background-color: #373636;"
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
            button.setIcon(QIcon(prefix + 'rec.png'))
            button.setIconSize(QSize(64, 64))
            button.setStyleSheet("background-color: darkgrey;"
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

    def snapshot(self, button):
        button.setStyleSheet("background-color: #373636;"
                             "border-style: outset;"
                             "border-width: 2px;"
                             "border-radius: 10px;"
                             "border-color: beige;"
                             "font: bold 32px;"
                             "color: red;"
                             "min-width: 72px;"
                             "min-height: 72px;"
                             "padding: 12px;")
        button.setEnabled(False)
        self.initSnapshotThread(button)

    def updateSnapshotButton(self, button):
        button.setEnabled(True)
        button.setStyleSheet("background-color: darkgrey;"
                             "border-style: outset;"
                             "border-width: 2px;"
                             "border-radius: 10px;"
                             "border-color: beige;"
                             "font: bold 32px;"
                             "color: black;"
                             "min-width: 72px;"
                             "min-height: 72px;"
                             "padding: 12px;")

    def tabChanged(self, index):
        if index != self.dc_index:
            if self.previewButton.isChecked():
                self.previewButton.setChecked(False)
                self.setup_camera()

    def updateSpeed(self, speed):
            self.speed_label.setText(str(speed))
            self.speed = speed

    def updateLat(self, lat):
        self.lat_label.setText("{:.5f}".format(lat))

    def updateLon(self, lon):
        self.lon_label.setText("{:.5f}".format(lon))

    def updateAlt(self, alt):
        self.alt_label.setText(str(alt))

    def updateBatt(self, batt):
       if batt < 5:
           self.virbBattLabel.setStyleSheet("QLabel {color: red; font: bold 24px}")
       elif batt >= 5 and batt < 20:
           self.virbBattLabel.setStyleSheet("QLabel {color: yellow; font: bold 24px}")
       else:
           self.virbBattLabel.setStyleSheet("QLabel {color: white; font: bold 24px}")

       self.virbBattLabel.setText(str(batt) + "%")

    def updatePreview(self, icon):
        self.previewButton.setIcon(icon)
        self.previewButton.setIconSize(QSize(int(704/2), int(396/2)))

    def setup_camera(self):
        if not self.previewButton.isEnabled():
            return

        if self.previewButton.isChecked():
            print("button checked")
            self.stop_signal.emit()

            self.initPreviewThread()

            self.previewButton.setText("Stop")
            self.previewButton.setStyleSheet("background-color: darkgrey;"
                                             "border-style: inset;"
                                             "border-width: 2px;"
                                             "border-radius: 10px;"
                                             "border-color: beige;"
                                             "font: bold 32px;"
                                             "color: red;"
                                             "min-width: 10em;"
                                             "padding: 6px;")
        else:
            print("button not checked")
            self.start_signal.emit()

            self.stop_preview.emit()

            pixmap = QPixmap(int(704/2), int(396/2))
            pixmap.fill(QColor("black"))
            icon = QIcon(pixmap)
            self.previewButton.setIcon(icon)
            self.previewButton.setIconSize(pixmap.rect().size())
            self.previewButton.setText("Preview")
            self.previewButton.setStyleSheet("background-color: darkgrey;"
                                             "border-style: outset;"
                                             "border-width: 2px;"
                                             "border-radius: 10px;"
                                             "border-color: beige;"
                                             "font: bold 32px;"
                                             "color: black;"
                                             "min-width: 10em;"
                                             "padding: 6px;")

    def changePressureLevel(self, value):
        self.tire.setWarnPressure(value/10.0)
        self.pslider_label.setText(str(self.tire.warnPressure) + " bar")

    def getTPMSwarn(self):
        conf_file = str(Path.home()) + "/.motorhome/tpms.conf"
        config = configparser.ConfigParser()

        try:
            config.read(conf_file)

            val = float(config['DEFAULT']['warn'])
            val = int(val * 10)

            self.low_pressure.setValue(val)
            self.tire.warnPressure = val/10.0
        except:
            return 48

        return val

    def updateConfig(self):
        conf_file = str(Path.home()) + "/.motorhome/tpms.conf"
        config = configparser.ConfigParser()
        config.read(conf_file)

        Default = config['DEFAULT']
        Default['warn'] = str(self.low_pressure.value()/10)

        with open(conf_file, 'w') as configfile:
            config.write(configfile)

    def appendMessage(self, flag, msg):
        if flag == False:
            item = QListWidgetItem(msg)
            item.setTextAlignment(Qt.AlignCenter)
            self.msg_list.addItem(item)
            return True

        return flag

    def removeMessage(self, flag, msg):
        if flag:
            try:
                item = self.msg_list.findItems(msg, Qt.MatchExactly)
                row = self.msg_list.row(item[0])
                self.msg_list.takeItem(row)
                return False
            except IndexError:
                pass
        return flag

    def setTPMS(self, sensor):
        sensor = sensor.split(',')
        self.tire.setPressure(sensor[0], sensor[1])
        self.tire.setTemperature(sensor[0], sensor[2])

        if sensor[0] == 'FL':
            if sensor[3] == '1':
                self.fl_label.setStyleSheet("color:yellow")
                self.tpmsFLflag = self.appendMessage(self.tpmsFLflag,
                                                     messages[0])
            else:
                self.fl_label.setStyleSheet("color:green")
                self.tpmsFLflag = self.removeMessage(self.tpmsFLflag,
                                                     messages[0])
            self.fl_label.setText(str(self.tire.FrontLeftPressure)  + " bar\n" + str(self.tire.FrontLeftTemp) + " C")
        elif sensor[0] == 'FR':
            if sensor[3] == '1':
                self.fr_label.setStyleSheet("color:yellow")
                self.tpmsFRflag = self.appendMessage(self.tpmsFRflag,
                                                     messages[1])
            else:
                self.fr_label.setStyleSheet("color:green")
                self.tpmsFRflag = self.removeMessage(self.tpmsFRflag,
                                                     messages[1])
            self.fr_label.setText(str(self.tire.FrontRightPressure)  + " bar\n" + str(self.tire.FrontRightTemp) + " C")
        elif sensor[0] == 'RL':
            if sensor[3] == '1':
                self.rl_label.setStyleSheet("color:yellow")
                self.tpmsRLflag = self.appendMessage(self.tpmsRLflag,
                                                     messages[2])
            else:
                self.rl_label.setStyleSheet("color:green")
                self.tpmsRLflag = self.removeMessage(self.tpmsRLflag,
                                                     messages[2])
            self.rl_label.setText(str(self.tire.RearLeftPressure)  + " bar\n" + str(self.tire.RearLeftTemp) + " C")
        elif sensor[0] == 'RR':
            if sensor[3] == '1':
                self.rr_label.setStyleSheet("color:yellow")
                self.tpmsRRflag = self.appendMessage(self.tpmsRRflag,
                                                     messages[3])
            else:
                self.rr_label.setStyleSheet("color:green")
                self.tpmsRRflag = self.removeMessage(self.tpmsRRflag,
                                                     messages[3])
            self.rr_label.setText(str(self.tire.RearRightPressure)  + " bar\n" + str(self.tire.RearRightTemp) + " C")

        if self.msg_list.count() > 0:
            self.msg_title = str(self.msg_list.count())
            self.warn_index = self.TabWidget.setTabText(3, self.msg_title)
        else:
            self.msg_title = ""
            self.warn_index = self.TabWidget.setTabText(3, self.msg_title)

        # turn on/off TPMS warn light
        prefix = str(Path.home()) + "/.motorhome/res/"
        if self.tpmsFLflag or self.tpmsFRflag or self.tpmsRLflag or self.tpmsRRflag:
            self.tpmsWarnLabel.setPixmap(self.tpms_warn_on)
            self.tpmsWarnLabel.setAlignment(Qt.AlignVCenter)
            self.TabWidget.setTabIcon(self.tp_index, QIcon(prefix + 'tpms_warn_on.png'))
        else:
            self.tpmsWarnLabel.setPixmap(self.tpms_warn_off)
            self.tpmsWarnLabel.setAlignment(Qt.AlignVCenter)
            self.TabWidget.setTabIcon(self.tp_index, QIcon(prefix + 'tpms_warn_off.png'))

    def poweroff(self):
        os.system("sudo shutdown -h now")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.exit_signal.emit()
            #ugly but efficient
            system = psutil.Process(os.getpid())
            system.terminate()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkgraystyle.load_stylesheet())
    win = MainApp()
    sys.exit(app.exec_())
