#!/usr/bin/env python3
"""
Backlight control based on local sunrise and sunset times
"""
import time
import math
import ephem
import subprocess

from crontab import CronTab
from datetime import datetime
from gps3.agps3threaded import AGPS3mechanism

def set_brightness(val, comment, timedata):
    val = str(round(val*255/100))

    platform = "rpi"

    cmd = "echo " + val + " | sudo tee -a /sys/class/backlight/" + platform + "_backlight/brightness > /dev/null"

    cron = CronTab(user='pi')
    cron.remove_all(comment=comment)
    job = cron.new(command=cmd, comment=comment)
    job.hour.on(timedata.hour)
    job.minute.on(timedata.minute)
    cron.write()

    return cmd

def backlight_ctrl():
    gps_thread = AGPS3mechanism()
    gps_thread.stream_data()
    gps_thread.run_thread()

    run = True
    while run:
        try:
            mode = int(gps_thread.data_stream.mode)

            # 2D or 3D fix required
            if mode > 1:
                lat = float(gps_thread.data_stream.lat)
                lon = float(gps_thread.data_stream.lon)
                run = False
        except ValueError:
            pass

        time.sleep(15)

    location = ephem.Observer()
    location.lat = str(lat)
    location.lon = str(lon)
    location.date = datetime.now()

    sun = ephem.Sun()

    sunrise = ephem.localtime(location.next_rising(sun))
    sunset = ephem.localtime(location.next_setting(sun))

    print("sunrise: " + str(sunrise.hour) + ":" + str(sunrise.minute))
    print("sunset: " + str(sunset.hour) + ":" + str(sunset.minute))

    cmd_sunrise = set_brightness(50, "sunrise", sunrise)
    cmd_sunset = set_brightness(15, "sunset", sunset)

    sunrise_stamp = sunrise.hour*60*60 + sunrise.minute*60 + sunrise.second
    sunset_stamp = sunset.hour*60*60 + sunrise.minute*60 + sunrise.second
    now = datetime.today()
    now = now.hour*60*60 + now.minute*60 + now.second

    if sunrise_stamp <= now <= sunset_stamp:
        subprocess.call(cmd_sunrise, shell=True)
    elif now > sunset_stamp:
        subprocess.call(cmd_sunset, shell=True)

if __name__ == "__main__":
    backlight_ctrl()
