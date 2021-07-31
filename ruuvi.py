"""
Ruuvitag sensor handling
"""
import time

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
        self.flag = RunFlag()
        self.running = True

    def run(self):
        """ Collect data from ruuvitag sensor """
        def wait_for_finish(run_flag, name):
            max_time = 20

            while run_flag.running:
                time.sleep(0.1)
                max_time -= 0.1
                if max_time < 0:
                    raise Exception('%s not finished' % name)

        def handle_data(received_data):
            self.flag.running = self.running
            data = received_data[1]
            self.temperature.emit(data['temperature'])
            self.humidity.emit(data['humidity'])
            self.pressure.emit(data['pressure'])
            self.ruuvi_batt.emit(data['battery'])

        RuuviTagSensor.get_datas(handle_data, self.mac, run_flag=self.flag)
        wait_for_finish(self.flag, 'RuuviTagSensor.get_datas')

        print("thread finished")
        self.finished.emit()

    def stop(self):
        """ stop ruuvitag execution """
        print("ruuvi: received stop signal")
        self.running = False
