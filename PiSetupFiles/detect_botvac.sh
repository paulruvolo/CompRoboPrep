#!/bin/bash

USB=`lsusb | grep 2108:780b`
if [[ ! -z $USB ]]
then
	sudo insmod /lib/modules/3.18.14-v7+/kernel/drivers/usb/serial/usbserial.ko vendor=0x2108 product=0x780B
else
	sudo insmod /lib/modules/3.18.14-v7+/kernel/drivers/usb/serial/usbserial.ko vendor=0x2108 product=0x780C
fi
