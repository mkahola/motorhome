#!/usr/bin/env python3

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import QtWidgets, QtCore, QtGui

from datetime import datetime
import threading
from threading import Thread
import cv2
import qdarkgraystyle
import socket
import psutil
import os
import sys
import time
import queue
import os.path
import configparser
from pathlib import Path

from tires import Tires
from virb import Virb

virb_addr = '192.168.100.15'

messages = ['Tire pressure low on front left tire',
            'Tire pressure low on front right tire',
            'Tire pressure low on rear left tire',
            'Tire pressure low on rear right tire',
            'Stairs down']

class getGPS(QObject):
    global vird_addr

    gpsSpeed = pyqtSignal(int)
    gpsLat = pyqtSignal(float)
    gpsLon = pyqtSignal(float)
    gpsAlt = pyqtSignal(int)
    gpsBatt = pyqtSignal(int)

    def run(self):
        global virb_addr

        self.camera = Virb((virb_addr, 80))

        while True:
            try:
                status = self.camera.status()
                self.gpsSpeed.emit(int(status['speed']*3.6))
                self.gpsLon.emit(status['gpsLongitude'])
                self.gpsLat.emit(status['gpsLatitude'])
                self.gpsAlt.emit(int(status['altitude']))
                self.gpsBatt.emit(int(status['batteryLevel'] + 0.5))
            except:
                print("unable to read status")
                pass

            time.sleep(1)

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: black;")
        self.setWindowTitle("Motorhome Info")
        self.warns = self.Warnings()
        self.warning = "No messages"
        self.resolution = QDesktopWidget().availableGeometry(-1)
        self.setup_ui()

        self.setup_warns()
        self.getTPMSwarn()
#        self.showFullScreen()
        self.showMaximized()

    def setup_ui(self):
        global messages
        global virb_addr

        # TPMS
        self.tire = Tires()
        self.tpmsFLflag = False
        self.tpmsFRflag = False
        self.tpmsRLflag = False
        self.tpmsRRflag = False

        # Garmin Virb
        self.virb = Virb((virb_addr, 80))
        self.speed = -1

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

        centralLayout = QVBoxLayout()
        centralLayout.addWidget(self.TabWidget, 1)
        centralLayout.addWidget(self.tpmsWarnLabel)

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
        page.setGeometry(0, 0, self.resolution.width(), self.resolution.height())
        self.recButton = QPushButton("Rec", self)
        self.recButton.setFixedSize(200,200)
        self.recButton.setCheckable(True)
        self.recButton.clicked.connect(self.startStopRecording)
        self.recButton.setStyleSheet("color: black;"
                                     "background-color: lightgrey;"
                                     "font: bold 28px;")

        vbox = QVBoxLayout()
        vbox.setAlignment(Qt.AlignCenter)
        vbox.addWidget(self.recButton)
        page.setLayout(vbox)

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

        # start server
        self.thread =  QThread()
        self.worker = getGPS()
        self.worker.moveToThread(self.thread)
        self.worker.gpsSpeed.connect(self.updateSpeed)
        self.worker.gpsLat.connect(self.updateLat)
        self.worker.gpsLon.connect(self.updateLon)
        self.worker.gpsAlt.connect(self.updateAlt)
        self.worker.gpsBatt.connect(self.updateBatt)
        self.thread.started.connect(self.worker.run)
        self.thread.start()

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

    def updateSpeed(self, speed):
            self.speed_label.setText(str(speed))
            self.speed = speed

    def updateLat(self, lat):
        self.lat_label.setText("{:.4f}".format(lat))

    def updateLon(self, lon):
        self.lon_label.setText("{:.4f}".format(lon))

    def updateAlt(self, alt):
        self.alt_label.setText(str(alt))

    def updateBatt(self, batt):
       self.battery = batt

    def startStopRecording(self):
        if self.recButton.isChecked():
            print("start recording")
            self.recButton.setStyleSheet("color: white;"
                                         "background-color: red;"
                                         "font: bold 28px;")
            self.virb.set_features('autoRecord', 'off')
            self.virb.start_recording()
        else:
            print("stop recording")
            self.recButton.setStyleSheet("color: black;"
                                         "background-color: lightgrey;"
                                         "font: bold 28px;")
            self.virb.stop_recording()
            self.virb.set_features('autoRecord', 'whenMoving')

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
        size = 32
        if self.tpmsFLflag or self.tpmsFRflag or self.tpmsRLflag or self.tpmsRRflag:
            self.tpmsWarnLabel.setPixmap(self.tpms_warn_on)
            self.tpmsWarnLabel.setAlignment(Qt.AlignVCenter)
            self.TabWidget.setTabIcon(self.tp_index, QIcon(prefix + 'tpms_warn_on.png'))
            self.TabWidget.setIconSize(QtCore.QSize(size, size))
        else:
            self.tpmsWarnLabel.setPixmap(self.tpms_warn_off)
            self.tpmsWarnLabel.setAlignment(Qt.AlignVCenter)
            self.TabWidget.setTabIcon(self.tp_index, QIcon(prefix + 'tpms_warn_off.png'))
            self.TabWidget.setIconSize(QtCore.QSize(size, size))

    def sensor_handler(self, client):
        while True:
            sensor = client.recv(32).decode('utf-8')
            if sensor:
                sensor = sensor.split(',')
                if sensor[0] == 'FL' or sensor[0] == 'FR' or sensor[0] == 'RL' or sensor[0] == 'RR':
                    self.setTPMS(sensor)
        client.close()

    def get_warns(self):
        # create a local socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            # bind the socket to the port
            sock.bind(('localhost', 5000))
            # listen for incoming connections
            sock.listen(5)
            print("Server started...")

            while True:
                client, addr = sock.accept()
                threading.Thread(target=self.sensor_handler, args=(client,)).start()

    def setup_warns(self):
        # warnings server
        self.warns.worker = Thread(target=self.get_warns, args=())
        self.warns.worker.setDaemon(True)
        self.warns.worker.start()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            #ugly but efficient
            system = psutil.Process(os.getpid())
            system.terminate()

    class Warnings:
        def __init__(self, warns=0):
            self.warns = warns
            self.worker = 0

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkgraystyle.load_stylesheet())
    win = MainApp()
    sys.exit(app.exec_())
