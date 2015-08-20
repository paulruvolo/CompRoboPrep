#!/bin/bash

VIDEOMODE="-ex sports -awb off -y 480 -x 640 -fps 10 -mm matrix -rot 180"
echo $#
if [ $# = 1 ]; then
	VIDEOMODE=$1
	echo $VIDEOMODE
fi

export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:~pi/mjpg-streamer/mjpg-streamer-experimental
~pi/mjpg-streamer/mjpg-streamer-experimental/mjpg_streamer -o "output_http.so -w ./www -p 11111" -i "input_raspicam.so -quality 20 $VIDEOMODE"
