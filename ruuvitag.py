#!/usr/bin/env python3

"""
Ruuvitag sensor data
"""
import os
import configparser
import time
import json
import asyncio
import websockets

from pathlib import Path

from ruuvitag_sensor.ruuvitag import RuuviTag

def get_ruuvitag_mac(conf_file):
    config = configparser.ConfigParser()

    try:
        config.read(conf_file)
        mac = config['RuuviTag']['mac']
    except:
        return

    return mac

def run_ruuvitag(timeout):
    os.environ['RUUVI_BLE_ADAPTER'] = "Bleson"
    mac = get_ruuvitag_mac(str(Path.home()) + "/.motorhome/motorhome.conf")
    sensor = RuuviTag(mac)

    async def ruuvi(websocket, path):
        state = {'id': 'ruuvi',
                 'temperature': 0.0,
                 'humidity': 0.0,
                 'pressure': 0.0,
                 'battery': 0.0,
                }
        while True:
            state = sensor.update()
            state['id'] = 'ruuvi'
            data = json.dumps(state)
            await websocket.send(data)
            await asyncio.sleep(timeout)
    try:
        start_server = websockets.serve(ruuvi, port=5679)
    except:
        print("unable to start server")
        pass

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    run_ruuvitag(15)
