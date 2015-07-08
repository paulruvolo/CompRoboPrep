#!/bin/bash

# TODO: need to possible restart video if using gstreamer

sudo service ifplugd stop
sleep 2
sudo killall udhcpd
sudo ifdown wlan0
sleep 2
sudo iwconfig wlan0 key off
sudo iwconfig wlan0 power off
sudo iwconfig wlan0 mode ad-hoc
sudo ifup -i /etc/network/interfaces_adhoc wlan0
sudo iwconfig wlan0 key off
sudo udhcpd /etc/udhcpd.conf 
sudo service ifplugd start 
