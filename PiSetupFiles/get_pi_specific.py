#!/usr/bin/env python

import subprocess
import re
import sys


data={"e8:de:27:13:0e:63" : {"adhocnet" : "rpi-adhoc-205", "adhocnetbssid" : "AA:AA:AA:AA:AA:AA", "adhocnetchannel":5}}


process = subprocess.Popen(["ifconfig","wlan0"],stdout=subprocess.PIPE)
out,err = process.communicate()
m = re.search('HWaddr ([0-9a-f:]*)', out)
mac_addr = m.group(1)

if len(sys.argv) < 2:
	print "USAGE: ./get_pi_specific.py [adhocnet,adhocnetbssid]"
	exit(-1)

if sys.argv[1] != 'adhocnet' and sys.argv[1] != 'adhocnetbssid' and sys.argv[1] != 'adhocnetchannel':
	print "unknown info identifier " + sys.argv[1]
	exit(-1)

print data[mac_addr][sys.argv[1]]
