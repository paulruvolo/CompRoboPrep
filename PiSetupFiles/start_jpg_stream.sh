#!/bin/bash

export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:~pi/mjpg-streamer/mjpg-streamer-experimental
~pi/mjpg-streamer/mjpg-streamer-experimental/mjpg_streamer -o "output_http.so -w ./www -p 11111" -i "input_raspicam.so -ex sports -y 240 -x 320 -fps 30 -mm matrix -rot 180"
