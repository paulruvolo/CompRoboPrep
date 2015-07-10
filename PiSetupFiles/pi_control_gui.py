#!/usr/bin/python
# Example using a character LCD plate.
import math
import time
import subprocess
from os import system

import Adafruit_CharLCD as LCD

last_message = ""

def my_message(lcd, msg):
	global last_message
	if msg == last_message:
		return
	last_message = msg
	lcd.clear()
	lcd.message(msg)


DISPLAY_STATE = 0
SELECT_NETWORK_MODE_STATE = 1
NETWORK_RECONFIGURE_STATE = 2
POWER_DOWN_PROMPT_STATE = 3

MANAGED_MODE = 0
ADHOC_MODE = 1

state = DISPLAY_STATE

# Initialize the LCD using the pins 
lcd = LCD.Adafruit_CharLCDPlate()

lcd.set_backlight(True)

print 'Press Ctrl-C to quit.'
while True:
	if state == DISPLAY_STATE:
		proc = subprocess.Popen(["hostname -I"], stdout=subprocess.PIPE, shell=True)
		(ip_address, err) = proc.communicate()
		ip_address = ip_address.rstrip()
		proc = subprocess.Popen(["iwgetid -r"], stdout=subprocess.PIPE, shell=True)
		(ssid, err) = proc.communicate()
		ssid = ssid.rstrip()
		proc = subprocess.Popen(["iwconfig wlan0 | egrep Quality"],stdout=subprocess.PIPE,shell=True)
		(linkquality, err) = proc.communicate()
		if linkquality.find('=') >=0:
			linkquality = int(linkquality[linkquality.find('=')+1:linkquality.find('/')])
		if linkquality > 65:
			linkquality = 5
		elif linkquality > 58:
			linkquality = 4
		elif linkquality > 50:
			linkquality = 3
		elif linkquality > 44:
			linkquality = 2
		elif linkquality > 38:
			linkquality = 1
		else:
			linkquality = 0
		my_message(lcd, ssid + " S" + str(linkquality) + "\n" + ip_address)
	elif state == SELECT_NETWORK_MODE_STATE:
		if network_mode == MANAGED_MODE:
			my_message(lcd,"* OLIN-ROBOTICS\n  AD-HOC")
		else:
			my_message(lcd,"  OLIN-ROBOTICS\n* AD-HOC")
	elif state == POWER_DOWN_PROMPT_STATE:
		my_message(lcd,"Press select to\nShutdown")
	elif state == NETWORK_RECONFIGURE_STATE:
		my_message(lcd,"Reconfiguring\nnetwork...")
		if network_mode == ADHOC_MODE:
			proc = subprocess.Popen(["~pi/start_adhoc.sh"], stdout=subprocess.PIPE, shell=True)
			(out, err) = proc.communicate()		
		else:
			proc = subprocess.Popen(["~pi/start_managed.sh"], stdout=subprocess.PIPE, shell=True)
			(out, err) = proc.communicate()
		state = DISPLAY_STATE

	if lcd.is_pressed(LCD.RIGHT) and state == DISPLAY_STATE:
		state = SELECT_NETWORK_MODE_STATE
		network_mode = MANAGED_MODE
	elif (lcd.is_pressed(LCD.DOWN) or lcd.is_pressed(LCD.UP)) and state == DISPLAY_STATE:
		state = POWER_DOWN_PROMPT_STATE
	elif (lcd.is_pressed(LCD.DOWN) or lcd.is_pressed(LCD.UP)) and state == SELECT_NETWORK_MODE_STATE:
		if network_mode == MANAGED_MODE:
			network_mode = ADHOC_MODE
		else:
			network_mode = MANAGED_MODE
	elif lcd.is_pressed(LCD.LEFT) and state == SELECT_NETWORK_MODE_STATE:
		state = DISPLAY_STATE
	elif (lcd.is_pressed(LCD.RIGHT) or lcd.is_pressed(LCD.SELECT)) and state == SELECT_NETWORK_MODE_STATE:
		state = NETWORK_RECONFIGURE_STATE
	elif (lcd.is_pressed(LCD.UP) or lcd.is_pressed(LCD.DOWN)) and state == POWER_DOWN_PROMPT_STATE:
		state = DISPLAY_STATE
	elif (lcd.is_pressed(LCD.SELECT) or lcd.is_pressed(LCD.RIGHT)) and state == POWER_DOWN_PROMPT_STATE:
		lcd.set_backlight(False)
		lcd.clear()
		system("shutdown -h now")
	time.sleep(.05)
