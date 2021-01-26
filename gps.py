from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import QtCore, QtGui

import time

from virb import Virb

class GPS(QObject):
    stop_signal = pyqtSignal()
    start_signal = pyqtSignal()
    finished = pyqtSignal()
    exit_signal = pyqtSignal()

    gpsSpeed = pyqtSignal(int)
    gpsLat = pyqtSignal(float)
    gpsLon = pyqtSignal(float)
    gpsAlt = pyqtSignal(int)
    gpsBatt = pyqtSignal(int)

    def __init__(self, ip, parent=None):
        QObject.__init__(self, parent=parent)
        self.running = True
        self.request = True
        self.camera = Virb((ip, 80))
        self.ip = ip

    def run(self):

        while self.running:
            if self.request:
                try:
                    status = self.camera.status()
                    self.gpsBatt.emit(int(status['batteryLevel'] + 0.5))
                    self.gpsBatt.emit(int(status['batteryLevel'] + 0.5))
                except ConnectionError:
                    print("connection error")
                    time.sleep(10)
                    self.camera = Virb(self.ip, 80)
                    pass
                except:
                    print("data unavailable")
                    pass

                try:
                    self.gpsSpeed.emit(int(status['speed']*3.6))
                    self.gpsLon.emit(status['gpsLongitude'])
                    self.gpsLat.emit(status['gpsLatitude'])
                    self.gpsAlt.emit(int(status['altitude']))
                except:
                    print("unable to read status")
                    pass
            else:
                print("status requests halted")

            time.sleep(1)

        print("thread finished")
        self.finished.emit()

    def halt(self):
        print("received stop signal")
        self.request = False

    def stop(self):
        print("received exit signal")
        self.running = False

    def get_status(self):
        print("continuing status reqests")
        self.request = True
