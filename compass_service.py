#!/usr/bin/env python3

# WS server that sends dasboard data

import asyncio
import datetime
import random
import websockets
import time
import math

from gps3.agps3threaded import AGPS3mechanism

def run_compass_server():
    async def gps(websocket, path):
        gps_thread = AGPS3mechanism()
        gps_thread.stream_data()
        gps_thread.run_thread()

        while True:
            try:
                course = round(gps_thread.data_stream.track)
                course = '{:d}'.format(track)
            except:
                pass

            try:
                await websocket.send(course)
            except:
                await websocket.send("0")

            await asyncio.sleep(0.2)

    try:
        start_server = websockets.serve(gps, "127.0.0.1", 5679)
    except:
        print("unable to start server")
        pass

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    run_compass_server()
