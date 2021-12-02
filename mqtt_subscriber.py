"""
MQTT subscriber
"""
import paho.mqtt.client as mqtt
import time
import json

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
                print("ruuvitag failed due to key error")

    def run(self):
        self.client = mqtt.Client("RPi")
        self.client.connect(self.mqttBroker)
        self.client.loop_start()
        self.client.subscribe("/motorhome/ruuvitag")
        self.client.on_message = self.on_message

        while self.running:
            time.sleep(1)

        print("thread finished")
        self.finished.emit()

    def stop(self):
        """ stop ruuvitag execution """
        print("ruuvi: received stop signal")
        self.running = False
        self.client.loop_stop()
