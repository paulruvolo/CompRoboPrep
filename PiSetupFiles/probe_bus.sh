#!/bin/bash

echo $1
echo `udevadm info --name=$1 --attribute-walk | sed -n 's/\s*ATTRS{\(\(devnum\)\|\(busnum\)\)}==\"\([^\"]\+\)\"/\1\ \4/p' | head -n 2 | awk '{$1 = sprintf("%s:%03d", $1, $2); print $1;}'`
