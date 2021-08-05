"""
Search Garmin Virb from the network
"""
import time
import subprocess
import nmap3
import configparser
import netifaces
from pathlib import Path

from PyQt5.QtCore import pyqtSignal, QObject

def ping_ok(ip):
    try:
        cmd = "ping -c 1 " + ip
        output = subprocess.check_output(cmd, shell=True)
    except Exception as e:
        return False

    return True

def search_with_nmap():
    virb_ip = ""

    for iface_name in netifaces.interfaces():
        addresses = [i['addr'] for i in netifaces.ifaddresses(iface_name).setdefault(netifaces.AF_INET, [{'addr':'No IP addr'}])]
        if iface_name == "wlan0":
            my_ip = addresses[0].split('.')
            break

    my_ip[3] = "0/24"
    ip_addr = "."
    ip_addr = ip_addr.join(my_ip)
    nmap = nmap3.NmapHostDiscovery()
    result = nmap.nmap_no_portscan(ip_addr, "-sP")

    for i in range(len(result)):
        try:
           device = result[list(result.keys())[i]]['hostname'][0]['name']
           if device == "Garmin-WiFi":
                virb_ip = list(result)[i]
                break
        except IndexError:
            pass
        except KeyError:
            pass

    return virb_ip

def search_virb():
    conf_file = str(Path.home()) + "/.motorhome/network.conf"
    config = configparser.ConfigParser()
    config.read(conf_file)

    ssid = subprocess.check_output(['sudo', 'iwgetid']).decode("utf-8").split('"')[1]

    try:
        virb_ip = config[ssid]['ip']
    except Exception as e:
        virb_ip = ""

    if ping_ok(virb_ip):
        print("searchvirb: ping to " + virb_ip + " ok")
        return virb_ip
    else:
        print("searchvirb: Searching Garmin Virb with nmap")
        virb_ip = search_with_nmap()
        if not virb_ip:
            data = config[ssid]
            data['ip'] = virb_ip

            with open(conf_file, 'w') as configfile:
                config.write(configfile)

    return virb_ip

class SearchVirb(QObject):
    """ Search Garmin Virb from the network and return it's IP address """
    start_signal = pyqtSignal()
    finished = pyqtSignal()
    exit_signal = pyqtSignal()
    ip = pyqtSignal(str)

    def __init__(self, parent=None):
        QObject.__init__(self, parent=parent)
        self.running = True

    def run(self):
        """ run for the Garmin Virb"""
        virb_ip = ""
        while self.running and not virb_ip:
            virb_ip = search_virb()
            if virb_ip:
                print("Virb found: " + virb_ip)
                self.ip.emit(virb_ip)
                self.running = False
                continue
            time.sleep(10)

        self.finished.emit()

    def stop(self):
        """ Stop searching Garmin Virb """
        print("searchvirb: Received exit signal")
        self.running = False
