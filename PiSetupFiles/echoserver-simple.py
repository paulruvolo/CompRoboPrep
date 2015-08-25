#!/usr/bin/env python

"""
A simple echo server
"""

import subprocess
import re
import socket
from os import system
from time import sleep
host = ''
port = 10003
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
    source_port = None
    system(cmd)
    p = subprocess.Popen(['tcpdump','-i','wlan0','udp','port','5000','-v'], stdout=subprocess.PIPE)
    while True:
        line = p.stdout.readline()
	m = re.search('raspberrypi.local.([0-9]+) ',line)
	if m:
            print m.group(1)
            source_port = m.group(1)
            p.kill()
            break
    print source_port
    if source_port:
        client.send(source_port + "\n")
    client.close()
s.close()
