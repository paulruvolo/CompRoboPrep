#!/usr/bin/env python

"""
A simple echo server
"""

import socket
from os import system
from time import sleep
host = ''
port = 10002
backlog = 5
size = 1024
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((host,port))
s.listen(backlog)

while 1:
    client, address = s.accept()
    print type(address)
    sleep(1)
    system('sudo killall raspivid')
    system('sudo killall gst-launch-1.0')
    system('sudo killall mjpg_streamer')
    cmd  = "~pi/start_gst_udp.sh " + address[0] + ' &'
    system(cmd)
    data = client.recv(size)
    if data:
        client.send(data)
    client.close()
s.close()
