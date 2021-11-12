"""
TPMS for motorhome infotainment
"""
import time
import configparser
from pathlib import Path
from PyQt5.QtCore import pyqtSignal, QObject

import bluetooth._bluetooth as bluez

from bluetooth_utils import (toggle_device,
                             enable_le_scan, parse_le_advertising_events,
                             disable_le_scan, raw_packet_to_str)


def get_pressure(data):
    """ get tire pressure """
    p_word1 = int(str(data[36:38]), 16)
    p_word2 = int(str(data[38:40]), 16) << 8
    p_word3 = int(str(data[40:42]), 16) << 16
    p_word4 = int(str(data[42:44]), 16) << 24

    return (p_word4 + p_word3 + p_word2 + p_word1)/100000

def get_temperature(data):
    """ get tire temperature """
    t_word1 = int(str(data[44:46]), 16)
    t_word2 = int(str(data[46:48]), 16) << 8
    temp = t_word1 + t_word2

    if temp > 2**15:
        temp = temp - (2**16 + 1)

    return temp/100.0

class Tire:
    """ Tire class """
    def __init__(self, tire):
        self.name = tire
        self.timestamp = time.monotonic()
        self.mac = []
        self.tpms_warn = 0

        conf_file = str(Path.home()) + "/.motorhome/motorhome.conf"
        config = configparser.ConfigParser()

        try:
            config.read(conf_file)
            self.season = "TPMS_" + config['Season']['season']
            self.warn_pressure = float(config[self.season]['warn'])

            if tire == 'FL':
                self.mac.append(config['TPMS_summer']['frontLeft'])
                self.mac.append(config['TPMS_winter']['frontLeft'])
            elif tire == 'FR':
                self.mac.append(config['TPMS_summer']['frontRight'])
                self.mac.append(config['TPMS_winter']['frontRight'])
            elif tire == 'RL':
                self.mac.append(config['TPMS_summer']['rearLeft'])
                self.mac.append(config['TPMS_winter']['rearLeft'])
            elif tire == 'RR':
                self.mac.append(config['TPMS_summer']['rearRight'])
                self.mac.append(config['TPMS_winter']['rearRight'])
        except (configparser.Error, IOError, OSError) as __err:
            print("TPMS: unable to read conf file for tire " + tire)
            self.warn_pressure = 0.0

    def set_timestamp(self, timestamp):
        """ set timestamp of last received tpms data """
        self.timestamp = timestamp

    def update_warn_level(self, season):
        """ update TPMS pressure warn level """
        conf_file = str(Path.home()) + "/.motorhome/motorhome.conf"
        config = configparser.ConfigParser()

        try:
            config.read(conf_file)
            self.warn_pressure = float(config[season]['warn'])
        except (configparser.Error, IOError, OSError) as __err:
            self.warn_pressure = 0

    def check_pressure(self, pressure, season):
        """ check pressure agains TPMS warn level """
        self.update_warn_level(season)

        if pressure > self.warn_pressure:
            return 0

        return 1

class TPMS(QObject):
    """ TPMS class """
    start_signal = pyqtSignal()
    finished = pyqtSignal()
    exit_signal = pyqtSignal()
    set_season = pyqtSignal(int)

    tpms = pyqtSignal(tuple)
    tpms_warn = pyqtSignal(int)

    def __init__(self, parent=None):
        QObject.__init__(self, parent=parent)
        self.front_left = Tire('FL')
        self.front_right = Tire('FR')
        self.rear_left = Tire('RL')
        self.rear_right = Tire('RR')
        self.running = True

        conf_file = str(Path.home()) + "/.motorhome/motorhome.conf"
        config = configparser.ConfigParser()

        try:
            config.read(conf_file)
            self.season = "TPMS_" + config['Season']['season']
        except (configparser.Error, IOError, OSError) as __err:
            self.season = "TPMS_summer"

        print("tpms: " + self.season)

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

    def send_pressure_temp(self, tire, now, data_str):
        """ send pressure and temperature data to GUI """
        if (now - tire.timestamp) > 5:
            #print("BLE packet: %s %02x %s %d" % (mac, adv_type, data_str, rssi))
            pressure = get_pressure(data_str)
            temp = get_temperature(data_str)
            warn = tire.check_pressure(pressure, self.season)
            if warn != tire.tpms_warn:
                self.tpms_warn.emit(warn)
                tire.tpms_warn = warn

            data = (tire.name, pressure, temp, warn)
            tire.timestamp = now
            self.tpms.emit(data)

    def get_season(self):
        if self.season == "TPMS_summer":
            return 0
        else:
            return 1

    def run(self):
        """ run TPMS service """
        while self.running:
            def le_advertise_packet_handler(mac, adv_type, data, rssi):
                data_str = raw_packet_to_str(data)
                index = self.get_season()

                if mac == self.front_left.mac[index]:
                    self.send_pressure_temp(self.front_left, time.time(), data_str)
                elif mac == self.front_right.mac[index]:
                    self.send_pressure_temp(self.front_right, time.time(), data_str)
                elif mac == self.rear_left.mac[index]:
                    self.send_pressure_temp(self.rear_left, time.time(), data_str)
                elif mac == self.rear_right.mac[index]:
                    self.send_pressure_temp(self.rear_right, time.time(), data_str)

            # Blocking call (the given handler will be called each time a new LE
            # advertisement packet is detected)
            index = self.get_season()
            mac_list = [self.front_left.mac[index],
                        self.front_right.mac[index],
                        self.rear_left.mac[index],
                        self.rear_right.mac[index]]

            parse_le_advertising_events(self.sock, mac_addr=mac_list,
                                        handler=le_advertise_packet_handler,
                                        debug=False)

        print("TPMS: thread finished")
        self.finished.emit()

    def update_season(self, season):
        """ set tire season summer/winter """
        if season:
            self.season = "TPMS_winter"
        else:
            self.season = "TPMS_summer"

        print("TPMS: " + self.season)

    def stop(self):
        """ Stop TPMS service """
        print("TPMS: received exit signal")
        disable_le_scan(self.sock)
        self.running = False
