"""
GPS daemon thread
"""
import time
import subprocess
import math

from datetime import datetime, timedelta
from gps3.agps3threaded import AGPS3mechanism
from virb import Virb

from PyQt5.QtCore import pyqtSignal, QObject

def update_datetime(date, update):
    """ update date and time for system clock """
    if date == "n/a" or update:
        return update

    print("GPS Thread: Update date and time")
    utc_offset = time.localtime().tm_gmtoff
    my_time = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.%fZ")
    timezone = timedelta(seconds=utc_offset)
    my_time += timezone

    cur_date = my_time.strftime('{:}'.format(my_time.strftime('%Y-%m-%d %H:%M:%S')))
    subprocess.call(['sudo', 'date', '-s', cur_date])

    return True

def get_virb_location(virb):
    lat = virb.get_latitude()
    lon = virb.get_longitude()
    alt = virb.get_altitude()
    speed = virb.get_speed()
    course = math.nan
    src = 1

    if lat != -999 or lon != -999 or alt != -999:
        mode = 3
    else:
        mode = 0

    location = (lat, lon, alt, speed, course, src)

    return location, mode

class Location(QObject):
    """ location class """
    finished = pyqtSignal()
    exit_signal = pyqtSignal()

    gpsLocation = pyqtSignal(tuple)
    gpsFix = pyqtSignal(int)

    def __init__(self, parent=None):
        QObject.__init__(self, parent=parent)
        self.running = True
        self.virb = Virb()
        self.virb_initialized = False
        self.gps_thread = AGPS3mechanism()
        self.gps_thread.stream_data()

    def run(self):
        """ Run gps sensor data receiver """
        self.gps_thread.run_thread()
        mode, mode_prev, prev = 0, 0, 0
        time_updated = False

        while self.running:
            now = time.monotonic()
            if now - prev >= 0.2:
                prev = now
                try:
                    if not time_updated:
                        time_updated = update_datetime(self.gps_thread.data_stream.time,
                                                       time_updated)

                    mode = int(self.gps_thread.data_stream.mode)

                    # 2D or 3D fix required
                    if mode > 1:
                        lat = float(self.gps_thread.data_stream.lat)
                        lon = float(self.gps_thread.data_stream.lon)
                        alt = float(self.gps_thread.data_stream.alt)
                        speed = float(self.gps_thread.data_stream.speed)
                        course = float(self.gps_thread.data_stream.track)
                        src = 0
                    elif self.virb_initialized:
                        location, mode = get_virb_location(self.virb)
                        time.sleep(0.9)

                    # emit GPS fix if changed
                    if mode != mode_prev:
                        self.gpsFix.emit(mode)
                        mode_prev = mode
                    if mode > 1:
                        self.gpsLocation.emit(location)

                except ValueError:
                    if self.virb_initialized:
                        location, mode = get_virb_location(self.virb)
                        time.sleep(0.9)

                        # emit GPS fix if changed
                        if mode != mode_prev:
                            self.gpsFix.emit(mode)
                            mode_prev = mode
                        if mode > 1:
                            self.gpsLocation.emit(location)
                    else:
                        pass

            time.sleep(0.1)

        print("GPS thread: thread finished")
        self.finished.emit()

    def stop(self):
        """Stop running the gps thread"""
        print("GPS thread: received exit signal")
        self.running = False
        self.virb_initialized = False

    def init_virb(self, ip):
        """Received Garmin Virb ip"""
        print("GPS thread: received Garmin Virb ip: " + ip)
        self.virb.ip = ip
        self.virb = Virb((self.virb.ip, 80))
        self.virb_initialized = True
