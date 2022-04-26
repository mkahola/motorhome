#!/usr/bin/env python3
"""
TPMS for motorhome infotainment
"""
import paho.mqtt.client as mqtt
import time
import configparser
import json
from pathlib import Path

import bluetooth._bluetooth as bluez

from bluetooth_utils import (toggle_device,
                             enable_le_scan, parse_le_advertising_events,
                             disable_le_scan, raw_packet_to_str)

season = 0

def get_pressure(data):
    """ get tire pressure """

    try:
        p_word1 = int(str(data[36:38]), 16)
    except ValueError:
        p_word1 = 0

    try:
        p_word2 = int(str(data[38:40]), 16) << 8
    except ValueError:
        p_word2 = 0

    try:
        p_word3 = int(str(data[40:42]), 16) << 16
    except ValueError:
        p_word3 = 0

    try:
        p_word4 = int(str(data[42:44]), 16) << 24
    except ValueError:
        p_word4 = 0

    return (p_word4 + p_word3 + p_word2 + p_word1)/100000

def get_temperature(data):
    """ get tire temperature """

    try:
        t_word1 = int(str(data[44:46]), 16)
    except ValueError:
        t_word1 = 0

    try:
        t_word2 = int(str(data[46:48]), 16) << 8
    except ValueError:
        t_word2 = 0

    temp = t_word1 + t_word2

    if temp > 2**15:
        temp = temp - (2**16 + 1)

    return temp/100.0

def get_season(client, userdata, message):
    global season
    season = message.payload.decode("utf-8", "ignore")
    print("season: " + str(season))

def update_season(self, season):
    """ set tire season summer/winter """
    if season:
        self.season = "TPMS_winter"
    else:
        self.season = "TPMS_summer"

    print("TPMS: " + self.season)

class Tire:
    """ Tire class """
    def __init__(self, tire):
        global season
        self.name = tire
        self.timestamp = time.monotonic()
        self.mac = []
        self.tpms_warn = 0

        conf_file = str(Path.home()) + "/.motorhome/motorhome.conf"
        config = configparser.ConfigParser()

        try:
            config.read(conf_file)
            season_str = "TPMS_" + config['Season']['season']
            self.warn_pressure = float(config[season_str]['warn'])

            if season_str == "TPMS_summer":
                season = 0
            else:
                season = 1

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
            elif tire == 'Spear':
                self.mac.append(config['TPMS_summer']['spear'])
                self.mac.append(config['TPMS_winter']['spear'])
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
        #self.update_warn_level(season)

        if pressure > self.warn_pressure:
            return 0

        return 1

    def send_data(self, now, client, data_str):
        global season
        tpms = {'id': 'tpms',
                'tire': {'position': '', 'pressure': '', 'temperature': '', 'warn': 0},
               }

        """ send pressure and temperature data to GUI """
        if (now - self.timestamp) > 1:
            #print("BLE packet: %s %02x %s %d" % (mac, adv_type, data_str, rssi))
            pressure = get_pressure(data_str)

            warn = self.check_pressure(pressure, season)
            if warn != self.tpms_warn:
                self.tpms_warn = warn
                client.publish("/motorhome/tpms_warn", warn)

            tpms['tire']['position'] = self.name
            tpms['tire']['pressure'] = pressure
            tpms['tire']['temperature'] = get_temperature(data_str)
            tpms['tire']['warn'] = self.tpms_warn

            client.publish("/motorhome/tpms", json.dumps(tpms))
            self.timestamp = now

def run_tpms():
    front_left = Tire('FL')
    front_right = Tire('FR')
    rear_left = Tire('RL')
    rear_right = Tire('RR')
    spear = Tire('Spear')

    mqttBroker = 'localhost'
    client = mqtt.Client("TPMS")
    client.connect(mqttBroker)

    client.loop_start()
    client.subscribe("/motorhome/tpms/season")
    client.on_message = get_season

    print("tpms: " + str(season))

    dev_id = 0  # the bluetooth device is hci0
    try:
        toggle_device(dev_id, True)
    except PermissionError:
        print("TPMS: No permission for bluetooth")
        return

    try:
        sock = bluez.hci_open_dev(dev_id)
    except:
        print("Cannot open bluetooth device %i" % dev_id)
        raise

    enable_le_scan(sock, filter_duplicates=True)

    mac_list = []
    for i in range(0, 2):
        mac_list.append(front_left.mac[i])
        mac_list.append(front_right.mac[i])
        mac_list.append(rear_left.mac[i])
        mac_list.append(rear_right.mac[i])
        mac_list.append(spear.mac[i])

    while True:
        def le_advertise_packet_handler(mac, adv_type, data, rssi):
            global season
            data_str = raw_packet_to_str(data)
            pressure = get_pressure(data_str)
            temperature = get_temperature(data_str)

            if mac == front_left.mac[season]:
                front_left.send_data(time.time(), client, data_str)
            elif mac == front_right.mac[season]:
                front_right.send_data(time.time(), client, data_str)
            elif mac == rear_left.mac[season]:
                rear_left.send_data(time.time(), client, data_str)
            elif mac == rear_right.mac[season]:
                rear_right.send_data(time.time(), client, data_str)
            elif mac == spear.mac[season]:
                spear.send_data(time.time(), client, data_str)

        # Blocking call (the given handler will be called each time a new LE
        # advertisement packet is detected)
        parse_le_advertising_events(sock, mac_addr=mac_list,
                                    handler=le_advertise_packet_handler,
                                    debug=False)

if __name__ == "__main__":
    run_tpms()
