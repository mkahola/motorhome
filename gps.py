"""
GPS daemon thread
"""
import time
import subprocess

from datetime import datetime, timedelta
from gps3.agps3threaded import AGPS3mechanism

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

class Location(QObject):
    """ location class """
    finished = pyqtSignal()
    exit_signal = pyqtSignal()

    gpsLocation = pyqtSignal(tuple)
    gpsFix = pyqtSignal(int)

    def __init__(self, parent=None):
        QObject.__init__(self, parent=parent)
        self.running = True

        self.gps_thread = AGPS3mechanism()
        self.gps_thread.stream_data()

    def run(self):
        """ Run gps sensor data receiver """
        self.gps_thread.run_thread()
        mode_prev = 0
        prev = 0
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
                    if mode != mode_prev:
                        self.gpsFix.emit(mode)
                        mode_prev = mode

                    # 2D or 3D fix required
                    if mode > 1:
                        lat = float(self.gps_thread.data_stream.lat)
                        lon = float(self.gps_thread.data_stream.lon)
                        alt = float(self.gps_thread.data_stream.alt)
                        speed = float(self.gps_thread.data_stream.speed)
                        course = float(self.gps_thread.data_stream.track)
                        location = (lat, lon, alt, speed, course)
                        self.gpsLocation.emit(location)
                except ValueError:
                    pass
            time.sleep(0.1)

        print("GPS thread: thread finished")
        self.finished.emit()

    def stop(self):
        """Stop running the gps thread"""
        print("GPS thread: received exit signal")
        self.running = False
