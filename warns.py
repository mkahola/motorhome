from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import QtWidgets, QtCore, QtGui

import socket
import time
import threading
from threading import Thread

class Warnings(QObject):
    data = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, parent=None):
        QObject.__init__(self, parent=parent)
        self._running = True

    def sensor_handler(self, client):
        client.settimeout(10)
        while self._running:
            try:
                sensor = client.recv(32).decode('utf-8')
                if sensor:
                    self.data.emit(sensor)
            except socket.timeout:
                time.sleep(1)
                pass
        client.close()

    def get_warns(self):
        # create a local socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # bind the socket to the port
        bind_ok = False
        while not bind_ok and self._running:
            try:
                sock.bind(('localhost', 5000))
                bind_ok = True
            except:
                time.sleep(5)
                continue
        # listen for incoming connections
        sock.listen(5)
        print("Server started...")

        sock.settimeout(60)
        while self._running:
            try:
                client, addr = sock.accept()
                threading.Thread(target=self.sensor_handler, args=(client,)).start()
            except socket.timeout:
                print("socket accept timeout")
                time.sleep(1)
                continue

        sock.close()
        self.finished.emit()

    def stop(self):
        print("warns thread: received stop signal")
        self._running = False

