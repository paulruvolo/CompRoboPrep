#!/bin/bash
raspivid -n -t 0 -rot 180 -ex sports -awb off -mm matrix -w 640 -h 480 -fps 30 -b 2000000 -o - | gst-launch-1.0 -e -vvvv fdsrc ! h264parse ! rtph264pay pt=96 config-interval=5 !  udpsink host=$1 port=5000
#raspivid -n -t 0 -rot 180 -ex sports -awb off -mm matrix -w 640 -h 480 -fps 30 -b 6000000 -o - | gst-launch-1.0 -e -vvvv fdsrc ! h264parse ! rtph264pay pt=96 config-interval=5 !  udpsink host=$1 port=5000
