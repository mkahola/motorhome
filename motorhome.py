#!/usr/bin/env python3
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWebKit import *
from PyQt5.QtWebKitWidgets import *
from PyQt5 import QtWidgets, QtCore, QtGui

from datetime import datetime, timedelta
import time
import qdarkgraystyle
import psutil
import sys
import os.path
import subprocess
import configparser
from pathlib import Path
import python_arptable
from python_arptable import get_arp_table

from tires import Tires
from tpms import TPMS
from virb import Virb
from camcorder import Camcorder
from gps import GPS
from warns import Warnings
from geolocation import Geolocation
from ruuvi import RuuviTag

class MainApp(QMainWindow):
    stop_signal = pyqtSignal()
    start_signal = pyqtSignal()
    exit_signal = pyqtSignal()
    stop_preview = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: black;")
        self.setWindowTitle("Motorhome Info")
        self.resolution = QDesktopWidget().availableGeometry(-1)
        self.prefix = str(Path.home()) + "/.motorhome/res/"
        self.network_available = False
        self.updateAddress = False
        self.ip = ""
        self.gps_ts = datetime.now() - timedelta(seconds=10)
        self.gps_connection = False

        self.setup_ui()

        conf_file = str(Path.home()) + "/.motorhome/tpms.conf"
        config = configparser.ConfigParser()

        try:
            config.read(conf_file)
            self.virb_mac = config['VIRB']['mac']
        except:
            self.virb_mac = ""

        self.ssid = subprocess.check_output(['sudo', 'iwgetid']).decode("utf-8").split('"')[1]
        if self.ssid != "VIRB-6267":
            self.network_available = True

        self.timer=QTimer()
        self.timer.timeout.connect(self.get_ip)
        self.timer.start(1000)

        self.datetimer=QTimer()
        self.datetimer.timeout.connect(self.updateDateTime)
        self.datetimer.start(1000)

        self.initTPMSThread()
        self.getTPMSwarn()
        self.showFullScreen()
