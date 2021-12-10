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

        if data['id'] == "ruuvi":
            try:
                self.temperature.emit(data['temperature'])
                self.humidity.emit(data['humidity'])
                self.pressure.emit(data['pressure'])
                self.ruuvi_batt.emit(data['battery'])
            except KeyError:
                print("failed to send ruuvitag data to gui due to key error")
        elif data['id'] == "tpms":
            try:
                self.tpms_warn.emit(data['tire']['warn'])
                tire = (data['tire']['position'], data['tire']['pressure'], data['tire']['temperature'], data['tire']['warn'])
                self.tpms.emit(tire)
            except KeyError:
                print("failed to send tpms data to gui due to key error")
        elif data['id'] == "gps":
            self.gpsFix.emit(data['mode'])
            location = (data['lat'], data['lon'], data['alt'], data['speed'], data['course'], data['src'])
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
