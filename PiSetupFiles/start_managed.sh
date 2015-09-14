#!/bin/bash

sudo killall udhcpd
sudo ifdown wlan0
sudo ifup wlan0
