#!/bin/sh -e

(sudo killall raspivid || true)
(sudo killall video_wrapper.sh || true)
sudo ~pi/video_wrapper.sh "$1" &