#        self.showMaximized()

    def get_ip(self):
        ip_ok = False

        conf_file = str(Path.home()) + "/.motorhome/network.conf"
        config = configparser.ConfigParser()
        config.read(conf_file)

        try:
            ip = config[self.ssid]['ip']
            response = os.system("ping -c 1 " + ip)

            #and then check the response...
            if response == 0:
                ip_ok = True
                self.ip = ip
                print("virb responded to ping")
            else:
                print("no response from virb!")

            self.initGPSThread()
            self.timer.stop()
        except:
            pass

        if not ip_ok:
            arp = get_arp_table()
            for i in range(len(arp)):
                if arp[i]['HW address'] == self.virb_mac:
                    self.ip = arp[i]['IP address']
                    # GPS data receiving thread
                    self.initGPSThread()
                    self.timer.stop()

                    try:
                        ssid = config[self.ssid]
                        ssid['ip'] = self.ip
                    except:
                        config.add_section(self.ssid)
                        config[self.ssid]['ip'] = self.ip

                    with open(conf_file, 'w') as configfile:
                        config.write(configfile)

        print("Virb ip: " + self.ip)

    def setup_ui(self):
        self.tire = Tires()
        self.tpmsFLflag = False
        self.tpmsFRflag = False
        self.tpmsRLflag = False
        self.tpmsRRflag = False
        self.speed = -1
        self.previewEnabled = False
        self.previewScale = 80

        #Initialize widgets
        self.centralWidget = QWidget()

        self.TabWidget = QTabWidget(self)
        self.TabWidget.setFont(QFont("Sanserif", 16))

        self.pages = [QWidget(), QWidget(), QWidget(), QWidget(), QWidget(), QWidget(), QWidget(), QWidget(), QWidget(), QWidget()]

        #initialize pages
        self.init_dashboard_ui(self.pages[0])
        self.init_gps_ui(self.pages[1])
        self.init_dashcam_ui(self.pages[2])
        self.init_tpms_ui(self.pages[3])
        self.init_ruuvitag(self.pages[4])
        self.init_settings_ui(self.pages[5])
        self.init_info_ui(self.pages[6])

        # warn lights
        self.temp_warn_off = QPixmap("")
        self.temp_warn_on = QPixmap(self.prefix + "snowflake.png").scaled(32, 32, Qt.KeepAspectRatio)
        self.tempWarnLabel = QLabel()
        self.tempWarnLabel.setPixmap(self.temp_warn_off)
        self.tempWarnLabel.setAlignment(Qt.AlignVCenter)

        self.tpms_warn_off = QPixmap(self.prefix + "tpms_warn_off.png").scaled(32, 32, Qt.KeepAspectRatio)
        self.tpms_warn_on = QPixmap(self.prefix + "tpms_warn_on.png").scaled(32, 32, Qt.KeepAspectRatio)
        self.tpmsWarnLabel = QLabel()
        self.tpmsWarnLabel.setPixmap(self.tpms_warn_off)
        self.tpmsWarnLabel.setAlignment(Qt.AlignVCenter)

        self.gps_disconnected = QPixmap(self.prefix + "no_gps.png").scaled(32, 32, Qt.KeepAspectRatio)
        self.gps_connected = QPixmap(self.prefix + "")
        self.gpsWarnLabel = QLabel()
        self.gpsWarnLabel.setPixmap(self.gps_disconnected)
        self.gpsWarnLabel.setAlignment(Qt.AlignVCenter)

        self.dateLabel = QLabel()
        self.dateLabel.setStyleSheet("QLabel {color: white; font: bold 14px}")
        self.dateLabel.setAlignment(Qt.AlignCenter)

        self.timeLabel = QLabel()
        self.timeLabel.setStyleSheet("QLabel {color: white; font: bold 24px}")
        self.timeLabel.setAlignment(Qt.AlignCenter)

        self.tempLabel = QLabel()
        self.tempLabel.setStyleSheet("QLabel {color: white; font: bold 24px}")
        self.tempLabel.setAlignment(Qt.AlignCenter)

        powerButton = QPushButton("", self)
        powerButton.setIcon(QIcon(self.prefix + 'power.png'))
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
        warnLayout.addWidget(self.tempWarnLabel)
        warnLayout.addWidget(self.tpmsWarnLabel)
        warnLayout.addWidget(self.gpsWarnLabel)
        warnLayout.addWidget(self.dateLabel)
        warnLayout.addWidget(self.timeLabel)
        warnLayout.addWidget(self.tempLabel)
        warnLayout.addWidget(powerButton)

        centralLayout = QVBoxLayout()
        centralLayout.addWidget(self.TabWidget, 1)
        centralLayout.addLayout(warnLayout)

        size = 32
        self.dashboard_index = self.TabWidget.addTab(self.pages[0], "")
        self.TabWidget.setTabIcon(self.dashboard_index, QIcon(self.prefix + 'speedometer.png'))
        self.TabWidget.setIconSize(QtCore.QSize(size, size))

        self.gps_index = self.TabWidget.addTab(self.pages[1], "")
        self.TabWidget.setTabIcon(self.gps_index, QIcon(self.prefix + 'gps.png'))
        self.TabWidget.setIconSize(QtCore.QSize(size, size))

        self.dc_index = self.TabWidget.addTab(self.pages[2], "")
        self.TabWidget.setTabIcon(self.dc_index, QIcon(self.prefix + 'camera.png'))
        self.TabWidget.setIconSize(QtCore.QSize(size, size))

        self.tpms_index = self.TabWidget.addTab(self.pages[3], "")
        self.TabWidget.setTabIcon(self.tpms_index, QIcon(self.prefix + 'tpms_warn_off.png'))
        self.TabWidget.setIconSize(QtCore.QSize(size, size))

        self.ruuvi_index = self.TabWidget.addTab(self.pages[4], "")
        self.TabWidget.setTabIcon(self.ruuvi_index, QIcon(self.prefix + 'weather.png'))
        self.TabWidget.setIconSize(QtCore.QSize(size, size))

        self.settings_index = self.TabWidget.addTab(self.pages[5], "")
        self.TabWidget.setTabIcon(self.settings_index, QIcon(self.prefix + 'settings.png'))
        self.TabWidget.setIconSize(QtCore.QSize(size, size))

        self.info_index = self.TabWidget.addTab(self.pages[6], "")
        self.TabWidget.setTabIcon(self.info_index, QIcon(self.prefix + 'info.png'))
        self.TabWidget.setIconSize(QtCore.QSize(size, size))

        self.TabWidget.setStyleSheet('''
            QTabBar::tab { height: 32px; width: 64px; color: #000000;}
            QTabBar::tab:selected {background-color: #373636;}
            QTabBar::tab:selected {font: 16pt bold; color: #000000}
            QTabBar::tab {margin: 0px;}
            ''')

        self.centralWidget.setLayout(centralLayout)
        self.setCentralWidget(self.centralWidget)

        self.TabWidget.currentChanged.connect(self.tabChanged)

    def init_dashcam_ui(self, page):
        page.setGeometry(0, 0, self.resolution.width(), self.resolution.height())

        recButton = QPushButton("", self)
        recButton.setIcon(QIcon(self.prefix + 'rec.png'))
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
        snapshotButton.setIcon(QIcon(self.prefix + 'snapshot.png'))
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

        self.previewLabel = QLabel("", self)
        self.previewLabel.setStyleSheet("background-color: black;"
                                        "border-style: outset;"
                                        "border-width: 1px;"
                                        "border-radius: 8px;"
                                        "border-color: beige;"
                                        "font: bold 32px;"
                                        "color: black;"
                                        "min-width: 565px;"
                                        "min-height: 320px;"
                                        "padding: 4px;")

        self.virbBattLabel = QLabel()
        self.virbBattLabel.setText(" VBat -- %")
        self.virbBattLabel.setStyleSheet("QLabel {color: white; font: bold 24px}")
        self.virbBattLabel.setAlignment(Qt.AlignRight)

        vbox = QVBoxLayout()
        vbox.setAlignment(Qt.AlignCenter)
        vbox.addWidget(recButton)
        vbox.addWidget(snapshotButton)
        vbox.addWidget(self.virbBattLabel)

        hbox = QHBoxLayout()
        hbox.setSpacing(40)
        hbox.addLayout(vbox)
        hbox.setAlignment(Qt.AlignCenter)
        hbox.addWidget(self.previewLabel)

        page.setLayout(hbox)

    def init_dashboard_ui(self, page):
        page.setGeometry(0, 0, self.resolution.width(), self.resolution.height())
        web = QWebView()
        web.settings().setAttribute(QWebSettings.JavascriptEnabled, True)
        web.settings().setAttribute(QWebSettings.LocalContentCanAccessRemoteUrls, True);
        web.load(QUrl("http://my.dashboard.com"))

        vbox = QVBoxLayout()
        vbox.addWidget(web)
        page.setLayout(vbox)

    def init_gps_ui(self, page):
        page.setGeometry(0, 0, self.resolution.width(), self.resolution.height())

        lat_label = QLabel("Latitude")
        lat_label.setFixedWidth(200)
        lat_label.setStyleSheet("font: bold 16px;"
                                "color: white;")

        lon_label = QLabel("Longitude")
        lon_label.setFixedWidth(200)
        lon_label.setStyleSheet("font: bold 16px;"
                                "color: white;")

        alt_label = QLabel("Altitude")
        alt_label.setFixedWidth(200)
        alt_label.setStyleSheet("font: bold 16px;"
                                "color: white;")
        hbox1 = QHBoxLayout()
        hbox1.setSpacing(20)
        hbox1.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
        hbox1.addWidget(lat_label)
        hbox1.addWidget(lon_label)
        hbox1.addWidget(alt_label)

        self.lat = QLabel("--")
        self.lat.setFixedWidth(200)
        self.lat.setStyleSheet("font: bold 32px;"
                               "color: white;")

        self.lon = QLabel("--")
        self.lon.setFixedWidth(200)
        self.lon.setStyleSheet("font: bold 32px;"
                                "color: white;")

        self.alt = QLabel("--")
        self.alt.setFixedWidth(200)
        self.alt.setStyleSheet("font: bold 32px;"
                               "color: white;")
        hbox2 = QHBoxLayout()
        hbox2.setSpacing(20)
        hbox2.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        hbox2.addWidget(self.lat)
        hbox2.addWidget(self.lon)
        hbox2.addWidget(self.alt)

        self.address = QLabel("")
        self.address.setStyleSheet("font: 24px;"
                                   "color: white;")
        hbox3 = QHBoxLayout()
        hbox3.setSpacing(20)
        hbox3.setAlignment(Qt.AlignCenter)
        hbox3.addWidget(self.address)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        vbox.addLayout(hbox3)

        page.setLayout(vbox)

    def init_tpms_ui(self, page):
        page.setGeometry(0, 0, self.resolution.width(), self.resolution.height())
        pressure = "-- bar"
        temperature = "-- "
        self.fl_label = QLabel(pressure + "\n" + temperature + "\u2103")
        self.fr_label = QLabel(pressure + "\n" + temperature + "\u2103")
        self.rl_label = QLabel(pressure + "\n" + temperature + "\u2103")
        self.rr_label = QLabel(pressure + "\n" + temperature + "\u2103")

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

        pixmap = QPixmap(self.prefix + "tire.png").scaled(128, 128, Qt.KeepAspectRatio)

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

    def init_ruuvitag(self, page):
        page.setGeometry(0, 0, self.resolution.width(), self.resolution.height())

        outdoor = QLabel("OUTDOOR:")
        outdoor.setStyleSheet("font: bold 32px;"
                              "color: white;")
        outdoor.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.temperatureLabel = QLabel(" --\u2103")
        self.temperatureLabel.setStyleSheet("font: bold 48px;"
                                            "color: white;")
        self.temperatureLabel.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)

        self.humidityLabel = QLabel("-- %")
        self.humidityLabel.setStyleSheet("font: bold 48px;"
                                         "color: white;")
        self.humidityLabel.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)

        self.pressureLabel = QLabel("-- hPa")
        self.pressureLabel.setStyleSheet("font: bold 48px;"
                                         "color: white;")
        self.pressureLabel.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)

        self.voltageLabel = QLabel()
        self.voltageLabel.setStyleSheet("font: bold 32px;"
                                        "color: yellow")
        self.voltageLabel.setAlignment(Qt.AlignRight)

        vbox = QVBoxLayout()
        vbox.addWidget(outdoor)
        vbox.addWidget(self.temperatureLabel)
        vbox.addWidget(self.humidityLabel)
        vbox.addWidget(self.pressureLabel)
        vbox.addWidget(self.voltageLabel)
        page.setLayout(vbox)

        self.initRuuvitagThread()

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

    def init_info_ui(self, page):
        conf_file = str(Path.home()) + "/.motorhome/tpms.conf"
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

        pixmap = QPixmap(typeLabel).scaled(256, 256, Qt.KeepAspectRatio)
        typeLabel = QLabel()
        typeLabel.setPixmap(pixmap)
        typeLabel.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)

        pixmap = QPixmap(makerLabel).scaled(256, 256, Qt.KeepAspectRatio)
        makerLabel = QLabel()
        makerLabel.setPixmap(pixmap)
        makerLabel.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)

        try:
            vinLabel = QLabel("VIN " + config['Maker']['vin'])
        except:
            vinLabel = QLabel()

        vinLabel.setStyleSheet("QLabel {color: white; font: bold 16px}")
        vinLabel.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)

        hbox = QHBoxLayout()
        hbox.addWidget(typeLabel)
        hbox.addWidget(makerLabel)

        vbox = QVBoxLayout()
        vbox.addWidget(modelLabel)
        vbox.addWidget(chassisLabel)
        vbox.addWidget(vinLabel)
        vbox.addLayout(hbox)

        page.setLayout(vbox)

    def initStartRecThread(self):
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

    def initStopRecThread(self):
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
        if self.ip == "":
            return

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

    def initTPMSThread(self):
        self.tpmsThread = QThread()
        self.tpmsWorker = TPMS()
        self.exit_signal.connect(self.tpmsWorker.stop)
        self.tpmsWorker.moveToThread(self.tpmsThread)
        self.tpmsWorker.finished.connect(self.tpmsThread.quit)
        self.tpmsWorker.finished.connect(self.tpmsWorker.deleteLater)
        self.tpmsThread.finished.connect(self.tpmsThread.deleteLater)
        self.tpmsThread.started.connect(self.tpmsWorker.run)

        self.tpmsWorker.tpms.connect(self.setTPMS)

        self.tpmsThread.start()

    def initGPSThread(self):
        if self.ip == "":
            return

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

        self.worker.gpsBatt.connect(self.updateBatt)
        self.worker.gpsLocation.connect(self.updateLocation)

        self.thread.started.connect(self.worker.run)

        self.thread.start()

    def initRuuvitagThread(self):
        conf_file = str(Path.home()) + "/.motorhome/tpms.conf"
        config = configparser.ConfigParser()

        try:
            config.read(conf_file)
            mac = config['RuuviTag']['mac']
        except:
            return

        self.ruuviThread =  QThread()
        self.ruuviWorker = RuuviTag(mac)
        self.exit_signal.connect(self.ruuviWorker.stop)
        self.ruuviWorker.moveToThread(self.ruuviThread)

        self.ruuviWorker.finished.connect(self.ruuviThread.quit)
        self.ruuviWorker.finished.connect(self.ruuviWorker.deleteLater)
        self.ruuviThread.finished.connect(self.ruuviThread.deleteLater)

        self.ruuviThread.started.connect(self.ruuviWorker.run)

        self.ruuviWorker.exit_signal.connect(self.ruuviWorker.stop)

        self.ruuviWorker.temperature.connect(self.updateTemperature)
        self.ruuviWorker.humidity.connect(self.updateHumidity)
        self.ruuviWorker.pressure.connect(self.updatePressure)
        self.ruuviWorker.ruuvi_batt.connect(self.updateRuuviBatt)

        self.ruuviThread.started.connect(self.ruuviWorker.run)

        self.ruuviThread.start()

    def record(self, button):
        if button.isChecked():
            button.setIcon(QIcon(self.prefix + 'stop.png'))
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
            button.setIcon(QIcon(self.prefix + 'rec.png'))
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
        if index == self.dc_index:
            self.previewEnabled = True
            self.setup_camera()
        else:
            self.previewEnabled = False
            self.setup_camera()

        if index == self.gps_index and self.network_available:
            self.updateAddress = True
        else:
            self.updateAddress = False


    def updateLocation(self, location):
        geolocation = Geolocation("motorhome")

        self.lat.setText("{:.5f}".format(location[0]))
        self.lon.setText("{:.5f}".format(location[1]))
        self.alt.setText("{:.0f}".format(location[2]))

        if self.updateAddress:
            self.address.setText(geolocation.get_address((location[0], location[1])))

        self.gps_ts = datetime.now()

    def updateBatt(self, batt):
       if batt < 5:
           self.virbBattLabel.setStyleSheet("QLabel {color: red; font: bold 24px}")
       elif batt >= 5 and batt < 20:
           self.virbBattLabel.setStyleSheet("QLabel {color: yellow; font: bold 24px}")
       else:
           self.virbBattLabel.setStyleSheet("QLabel {color: white; font: bold 24px}")

       self.virbBattLabel.setText("VBat " + str(batt) + "%")

    def updatePreview(self, pixmap):
        self.previewLabel.setPixmap(pixmap.scaled(int(704*self.previewScale/100), int(396*self.previewScale/100),
                                                  QtCore.Qt.KeepAspectRatio))

    def updateTemperature(self, temperature):
        if temperature < 3:
            self.tempWarnLabel.setPixmap(self.temp_warn_on)
        elif temperature > 3.2:
            self.tempWarnLabel.setPixmap(self.temp_warn_off)

        self.tempLabel.setText("{:.1f}".format(round(temperature, 1)) + " \u2103")
        self.temperatureLabel.setText("{:.1f}".format(round(temperature, 1)) + " \u2103")

    def updateHumidity(self, humidity):
        self.humidityLabel.setText("{:.0f}".format(round(humidity)) + " %")

    def updatePressure(self, pressure):
        self.pressureLabel.setText("{:.0f}".format(round(pressure)) + " hPa")

    def updateRuuviBatt(self, voltage):
        if voltage < 2.75:
            self.voltageLabel.setText("RuuviTag battery low: " + "{:.2f}".format(round(voltage/1000, 2)) + " V")

    def updateDateTime(self):
        t = datetime.now()
        self.dateLabel.setText("{:02d}".format(t.day) + "." + "{:02d}".format(t.month) + "\n" + str(t.year))
        self.timeLabel.setText("{:02d}".format(t.hour) + ":" + "{:02d}".format(t.minute))

        if not self.previewEnabled:
            diff = t - self.gps_ts
            if diff.total_seconds() > 5:
                self.gpsWarnLabel.setPixmap(self.gps_disconnected)
                self.gps_connection = False
            elif not self.gps_connection:
                self.gpsWarnLabel.setPixmap(self.gps_connected)
                self.gps_connection = True

    def setup_camera(self):
        if self.previewEnabled:
            print("preview enabled")
            self.stop_signal.emit()

            self.initPreviewThread()

        else:
            print("preview disabled")
            self.start_signal.emit()

            self.stop_preview.emit()

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

    def setTPMS(self, sensor):
        self.tire.setPressure(sensor[0], sensor[1])
        self.tire.setTemperature(sensor[0], sensor[2])

        if sensor[0] == 'FL':
            if sensor[3] == '1':
                self.fl_label.setStyleSheet("color:yellow")
            else:
                self.fl_label.setStyleSheet("color:green")
            self.fl_label.setText(str(self.tire.FrontLeftPressure)  + " bar\n" + str(self.tire.FrontLeftTemp) + " \u2103")
        elif sensor[0] == 'FR':
            if sensor[3] == '1':
                self.fr_label.setStyleSheet("color:yellow")
            else:
                self.fr_label.setStyleSheet("color:green")
            self.fr_label.setText(str(self.tire.FrontRightPressure)  + " bar\n" + str(self.tire.FrontRightTemp) + " \u2103")
        elif sensor[0] == 'RL':
            if sensor[3] == '1':
                self.rl_label.setStyleSheet("color:yellow")
            else:
                self.rl_label.setStyleSheet("color:green")
            self.rl_label.setText(str(self.tire.RearLeftPressure)  + " bar\n" + str(self.tire.RearLeftTemp) + " \u2103")
        elif sensor[0] == 'RR':
            if sensor[3] == '1':
                self.rr_label.setStyleSheet("color:yellow")
            else:
                self.rr_label.setStyleSheet("color:green")
            self.rr_label.setText(str(self.tire.RearRightPressure)  + " bar\n" + str(self.tire.RearRightTemp) + " \u2103")

        # turn on/off TPMS warn light
        if self.tpmsFLflag or self.tpmsFRflag or self.tpmsRLflag or self.tpmsRRflag:
            self.tpmsWarnLabel.setPixmap(self.tpms_warn_on)
            self.tpmsWarnLabel.setAlignment(Qt.AlignVCenter)
            self.TabWidget.setTabIcon(self.tpms_index, QIcon(self.prefix + 'tpms_warn_on.png'))
            self.TabWidget.setCurrentIndex(self.tabs, self.tpms_index)
        else:
            self.tpmsWarnLabel.setPixmap(self.tpms_warn_off)
            self.tpmsWarnLabel.setAlignment(Qt.AlignVCenter)
            self.TabWidget.setTabIcon(self.tpms_index, QIcon(self.prefix + 'tpms_warn_off.png'))

    def poweroff(self):
        os.system("sudo shutdown -h now")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            try:
                self.datetimer.stop()
            except:
                pass

            self.exit_signal.emit()
            #ugly but efficient
            time.sleep(5)
            system = psutil.Process(os.getpid())
            system.terminate()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkgraystyle.load_stylesheet())
    win = MainApp()
    sys.exit(app.exec_())

