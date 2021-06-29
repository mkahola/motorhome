from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import QtCore, QtGui

import time
import math
import nmap3
import subprocess

from netifaces import interfaces, ifaddresses, AF_INET
from datetime import datetime, timedelta
from gps3.agps3threaded import AGPS3mechanism

from virb import Virb

def update_datetime(dt, update):
    if dt == "n/a" or update:
        return update

    print("GPS Thread: Update date and time")
    utc_offset = time.localtime().tm_gmtoff
    my_time = datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S.%fZ")
    tz = timedelta(seconds=utc_offset)
    my_time += tz

    t = my_time.strftime('{:}'.format(my_time.strftime('%Y-%m-%d %H:%M:%S')))
    subprocess.call(['sudo', 'date', '-s', t])

    return True

class GPS(QObject):
    stop_signal = pyqtSignal()
    start_signal = pyqtSignal()
    finished = pyqtSignal()
    exit_signal = pyqtSignal()

    gpsBatt = pyqtSignal(int)
    gpsLocation = pyqtSignal(tuple)
    gpsFix = pyqtSignal(int)

    def __init__(self, ip, parent=None):
        QObject.__init__(self, parent=parent)
        self.running = True
        self.request = True
        self.camera = Virb((ip, 80))
        self.ip = ip

        self.gps_thread = AGPS3mechanism()
        self.gps_thread.stream_data()

    def run(self):
        self.gps_thread.run_thread()
        batt_ts = 0
        mode_prev = 0
        prev = 0
        time_updated = False

        while self.running:
            now = time.monotonic()
            if self.request:
                try_virb = False
                if not time_updated:
                    time_updated = update_datetime(self.gps_thread.data_stream.time, time_updated)

                if now - prev >= 1.0:
                    prev = now
                    try:
                        mode = int(self.gps_thread.data_stream.mode)
                        if mode != mode_prev:
                            self.gpsFix.emit(mode)
                            mode_prev = mode

                        # 2D or 3D fix required
                        if mode > 1:
                            lat = float(self.gps_thread.data_stream.lat)
                            lon = float(self.gps_thread.data_stream.lon)
                            alt = float(self.gps_thread.data_stream.alt)
                            location = (lat, lon, alt)
                            self.gpsLocation.emit(location)
                        else:
                            try_virb = True
                    except:
                        print("Trying Garmin Virb")
                        try_virb = True

                    if try_virb:
                        print("GPS from Garmin Virb")
                        try:
                            status = self.camera.status()
                            location = (status['gpsLatitude'], status['gpsLongitude'], status['altitude'])
                            self.gpsLocation.emit(location)
                        except:
                            print("data unavailable")
                            pass

                if now - batt_ts > 30:
                    print("Garmin Virb battery status update")
                    try:
                        status = self.camera.status()
                        self.gpsBatt.emit(round(float(status['batteryLevel'])))
                        batt_ts = now
                    except:
                        pass
            else:
                print("status requests halted")

            time.sleep(0.1)

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
