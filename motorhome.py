#!/usr/bin/env python3

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import QtWidgets, QtCore, QtGui

#from PyQt5.QtWebKitWidgets import QWebView, QWebPage
#from PyQt5.QtWebKit import QWebSettings
#from PyQt5.QtNetwork import *

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

camera = 0 #virtual device

messages = ['Tire pressure low on front left tire',
            'Tire pressure low on front right tire',
            'Tire pressure low on rear left tire',
            'Tire pressure low on rear right tire',
            'Stairs down']

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: black;")
        self.setWindowTitle("Motorhome Info")
        self.warns = self.Warnings()
        self.warning = "No messages"
        self.resolution = QDesktopWidget().availableGeometry(-1)
        self.setup_ui()
        self.setup_camera()
        self.setup_warns()
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

        #Initialize widgets
        self.centralWidget = QWidget()

        self.TabWidget = QTabWidget(self)
        self.TabWidget.setFont(QFont("Sanserif", 16))

        self.pages = [QWidget(), QWidget(), QWidget(), QWidget(), QWidget()]

        self.pages[0].setGeometry(0, 0, self.resolution.width(), self.resolution.height())
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        vbox1 = QVBoxLayout()
        vbox1.addWidget(self.image_label)
        self.pages[0].setLayout(vbox1)

        self.pages[1].setGeometry(0, 0, self.resolution.width(), self.resolution.height())
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

        vbox2 = QGridLayout()
        vbox2.addWidget(self.fl_label, 0, 0)
        vbox2.addWidget(tire1_label, 0, 1)
        vbox2.addWidget(tire2_label, 0, 2)
        vbox2.addWidget(self.fr_label, 0, 3)
        vbox2.addWidget(self.rl_label, 1, 0)
        vbox2.addWidget(tire3_label, 1, 1)
        vbox2.addWidget(tire4_label, 1, 2)
        vbox2.addWidget(self.rr_label, 1, 3)
        self.pages[1].setLayout(vbox2)

        # messages
        self.pages[2].setGeometry(0, 0, self.resolution.width(), self.resolution.height())
        self.msg_list = QListWidget()
        self.msg_list.setFont(QFont("Sanserif", 16))
        self.msg_model = QStandardItemModel(self.msg_list)
        vbox3 = QVBoxLayout()
        vbox3.addWidget(self.msg_list)
        self.pages[2].setLayout(vbox3)

        font = self.fl_label.font()
        font.setPointSize(16)
        font.setBold(True)

        # Tire pressure warnig level
        self.pages[3].setGeometry(0, 0, self.resolution.width(), self.resolution.height())
        self.low_pressure = QSlider(Qt.Horizontal, self)
        self.low_pressure.setFocusPolicy(Qt.NoFocus)
        self.low_pressure.setRange(10, 50)
        self.low_pressure.setPageStep(1)
        self.low_pressure.valueChanged.connect(self.changePressureLevel)
        self.low_pressure.sliderReleased.connect(self.updateConfig)
        self.ptitle_label = QLabel("TPMS warn level", self)
        self.ptitle_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.ptitle_label.setFont(QFont("Sanserif", 16))
        self.pslider_label = QLabel(" 1 bar", self)
        self.pslider_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.pslider_label.setMinimumWidth(60)
        self.pslider_label.setFont(QFont("Sanserif", 16))
        vbox4 = QHBoxLayout()
        vbox4.addWidget(self.ptitle_label)
        vbox4.addSpacing(10)
        vbox4.addWidget(self.low_pressure)
        vbox4.addSpacing(10)
        vbox4.addWidget(self.pslider_label)
        self.pages[3].setLayout(vbox4)

        # warn lights
        self.tpms_warn_off = QPixmap(prefix + "tpms_warn_off.png").scaled(64, 64, Qt.KeepAspectRatio)
        self.tpms_warn_on = QPixmap(prefix + "tpms_warn_on.png").scaled(64, 64, Qt.KeepAspectRatio)
        self.tpmsWarnLabel = QLabel()
        self.tpmsWarnLabel.setPixmap(self.tpms_warn_off)
        self.tpmsWarnLabel.setAlignment(Qt.AlignVCenter)

        centralLayout = QVBoxLayout()
        centralLayout.addWidget(self.TabWidget, 1)
        centralLayout.addWidget(self.tpmsWarnLabel)

        self.dc_index = self.TabWidget.addTab(self.pages[0], "Dashcam")
        self.tp_index = self.TabWidget.addTab(self.pages[1], "Tire Pressure")
        self.warn_index = self.TabWidget.addTab(self.pages[2], "Messages(0)")
        self.settings_index = self.TabWidget.addTab(self.pages[3], "Settings")

        self.TabWidget.setStyleSheet('''
            QTabBar::tab:selected {background-color: black;}
            QTabBar::tab:selected {font: 16pt bold}
            ''')

        self.centralWidget.setLayout(centralLayout)
        self.setCentralWidget(self.centralWidget)

    def setup_camera(self):
        #Initialize camera playback
        self.cap = cv2.VideoCapture(camera)

        try:
            self.cap.isOpened()
        except:
            self.cap.release()
            return
#            exit('Failure')

        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = float(self.cap.get(cv2.CAP_PROP_FPS))
        print("video: " + str(width) + "x" + str(height) + "@" + str(fps))

        self.timer = QTimer()
        self.timer.timeout.connect(self.display_video_stream)

        try:
            self.timer.start(int(1000/fps))
        except ZeroDivisionError:
            self.cap.release()
            return
#            exit('Failure')

    def display_video_stream(self):
        scale = 80

        #Read frame from camera
        ret, frame = self.cap.read()

        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            font = cv2.FONT_HERSHEY_DUPLEX
            datestr = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            cv2.putText(frame, datestr, (5, frame.shape[0]-10), font, 1, (255, 255, 0), 2, cv2
.LINE_AA)

            image = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(image).scaled(int(self.resolution.width()*scale/100),
                                                     int(self.resolution.height()*scale/100),
                                                     Qt.KeepAspectRatio)
            self.image_label.setPixmap(pixmap)

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
        print(conf_file)
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

        return False

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

        self.msg_title = "Messages(" + str(self.msg_list.count()) + ")"
        self.warn_index = self.TabWidget.setTabText(2, self.msg_title)

        # turn on/off TPMS warn light
        if self.tpmsFLflag or self.tpmsFRflag or self.tpmsRLflag or self.tpmsRRflag:
            self.tpmsWarnLabel.setPixmap(self.tpms_warn_on)
            self.tpmsWarnLabel.setAlignment(Qt.AlignVCenter)
        else:
            self.tpmsWarnLabel.setPixmap(self.tpms_warn_off)
            self.tpmsWarnLabel.setAlignment(Qt.AlignVCenter)

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
            self.cap.release()

            try:
                self.timer.stop()
            except:
                print("display timer not running")
                pass

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
