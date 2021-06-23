#!/usr/bin/env python3
import time
import subprocess

from datetime import datetime, timedelta
from gps3.agps3threaded import AGPS3mechanism

def do_update_datetime(dt, update):
    if dt == "n/a" or update:
        return update

    print("Updating date and time")
    utc_offset = time.localtime().tm_gmtoff
    my_time = datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S.%fZ")
    tz = timedelta(seconds=utc_offset)
    my_time += tz

    t = my_time.strftime('{:}'.format(my_time.strftime('%Y-%m-%d %H:%M:%S')))
    subprocess.call(['sudo', 'date', '-s', t])

    return True

def update_datetime():
    date_updated = False
    gps_thread = AGPS3mechanism()
    gps_thread.stream_data()
    gps_thread.run_thread()

    while not date_updated:
        date_updated = do_update_datetime(gps_thread.data_stream.time, date_updated)

if __name__ == "__main__":
    update_datetime()
