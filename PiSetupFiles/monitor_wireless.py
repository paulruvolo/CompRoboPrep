#!/usr/bin/env python

import commands
import time
import re

preauthed = {}
last_restart = time.time()

while True:
	print "checking system log"
	output = commands.getstatusoutput('iwconfig | grep "Signal level"')
	print output[1]
	lines = output[1].split('\n')
	for l in lines:
		macs = re.findall('Signal level=([0-9]*)',l)
		if len(macs):
			print macs[0]
			if  int(macs[0]) < 50 and time.time() - last_restart > 60:
				output = commands.getstatusoutput('service networking restart')
				last_restart = time.time()
				print 'restarting'
	time.sleep(5)
