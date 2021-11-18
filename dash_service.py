#!/usr/bin/env python3

# WS server that sends dasboard data

import asyncio
import websockets
import subprocess
import configparser
import nmap
import time
import math
import json
import threading

from datetime import datetime, timedelta
from pathlib import Path
from netifaces import interfaces, ifaddresses, AF_INET
from gps3.agps3threaded import AGPS3mechanism
from virb import Virb

virb_ip = ""

def ping_ok(ip):
    if not ip:
        return False

    try:
        cmd = "ping -c 1 " + ip
        output = subprocess.check_output(cmd, shell=True)
    except Exception as e:
        return False

    return True

def search_with_nmap():
    virb_ip = ""

    for iface_name in netifaces.interfaces():
        addresses = [i['addr'] for i in netifaces.ifaddresses(iface_name).setdefault(netifaces.AF_INET, [{'addr':'No IP addr'}])]
        if iface_name == "wlan0":
            my_ip = addresses[0].split('.')
            break

    my_ip[3] = "0/24"
    ip_addr = "."
    ip_addr = ip_addr.join(my_ip)

    nm = nmap.PortScanner()
    nm.scan(hosts=ip_addr, arguments='-sP')

    for i in nm.all_hosts():
        try:
            device = socket.gethostbyaddr(i)[0]
            if device == "Garmin-WiFi":
                virb_ip = i
                break
        except Exception as e:
            print("searchvirb: no hostname for " + i)
            pass

    return virb_ip

def search_virb():
    global virb_ip

    conf_file = str(Path.home()) + "/.motorhome/network.conf"
    config = configparser.ConfigParser()
    config.read(conf_file)

    ssid = subprocess.check_output(['sudo', 'iwgetid']).decode("utf-8").split('"')[1]

    try:
        virb_ip = config[ssid]['ip']
    except Exception as e:
        virb_ip = ""

    if not ping_ok(virb_ip):
        print("dash server: Searching Garmin Virb with nmap")
        virb_ip = search_with_nmap()
        if virb_ip:
            data = config[ssid]
            data['ip'] = virb_ip

            with open(conf_file, 'w') as configfile:
                config.write(configfile)

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

    threading.Thread(target=search_virb, daemon=True).start()

    print("running dash server")

    async def gps(websocket, path):
        global virb_ip
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
            if virb_ip and not virb_initialized:
                cam = Virb((virb_ip, 80))
                virb_initialized = True

            try:
                time_updated = update_datetime(gps_thread.data_stream.time,
                                               time_updated)
            except:
                pass

            try:
                mode = int(gps_thread.data_stream.mode)
            except KeyError:
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
                        pass

            try:
                if mode > 1:
                    data = json.dumps(d)
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
