#!/usr/bin/env python3

# WS server that sends dasboard data

import asyncio
import websockets
import subprocess
import configparser
import time
import math
import json

from datetime import datetime, timedelta
from pathlib import Path
from gps3.agps3threaded import AGPS3mechanism
from virb import Virb

def search_virb():

    conf_file = str(Path.home()) + "/.motorhome/network.conf"
    config = configparser.ConfigParser()
    config.read(conf_file)

    ssid = subprocess.check_output(['sudo', 'iwgetid']).decode("utf-8").split('"')[1]

    try:
        ip = config[ssid]['ip']
    except Exception as e:
        ip = ""

    return ip

def update_datetime(date, update):
    """ update date and time for system clock """
    if date == "n/a" or update:
        return update

    print("dash server: Update date and time")
    utc_offset = time.localtime().tm_gmtoff
    my_time = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.%fZ")
    timezone = timedelta(seconds=utc_offset)
    my_time += timezone

    cur_date = my_time.strftime('{:}'.format(my_time.strftime('%Y-%m-%d %H:%M:%S')))
    subprocess.call(['sudo', 'date', '-s', cur_date])

    return True

def run_dash_server():
    gps_thread = AGPS3mechanism()
    gps_thread.stream_data()
    gps_thread.run_thread()

    print("running dash server")

    async def gps(websocket, path):
        virb_initialized = False
        time_updated = False

        d = {'id': "gps",
             'lat': 0.0,
             'lon': 0.0,
             'alt': 0.0,
             'speed':0.0,
             'course': 0,
             'mode': 0,
             'src': "internal",
            }

        while True:
            try:
                time_updated = update_datetime(gps_thread.data_stream.time,
                                               time_updated)
            except:
                pass

            try:
                mode = int(gps_thread.data_stream.mode)
            except ValueError:
                print("dash server: Value not defined for GPS mode")
                await asyncio.sleep(1)
                continue

            if mode > 1:
                # speed in knots, convert to km/h
                d['lat'] = gps_thread.data_stream.lat
                d['lon'] = gps_thread.data_stream.lon
                d['alt'] = gps_thread.data_stream.alt
                d['speed']  = gps_thread.data_stream.speed
                d['course'] = gps_thread.data_stream.track
                d['src'] = "internal"
                d['mode'] = mode
            else:
                if virb_initialized:
                    try:
                        lat = cam.get_latitude()
                        lon = cam.get_longitude()
                        alt = cam.get_altitude()

                        if lat != -999 or lon != -999 or alt != -999:
                            mode = 3
                        else:
                            mode = 0

                        d['lat'] = lat
                        d['lon'] = lon
                        d['alt'] = alt
                        d['speed'] = cam.get_speed()
                        d['course'] = 0
                        d['src'] = "garmin"
                        d['mode'] = mode
                        time.sleep(0.8)
                    except:
                        virb_initialized = False
                        pass
                else:
                    virb_ip = search_virb()
                    if virb_ip:
                        cam = Virb((virb_ip, 80))
                        virb_initialized = True
            try:
                if mode > 1:
                    data = json.dumps(d)
                    print(data)
                    await websocket.send(data)
            except:
                pass
            await asyncio.sleep(0.2)

    try:
        start_server = websockets.serve(gps, port=5678)
    except:
        print("unable to start server")
        pass

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    run_dash_server()
