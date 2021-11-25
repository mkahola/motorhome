"""
Speedometer GUI
"""
import math
from datetime import datetime
from pathlib import Path

from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QSize, pyqtSignal

class SpeedoWindow(QWidget):
    """ Speedometer GUI implementation """
    info = pyqtSignal(dict)

    def create_window(self, infobar):
        """ Create window for speedometer """
        super(SpeedoWindow, self).__init__(None)

        self.setStyleSheet(open('res/childs.css', 'r').read())

        self.setWindowTitle("Speedometer")
        self.prefix = str(Path.home()) + "/.motorhome/res/"

        home_button = QPushButton()
        home_button.setIcon(QIcon(self.prefix + 'home.png'))
        home_button.setIconSize(QSize(64, 64))
        home_button.clicked.connect(self.exit)

        # time
        self.time_label = QLabel()

        # TPMS warn light
        self.tpms_warn_off = QPixmap("")
        self.tpms_warn_on = QPixmap(self.prefix + "tpms_warn_on.png").scaled(32, 32, Qt.KeepAspectRatio)
        self.tpms_warn_label = QLabel()

        # GPS fix
        self.gps_disconnected = QPixmap(self.prefix + "no_gps.png").scaled(32, 32, Qt.KeepAspectRatio)
        self.gps_connected = QPixmap("")
        self.gps_info_label = QLabel()
        self.gps_speed_label = QLabel("--")
        self.gps_speed_label.setStyleSheet("font: 240px")

        # Ruuvitag
        self.temp_info_label = QLabel()
        self.temp_warn_off = QPixmap("")
        self.temp_warn_on = QPixmap(self.prefix + "snowflake.png").scaled(32, 32, Qt.KeepAspectRatio)
        self.temp_warn_label = QLabel()

        # recording
        self.rec_info_label = QLabel()
        self.rec_off = QPixmap("")
        self.rec_on = QPixmap(self.prefix + "rec.png").scaled(32, 32, Qt.KeepAspectRatio)

        self.update_temperature(infobar.temperature)
        self.update_tpmswarn(infobar.tpmsWarn)
        self.update_time(datetime.now())
        self.update_gps_fix(infobar.gpsFix)
        self.update_speed(infobar.speed)
        self.update_recording(infobar.recording)

        #infobar
        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.tpms_warn_label, alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.temp_warn_label, alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.gps_info_label, alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.rec_info_label, alignment=Qt.AlignTop|Qt.AlignLeft)
        hbox1.addWidget(self.temp_info_label, alignment=Qt.AlignTop|Qt.AlignRight)
        hbox1.addWidget(self.time_label, alignment=Qt.AlignTop|Qt.AlignRight)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addWidget(QLabel("km/h"), alignment=Qt.AlignCenter)
        vbox.addWidget(self.gps_speed_label, alignment=Qt.AlignCenter)
        vbox.addWidget(home_button, alignment=Qt.AlignCenter)
        self.setLayout(vbox)

        self.showFullScreen()

    def update_infobar(self, data):
        """ update infobar on top of the screen """
        self.update_speed(data['speed'])
        self.update_time(data['time'])
        self.update_temperature(data['temperature'])
        self.update_tpmswarn(data['tpms'])
        self.update_gps_fix(data['gpsFix'])
        self.update_recording(data['recording'])

    def update_time(self, time_data):
        """ update time """
        self.time_label.setText("{:02d}".format(time_data.hour) + ":" + "{:02d}".format(time_data.minute))

    def update_speed(self, speed):
        """ update speed """
        if math.isnan(speed):
            return
        self.gps_speed_label.setText("{:d}".format(round(3.6*speed)))

    def update_temperature(self, temperature):
        """ update temperature """
        if math.isnan(temperature):
            return

        self.temp_info_label.setText("{0:d}".format(round(temperature)) + "\u2103")
        if temperature < 3.0:
            self.temp_warn_label.setPixmap(self.temp_warn_on)
        elif temperature > 3.2:
            self.temp_warn_label.setPixmap(self.temp_warn_off)

    def update_tpmswarn(self, warn):
        """ update tire pressure warn icon """
        if warn:
            self.tpms_warn_label.setPixmap(self.tpms_warn_on)
        else:
            self.tpms_warn_label.setPixmap(self.tpms_warn_off)

    def update_gps_fix(self, fix):
        """ update GPS fix """
        if fix:
            self.gps_info_label.setPixmap(self.gps_connected)
        else:
            self.gps_info_label.setPixmap(self.gps_disconnected)

    def update_recording(self, recording):
        """ update recording info """
        if recording:
            self.rec_info_label.setPixmap(self.rec_on)
        else:
            self.rec_info_label.setPixmap(self.rec_off)

    def exit(self):
        """ exit window """
        self.close()
