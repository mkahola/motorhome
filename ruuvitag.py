#!/usr/bin/env python3

"""
Ruuvitag sensor data
"""
import os
import configparser
import time
import json
import signal
import paho.mqtt.client as mqtt
from pathlib import Path

from ruuvitag_sensor.ruuvitag import RuuviTag

running = True

# trap ctrl-c, SIGINT and come down nicely
def signal_handler(signal, frame):
    global running

    print("Ruuvitag: terminating.")
    running = False

signal.signal(signal.SIGINT, signal_handler)

def get_ruuvitag_mac(conf_file):
    config = configparser.ConfigParser()

    try:
        config.read(conf_file)
        mac = config['RuuviTag']['mac']
    except:
        return

    return mac

# The callback for when the client receives a CONNACK response from the MQTT server.
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("$SYS/#")

def run_ruuvitag(timeout):
    global running

    mac = get_ruuvitag_mac(str(Path.home()) + "/.motorhome/motorhome.conf")
    sensor = RuuviTag(mac)

    state = {'id': 'ruuvi',
             'location': 'indoor',
             'temperature': None,
             'humidity': None,
             'pressure': None,
             'battery': None,
             }

    mqttBroker = 'localhost'
    client = mqtt.Client("Ruuvitag")
    client.on_connect = on_connect
    client.connect(mqttBroker)

    while running:
        data = sensor.update()
        state['temperature'] = data['temperature']
        state['humidity'] = data['humidity']
        state['pressure'] = data['pressure']
        state['battery'] = data['battery']
        print(state)
        client.publish("/motorhome/ruuvitag", json.dumps(state))
        time.sleep(timeout)

    client.disconnect()

if __name__ == "__main__":
    os.environ['RUUVI_BLE_ADAPTER'] = "Bleson"
    run_ruuvitag(15)
