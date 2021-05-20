from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import QtCore, QtGui

import sys
import socket
import time
import bluetooth._bluetooth as bluez
from bluetooth_utils import (toggle_device,
                             enable_le_scan, parse_le_advertising_events,
                             disable_le_scan, raw_packet_to_str)
import configparser
from pathlib import Path

class Tire:
    def __init__(self, tire):
        conf_file = str(Path.home()) + "/.motorhome/tpms.conf"
        config = configparser.ConfigParser()

        self.name = tire
        self.ts = time.time()

        try:
            config.read(conf_file)
            self.warnPressure = float(config['DEFAULT']['warn'])

            if tire == 'FL':
                self.mac = config['FrontLeft']['bt_addr']
            elif tire == 'FR':
                self.mac = config['FrontRight']['bt_addr']
            elif tire == 'RL':
                self.mac = config['RearLeft']['bt_addr']
            elif tire == 'RR':
                self.mac = config['RearRight']['bt_addr']
        except:
            print("unable to read conf file")
            self.warnPressure = 0.0
            self.mac = '00:00:00:00:00:00'

    def set_timestamp(self, ts):
        self.ts = ts

    def updateWarnLevel(self):
        conf_file = str(Path.home()) + "/.motorhome/tpms.conf"
        config = configparser.ConfigParser()

        try:
            config.read(conf_file)
            self.warnPressure = float(config['DEFAULT']['warn'])
        except:
            self.warnPressure = 0

    def check_pressure(self, pressure):
        self.updateWarnLevel()

        if pressure > self.warnPressure:
            return 0

        return 1

class TPMS(QObject):
    start_signal = pyqtSignal()
    finished = pyqtSignal()
    exit_signal = pyqtSignal()

    tpms = pyqtSignal(tuple)

    def __init__(self, parent=None):
        QObject.__init__(self, parent=parent)
        self.fl = Tire('FL')
        self.fr = Tire('FR')
        self.rl = Tire('RL')
        self.rr = Tire('RR')
        self.running = True

        dev_id = 0  # the bluetooth device is hci0
        try:
            toggle_device(dev_id, True)
        except PermissionError:
            print("No permission for bluetooth")
            self.running = False

        try:
            self.sock = bluez.hci_open_dev(dev_id)
        except:
            print("Cannot open bluetooth device %i" % dev_id)
            raise

        if self.running:
            enable_le_scan(self.sock, filter_duplicates=False)

    def get_pressure(self, data):
        p1 = int(str(data[36:38]), 16)
        p2 = int(str(data[38:40]), 16) << 8
        p3 = int(str(data[40:42]), 16) << 16
        p4 = int(str(data[42:44]), 16) << 24

        return (p4 + p3 + p2 + p1)/100000

    def get_temperature(self, data):
        t1 = int(str(data[44:46]), 16)
        t2 = int(str(data[46:48]), 16) << 8
        temp = t1 + t2

        if temp > 2**15:
            temp = temp - (2**16 + 1)

        return temp/100

    def send_pressure_temp(self, tire, now, mac, adv_type, data_str, rssi):
        if (now - tire.ts) > 5:
            #print("BLE packet: %s %02x %s %d" % (mac, adv_type, data_str, rssi))
            pressure = self.get_pressure(data_str)
            temp = self.get_temperature(data_str)
            data = (tire.name, "{:.1f}".format(pressure), "{:.1f}".format(temp), str(tire.check_pressure(pressure)))
            tire.ts = now
            self.tpms.emit(data)
        return 0

    def run(self):
        while self.running:
            try:
                def le_advertise_packet_handler(mac, adv_type, data, rssi):
                    data_str = raw_packet_to_str(data)
                    data_wo_rssi = (mac, data_str)

                    if mac == self.fl.mac:
                        ret = self.send_pressure_temp(self.fl, time.time(), mac, adv_type, data_str, rssi)
                    elif mac == self.fr.mac:
                        ret = self.send_pressure_temp(self.fr, time.time(), mac, adv_type, data_str, rssi)
                    elif mac == self.rl.mac:
                        ret = self.send_pressure_temp(self.rl, time.time(), mac, adv_type, data_str, rssi)
                    elif mac == self.rr.mac:
                        ret = self.send_pressure_temp(self.rr, time.time(), mac, adv_type, data_str, rssi)

                # Blocking call (the given handler will be called each time a new LE
                # advertisement packet is detected)
                parse_le_advertising_events(self.sock,
                                            handler=le_advertise_packet_handler,
                                            debug=False)
            except:
                print("data unavailable")
                pass

        print("thread finished")
        self.finished.emit()

    def stop(self):
        print("received exit signal")
        disable_le_scan(self.sock)
        self.running = False
