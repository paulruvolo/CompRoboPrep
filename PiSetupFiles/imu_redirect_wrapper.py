#!/usr/bin/env python

from subprocess import call

while True:
	call(['python','/home/pi/imu_redirect.py'])
	print "blah"
