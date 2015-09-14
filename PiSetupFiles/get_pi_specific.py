#!/usr/bin/env python

import subprocess
import re
import sys


data={"30:b5:c2:15:d9:59" : {"adhocnet" : "rpi-adhoc-222", "adhocnetbssid" : "A0:AA:AA:AA:AA:AA", "adhocnetchannel":1},
    "c4:6e:1f:10:d2:d7" : {"adhocnet" : "rpi-adhoc-206", "adhocnetbssid" : "A1:AA:AA:AA:AA:AA", "adhocnetchannel":2},
    "e8:de:27:08:a1:f8" : {"adhocnet" : "rpi-adhoc-209", "adhocnetbssid" : "A2:AA:AA:AA:AA:AA", "adhocnetchannel":3}, 
    "c4:6e:1f:1a:79:70" : {"adhocnet" : "rpi-adhoc-203", "adhocnetbssid" : "A3:AA:AA:AA:AA:AA", "adhocnetchannel":4}, 
    "e8:de:27:08:92:ad" : {"adhocnet" : "rpi-adhoc-201", "adhocnetbssid" : "A4:AA:AA:AA:AA:AA", "adhocnetchannel":5},
    "c4:6e:1f:12:e5:70" : {"adhocnet" : "rpi-adhoc-202", "adhocnetbssid" : "AA:AA:AA:AA:AA:A5", "adhocnetchannel":6}, 
    "30:b5:c2:18:af:d2" : {"adhocnet" : "rpi-adhoc-220", "adhocnetbssid" : "A6:AA:AA:AA:AA:AA", "adhocnetchannel":7}, 
    "e8:de:27:17:e9:a5" : {"adhocnet" : "rpi-adhoc-207", "adhocnetbssid" : "BA:AA:AA:AA:AA:AA", "adhocnetchannel":8}, 
    "e8:de:27:13:0e:63" : {"adhocnet" : "rpi-adhoc-205", "adhocnetbssid" : "A8:AA:AA:AA:AA:AA", "adhocnetchannel":9}, 
    "e8:de:27:12:cb:a1" : {"adhocnet" : "rpi-adhoc-200", "adhocnetbssid" : "A9:AA:AA:AA:AA:AA", "adhocnetchannel":10} 
     }


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
