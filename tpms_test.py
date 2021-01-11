#!/usr/bin/env python3

import sys
import socket
import time
import random

def main(argv):
    stairs_done = False

    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientsocket.connect(('localhost', 5000))

    val = argv[0] + "," + argv[1] + "," + argv[2] + "," + argv[3]
    print(val)
    clientsocket.send(val.encode())

    clientsocket.close()

if __name__ == '__main__':
    main(sys.argv[1:])
