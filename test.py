0#!/usr/bin/env python3

import sys
import socket
import time
import random

def main(argv):
    stairs_done = False

    while True:

        if not stairs_done:
            val = 'Stairs,1'

            clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            clientsocket.connect(('localhost', 5000))
            clientsocket.send(val.encode())

            time.sleep(3)

            val = 'Stairs,0'

            clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            clientsocket.connect(('localhost', 5000))
            clientsocket.send(val.encode())
            stairs_done = True

        time.sleep(3)

        tp = 5.0  + random.randint(-5, 5)/10
        temp = 26 + random.randint(-3, 20)

        val = "FL," + str(tp) + "," + str(temp)
        clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientsocket.connect(('localhost', 5000))
        clientsocket.send(val.encode())

        time.sleep(1)

        tp = 5.0  + random.randint(-5, 5)/10
        temp = 23 + random.randint(-3, 20)

        val = "FR," + str(tp) + "," + str(temp)
        clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientsocket.connect(('localhost', 5000))
        clientsocket.send(val.encode())

        time.sleep(1)

        tp = 5.0  + random.randint(-5, 5)/10
        temp = 32 + random.randint(-3, 20)

        val = "RL," + str(tp) + "," + str(temp)
        clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientsocket.connect(('localhost', 5000))
        clientsocket.send(val.encode())

        time.sleep(1)
        tp = 5.0  + random.randint(-5, 5)/10
        temp = 25 + random.randint(-3, 20)

        val = "RR," + str(tp) + "," + str(temp)
        clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientsocket.connect(('localhost', 5000))
        clientsocket.send(val.encode())

        time.sleep(1)

if __name__ == '__main__':
    main(sys.argv[1:])
