#!/usr/bin/env python

"""
A simple echo server
"""

import subprocess
import re
import socket
import select
from os import system
from time import sleep, time
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
    send_port = client.recv(1024)
    while not send_port.endswith('\n'):
        data = client.recv(1024)
        send_port += data
    send_port = send_port.strip()
    fields = send_port.split(',')
    if len(fields) == 1:
        send_port = fields[0]
        video_mode = "-ex sports -awb off -mm matrix -w 640 -h 480 -fps 30 -b 2000000"
    else:
        send_port = fields[0]
        video_mode = fields[1]
    cmd  = "~pi/start_gst_udp.sh " + address[0] + ' ' + send_port + ' "' + video_mode + '"&'
    source_port = None
    print system(cmd)
    p = subprocess.Popen(['tcpdump','-i','wlan0','udp','port',send_port,'-v'], stdout=subprocess.PIPE)
    poll_obj = select.poll()
    poll_obj.register(p.stdout, select.POLLIN)  
    start_time = time()
    while time() - start_time < 60:
        print time() - start_time
        poll_result = poll_obj.poll(0)
        if not poll_result:
            sleep(1)
            continue
        line = p.stdout.readline()
	m = re.search('raspberrypi.*.local.([0-9]+) ',line)
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
