#!/usr/bin/env python3

# WS server that sends dasboard data

import asyncio
import datetime
import random
import websockets
import subprocess
import configparser
from pathlib import Path
import nmap3
import time
import math

from netifaces import interfaces, ifaddresses, AF_INET
from gps3.agps3threaded import AGPS3mechanism
from virb import Virb

use_virb = True

def search_virb(my_device):
    virb_ip = ""

    def is_virb_ssid():
        ssid = subprocess.check_output(['sudo', 'iwgetid']).decode("utf-8").split('"')[1]
        if ssid == "VIRB-6267":
            return True

        return False

    if is_virb_ssid():
        return "192.168.0.1"

    while virb_ip == "":
        print("Dashboard searching Garmin Virb")

        for ifaceName in interfaces():
            addresses = [i['addr'] for i in ifaddresses(ifaceName).setdefault(AF_INET, [{'addr':'No IP addr'}] )]
            if ifaceName == "wlan0":
                my_ip = addresses[0].split('.')
                break

        my_ip[3] = "0/24"
        ip = "."
        ip = ip.join(my_ip)
        nmap = nmap3.NmapHostDiscovery()
        result=nmap.nmap_no_portscan(ip, "-sP")

        for i in range(len(result)):
             try:
                device = result[list(result.keys())[i]]['hostname'][0]['name']
                if device == my_device:
                    virb_ip = list(result)[i]
                    break
             except:
                    pass

             time.sleep(1)

    return virb_ip

def run_dash_server():
    async def gps(websocket, path):
        gps_thread = AGPS3mechanism()
        gps_thread.stream_data()
        gps_thread.run_thread()

        global use_virb

        if use_virb:
            ip = search_virb("Garmin-WiFi")
            print("Virb ip: " + ip)
            cam = Virb((ip, 80))

        while True:
            try:
                # speed in knots, convert to km/h
                speed = round(float(gps_thread.data_stream.speed)*3.6, 1)
                speed = '{:.1f}'.format(speed)
            except:
                print("GPS speed failed, trying Garmin Virb")
                speed = round(cam.get_speed()*3.6, 1)
                speed = '{:.1f}'.format(speed)

            try:
                await websocket.send(speed)
            except:
                await websocket.send("0")

            await asyncio.sleep(1)

    try:
        start_server = websockets.serve(gps, "127.0.0.1", 5678)
    except:
        print("unable to start server")
        pass

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    run_dash_server()
