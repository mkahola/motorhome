0#!/usr/bin/env python3

import sys
import socket
import time
import random

def check_tp(tp):
    if tp < 2.8:
        return 1
    else:
        return 0

def main(argv):
    stairs_done = False

    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientsocket.connect(('localhost', 5000))

    while True:

        if not stairs_done:
            val = 'Stairs,1'

            clientsocket.send(val.encode())

            time.sleep(10)

            val = 'Stairs,0'

            clientsocket.send(val.encode())
            stairs_done = True

        time.sleep(1)

        tp = 5.0  + random.randint(-5, 5)/10
        temp = 26 + random.randint(-3, 20)
        warn= check_tp(tp)
        val = "FL," + str(tp) + "," + str(temp) + "," + str(warn)
        clientsocket.send(val.encode())

        time.sleep(1)

        tp = 5.0  + random.randint(-5, 5)/10
        temp = 23 + random.randint(-3, 20)
        warn= check_tp(tp)

        val = "FR," + str(tp) + "," + str(temp) + "," + str(warn)

        clientsocket.send(val.encode())

        time.sleep(1)

        tp = 5.0  + random.randint(-5, 5)/10
        temp = 32 + random.randint(-3, 20)
        warn= check_tp(tp)

        val = "RL," + str(tp) + "," + str(temp) + "," + str(warn)
        clientsocket.send(val.encode())

        time.sleep(1)
        tp = 5.0  + random.randint(-5, 5)/10
        temp = 25 + random.randint(-3, 20)
        warn= check_tp(tp)

        val = "RR," + str(tp) + "," + str(temp) + "," + str(warn)
        clientsocket.send(val.encode())

        time.sleep(1)

if __name__ == '__main__':
    main(sys.argv[1:])
