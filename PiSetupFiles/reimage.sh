#!/bin/bash

if [ $# -ne 1 ]; then
	echo "illegal number of parameters"
fi

echo image_$1
sudo diskutil unmountDisk /dev/disk$1

screen -d -m -S image_$1 sudo dd if=~/Desktop/comprobo_2015_goldmaster_1.0.4.img of=/dev/rdisk$1 bs=1m
