#!/usr/bin/env python3

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

def get_pressure(data):
    p1 = int(data[36:38], 16)
    p2 = int(data[38:40], 16) << 8
    p3 = int(data[40:42], 16) << 16
    p4 = int(data[42:44], 16) << 24

    return (p4 + p3 + p2 + p1)/100000

def get_temperature(data):
    t1 = int(data[44:46], 16)
    t2 = int(data[46:48], 16) << 8
    return (t1 + t2)/100

def send_pressure_temp(tire, now, mac, adv_type, data_str, rssi, clientsocket):
    if (now - tire.ts) > 5:
#        print("BLE packet: %s %02x %s %d" % (mac, adv_type, data_str, rssi))
        pressure = get_pressure(data_str)
        temp = get_temperature(data_str)
        val = tire.name + "," + "{:.1f}".format(pressure) + "," + "{:.0f}".format(temp) + "," + str(tire.check_pressure(pressure))
        print(val)

        try:
            clientsocket.send(val.encode())
            tire.set_timestamp(now)
        except:
            print("unable to send data to server")
            pass

def main():
    fl = Tire('FL')
    fr = Tire('FR')
    rl = Tire('RL')
    rr = Tire('RR')

    print("FL: " + fl.mac)
    print("FR: " + fr.mac)
    print("RL: " + rl.mac)
    print("RR: " + rr.mac)

    connected = False
    while not connected:
        try:
            clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            clientsocket.connect(('localhost', 5000))
            connected = True
        except:
            print("Server not responding")
            connected = False
            time.sleep(1)

    dev_id = 0  # the bluetooth device is hci0
    toggle_device(dev_id, True)

    try:
        sock = bluez.hci_open_dev(dev_id)
    except:
        print("Cannot open bluetooth device %i" % dev_id)
        raise

    enable_le_scan(sock, filter_duplicates=False)

    try:
        def le_advertise_packet_handler(mac, adv_type, data, rssi):
            data_str = raw_packet_to_str(data)
            data_wo_rssi = (mac, data_str)

            if mac == fl.mac:
                send_pressure_temp(fl, time.time(), mac, adv_type, data_str, rssi, clientsocket)
            elif mac == fr.mac:
                send_pressure_temp(fr, time.time(), mac, adv_type, data_str, rssi, clientsocket)
            elif mac == rl.mac:
                send_pressure_temp(rl, time.time(), mac, adv_type, data_str, rssi, clientsocket)
            elif mac == rr.mac:
                send_pressure_temp(rr, time.time(), mac, adv_type, data_str, rssi, clientsocket)

        # Blocking call (the given handler will be called each time a new LE
        # advertisement packet is detected)
        parse_le_advertising_events(sock,
                                    handler=le_advertise_packet_handler,
                                    debug=False)
    except KeyboardInterrupt:
        disable_le_scan(sock)
        clientsocket.close()

if __name__ == "__main__":
    main()
