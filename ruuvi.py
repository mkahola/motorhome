"""
Ruuvitag sensor handling
"""
import time
import websockets
import asyncio
import json

from ruuvitag_sensor.ruuvi import RuuviTagSensor, RunFlag
from PyQt5.QtCore import pyqtSignal, QObject

class Ruuvi:
    """ Ruuvitag sensor class """
    def __init__(self):
        self.temperature = float('nan')
        self.humidity = float('nan')
        self.pressure = float('nan')
        self.vbatt = float('nan')

    def set_temperature(self, temp):
        """ set temperature """
        self.temperature = temp

    def set_humidity(self, humidity):
        """ set humidity """
        self.humidity = humidity

    def set_pressure(self, pressure):
        """ set pressure """
        self.pressure = pressure

    def set_vbat(self, vbatt):
        """ set battery voltage """
        self.vbatt = vbatt

class RuuviTag(QObject):
    """ Ruuvitag """
    stop_signal = pyqtSignal()
    start_signal = pyqtSignal()
    finished = pyqtSignal()
    exit_signal = pyqtSignal()

    temperature = pyqtSignal(float)
    humidity = pyqtSignal(float)
    pressure = pyqtSignal(float)
    ruuvi_batt = pyqtSignal(float)

    def __init__(self, mac, parent=None):
        QObject.__init__(self, parent=parent)
        self.mac = mac
        self.uri = "ws://localhost:5679"
        self.running = True

    def run(self):
        async def ruuvi():
            async with websockets.connect(self.uri) as websocket:
                while self.running:
                    data = await websocket.recv()
                    data = json.loads(data)

                    try:
                        self.temperature.emit(data['temperature'])
                        self.humidity.emit(data['humidity'])
                        self.pressure.emit(data['pressure'])
                        self.ruuvi_batt.emit(data['battery'])
                    except KeyError:
                        print("ruuvitag failed due to key error")
        asyncio.run(ruuvi())

        print("thread finished")
        self.finished.emit()

    def stop(self):
        """ stop ruuvitag execution """
        print("ruuvi: received stop signal")
        self.running = False
