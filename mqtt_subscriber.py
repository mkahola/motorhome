"""
MQTT subscriber
"""
import paho.mqtt.client as mqtt
import time
import json
import configparser

from pathlib import Path
from PyQt5.QtCore import pyqtSignal, QObject

class MQTT(QObject):
    """ MQTT subcribers """
    stop_signal = pyqtSignal()
    start_signal = pyqtSignal()
    finished = pyqtSignal()
    exit_signal = pyqtSignal()

    """ Ruuvitag """
    temperature = pyqtSignal(float)
    humidity = pyqtSignal(float)
    pressure = pyqtSignal(float)
    ruuvi_batt = pyqtSignal(float)

    """ TPMS """
    tpms = pyqtSignal(tuple)
    tpms_warn = pyqtSignal(int)

    """ GPS """
    gpsLocation = pyqtSignal(tuple)
    gpsFix = pyqtSignal(int)

    def __init__(self, parent=None):
        QObject.__init__(self, parent=parent)
        self.mqttBroker = 'localhost'
        self.running = True

    def on_message(self, client, userdata, message):
        decoded = str(message.payload.decode("utf-8","ignore"))
        data = json.loads(decoded)

        if data.get('id') == "ruuvi":
            self.temperature.emit(data.get('temperature'))
            self.humidity.emit(data.get('humidity'))
            self.pressure.emit(data.get('pressure'))
            self.ruuvi_batt.emit(data.get('battery'))
        elif data.get('id') == "tpms":
            self.tpms_warn.emit(data.get('tire').get('warn'))
            tire = (data.get('tire').get('position'), data.get('tire').get('pressure'), data.get('tire').get('temperature'), data.get('tire').get('warn'))
            self.tpms.emit(tire)
        elif data.get('id') == "gps":
            self.gpsFix.emit(data.get('mode'))
            location = (data.get('lat'), data.get('lon'), data.get('alt'), data.get('speed'), data.get('course'), data.get('src'))
            self.gpsLocation.emit(location)

    def run(self):
        print("mqtt_subscriber: Thread started")
        self.client = mqtt.Client("RPi")
        self.client.connect(self.mqttBroker)
        self.client.loop_start()
        self.client.subscribe("/motorhome/ruuvitag")
        self.client.subscribe("/motorhome/tpms")
        self.client.subscribe("/motorhome/gps")
        self.client.on_message = self.on_message

        while self.running:
            time.sleep(1)

        self.client.loop_stop()
        print("thread finished")
        self.finished.emit()

    def stop(self):
        """ stop ruuvitag execution """
        print("mqtt_subscriber: received stop signal")
        self.running = False
        self.client.loop_stop()
