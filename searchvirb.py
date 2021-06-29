from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import QtCore, QtGui

import time
import subprocess
import nmap3
from netifaces import interfaces, ifaddresses, AF_INET

def search_virb():
    def is_virb_ssid():
        ssid = subprocess.check_output(['sudo', 'iwgetid']).decode("utf-8").split('"')[1]
        if ssid == "VIRB-6267":
            return True

        return False

    virb_ip = ""

    if is_virb_ssid():
        return "192.168.0.1"

    print("Searching Garmin Virb")
    for ifaceName in interfaces():
        addresses = [i['addr'] for i in ifaddresses(ifaceName).setdefault(AF_INET, [{'addr':'No IP addr'}] )]
        if ifaceName == "wlan0":
            my_ip = addresses[0].split('.')
            break

    my_ip[3] = "0/24"
    ip = "."
    ip = ip.join(my_ip)
    nmap = nmap3.NmapHostDiscovery()
    result=nmap.nmap_no_portscan(ip, "-sP")

    for i in range(len(result)):
        try:
            device = result[list(result.keys())[i]]['hostname'][0]['name']
            if device == "Garmin-WiFi":
                virb_ip = list(result)[i]
                print("Virb found: " + virb_ip)
                break
        except:
            pass

    return virb_ip

class SearchVirb(QObject):
    start_signal = pyqtSignal()
    finished = pyqtSignal()
    exit_signal = pyqtSignal()
    ip = pyqtSignal(str)

    def __init__(self, parent=None):
        QObject.__init__(self, parent=parent)
        self.running = True

    def run(self):
        virb_ip = ""
        while self.running and not virb_ip:
            virb_ip = search_virb()
            if virb_ip:
                print("Virb ip: " + virb_ip)
                self.ip.emit(virb_ip)
                self.running = False
                continue
            time.sleep(10)

    def stop(self):
        print("searchvirb: Received exit signal")
        self.running = False
