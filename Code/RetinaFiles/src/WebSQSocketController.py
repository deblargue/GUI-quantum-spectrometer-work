#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This script can be used to talk to the SingleQuantum Retina WebSQ.

This script requires Python 3.6.1 or newer and the websockets package installed.
https://pypi.org/project/websockets/

This project is licensed under the terms of the MIT license.
Copyright (c) 2023 Single Quantum B. V. and Hielke Walinga
"""

import asyncio
import signal
import struct
from sys import platform

import websockets


async def websocket_client(base_url, callback, n=0, normalized=False):
    """
    Listens to the Retina websocket and processes every package.
    For each package `callback` is called.
    Give the URL (base_url) for the socket stream
    and the callback that is called everytime a package is received.
    A package contains the information for all the channels in an array.
    If given n, the callback is called around n times.

    Notes
    -----
    The values for BiasI only update when an IV sweep is being done on the channel.
    """
    uri = base_url + "/counts"

    async with websockets.connect(uri) as websocket:
        # Close the connection when receiving SIGTERM.
        if platform == "linux" or platform == "linux2":
            loop = asyncio.get_event_loop()
            loop.add_signal_handler(signal.SIGTERM, lambda: asyncio.ensure_future(websocket.close()))
        # Process messages received on the connection.
        i = 0
        async for message in websocket:
            channel_size = 32  # One channel gives 32 bytes of information.
            payload = []
            for offset in range(0, len(message), channel_size):
                channel = message[offset:(offset + channel_size)]
                inttime = struct.unpack("<I", channel[16:20])[0] * 10  # ms
                payload.append(
                    {
                        "mcuId": struct.unpack("<B", channel[0:1])[0],
                        "cuId": struct.unpack("<B", channel[1:2])[0],
                        "cuStatus": struct.unpack("<B", channel[2:3])[0],
                        "monitorV": struct.unpack("<f", channel[4:8])[0],
                        "biasI": struct.unpack("<f", channel[8:12])[0],
                        "inttime": inttime,
                        "counts": (
                            int(1000 / inttime) * struct.unpack("<I", channel[12:16])[0]
                            if normalized
                            else struct.unpack("<I", channel[12:16])[0]
                        ),
                        "rank": struct.unpack("<I", channel[20:24])[0],
                        "time": struct.unpack("<d", channel[24:])[0],
                    }
                )
            callback(payload)
            i += 1
            if n and i >= n:
                return

def print_counts(payload):
    """
    Prints the recieved messages in a more human readable format.
    """
    for message in payload:
        time, mcuId, cuId, rank = message["time"], message['mcuId'], message['cuId'], message["rank"]
        counts, monitorV, biasI, inttime = message['counts'], message['monitorV'], message['biasI'], message['inttime']
        print(f"""{time} | 
                  {mcuId}.{str(cuId).zfill(2)} ({str(rank).zfill(2)}) | 
                  Counts: {str(counts).rjust(10,' ')} Counts | 
                  monitorV: {str(round(monitorV,6)).rjust(6,' ')} V | 
                  BiasI: {str(biasI).rjust(6,' ')} μA | 
                  intTime: {inttime} ms""")


if __name__ == '__main__':
    # This should be the same URL/IP as the retina interface.
    #url = "192.168.1.1"
    url = "130.237.35.62"
    base_url = f'ws://{url}'
    n = None
    if n is not None:
        print("Get n:" + str(n))
    loop = asyncio.get_event_loop()
    loop.run_until_complete(websocket_client(base_url, print_counts, n=n))
