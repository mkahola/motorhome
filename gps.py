"""
GPS daemon thread
"""
import websockets
import asyncio
import json

from PyQt5.QtCore import pyqtSignal, QObject

class Location(QObject):
    """ location class """
    finished = pyqtSignal()
    exit_signal = pyqtSignal()

    gpsLocation = pyqtSignal(tuple)
    gpsFix = pyqtSignal(int)

    def __init__(self, parent=None):
        QObject.__init__(self, parent=parent)
        self.running = True
        self.uri = "ws://localhost:5678"
    def run(self):
        """ Run gps sensor data receiver """

        async def gps():
            async with websockets.connect(self.uri) as websocket:
                mode, mode_prev = 0, 0
                while self.running:
                    data = await websocket.recv()
                    data = json.loads(data)
                    if data['id'] == "gps":
                        mode = data['mode']
                        # emit GPS fix if changed
                        if mode != mode_prev:
                            self.gpsFix.emit(mode)
                            mode_prev = mode
                        if mode > 1:
                            location = (data['lat'], data['lon'], data['alt'], data['speed'], data['course'], data['src'])
                            self.gpsLocation.emit(location)

        asyncio.run(gps())

        print("GPS thread: thread finished")
        self.finished.emit()

    def stop(self):
        """Stop running the gps thread"""
        print("GPS thread: received exit signal")
        self.running = False
