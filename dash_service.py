#!/usr/bin/env python3

# WS server that sends dasboard data

import asyncio
import datetime
import random
import websockets
import subprocess
import configparser
from pathlib import Path

from virb import Virb

def run_dash_server():
    async def gps(websocket, path):
        ssid = subprocess.check_output(['sudo', 'iwgetid']).decode("utf-8").split('"')[1]
        conf_file = str(Path.home()) + "/.motorhome/network.conf"
        config = configparser.ConfigParser()
        config.read(conf_file)

        try:
            ip = config[ssid]['ip']
        except:
            print("no ip found, using default")
            ip = "192.168.0.1"
            pass
        print("Virb ip: " + ip)

        cam = Virb((ip, 80))

        while True:
            speed = '{:.0f}'.format(cam.get_speed())
            try:
                await websocket.send(speed)
            except:
                print("unable to send speed data")
                return
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
