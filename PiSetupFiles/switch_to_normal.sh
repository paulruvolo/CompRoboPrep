#!/bin/sh -e

ifdown wlan0
ifup wlan0
killall raspivid
