#!/usr/bin/python
# Example using a character LCD plate.
import math
import time
import subprocess
from os import system, path

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
VIDEO_MODE_HEADER = 4
SELECT_VIDEO_MODE = 5
VIDEO_MODE_RECONFIGURE = 6

VIDEO_MODES = ["320x240 MJPG", "640x480 MJPG", "1024x768 MJPG", "320x240 H264", "640x480 H264", "1024x768 H264"]

MANAGED_MODE = 0
ADHOC_MODE = 1

state = DISPLAY_STATE

# Initialize the LCD using the pins 
lcd = LCD.Adafruit_CharLCDPlate()

lcd.set_backlight(True)
import time

old_backlight = -1

print 'Press Ctrl-C to quit.'
while True:
	clock = int(time.time())%2 == 0
	lcd.set_backlight(clock or
			  path.exists('/dev/ttyUSB0') or
			  path.exists('/dev/ttyUSB1'))
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
			linkquality = int(linkquality[linkquality.find('=')+1:linkquality.find('/')]) - 1
		my_message(lcd, ssid + " " + str(linkquality) + "\n" + ip_address)
	elif state == SELECT_NETWORK_MODE_STATE:
		if network_mode == MANAGED_MODE:
			my_message(lcd,"* OLIN-ROBOTICS\n  AD-HOC")
		else:
			my_message(lcd,"  OLIN-ROBOTICS\n* AD-HOC")
	elif state == SELECT_VIDEO_MODE:
		my_message(lcd,"* " + VIDEO_MODES[video_mode] + "\n  " + VIDEO_MODES[(video_mode+1)%len(VIDEO_MODES)] + "\n")
	elif state == POWER_DOWN_PROMPT_STATE:
		my_message(lcd,"Press select to\nShutdown")
	elif state == VIDEO_MODE_RECONFIGURE:
		my_message(lcd,"Reconfiguring video\nmode...")
		system("sudo killall raspivid")
		system("sudo killall mjpg_streamer")
		system("sudo killall video_wrapper.sh")
		system("sudo killall gst-launch-1.0")
		if VIDEO_MODES[video_mode] == "320x240 MJPG":
			system('sudo ~pi/start_jpg_stream.sh "-ex sports -y 240 -x 320 -fps 10 -mm matrix -rot 180" &')
		elif VIDEO_MODES[video_mode] == "640x480 MJPG":
			system('sudo ~pi/start_jpg_stream.sh "-ex sports -y 480 -x 640 -fps 10 -mm matrix -rot 180" &')
		elif VIDEO_MODES[video_mode] == "1024x768 MJPG":
			system('sudo ~pi/start_jpg_stream.sh "-ex sports -y 768 -x 1024 -fps 10 -mm matrix -rot 180" &')
		elif VIDEO_MODES[video_mode] == "320x240 H264":
			system('sudo ~pi/video_wrapper.sh "-ex sports -h 240 -w 320 -fps 10 -mm matrix" &')
		elif VIDEO_MODES[video_mode] == "640x480 H264":
			system('sudo ~pi/video_wrapper.sh "-ex sports -h 480 -w 640 -fps 10 -mm matrix" &')
		elif VIDEO_MODES[video_mode] == "1024x768 H264":
			system('sudo ~pi/video_wrapper.sh "-ex sports -h 768 -w 1024 -fps 10 -mm matrix" &')
		state = DISPLAY_STATE
	elif state == NETWORK_RECONFIGURE_STATE:
		my_message(lcd,"Reconfiguring\nnetwork...")
		if network_mode == ADHOC_MODE:
			proc = subprocess.Popen(["~pi/start_adhoc.sh"], stdout=subprocess.PIPE, shell=True)
			(out, err) = proc.communicate()		
		else:
			proc = subprocess.Popen(["~pi/start_managed.sh"], stdout=subprocess.PIPE, shell=True)
			(out, err) = proc.communicate()
		# need to do this in order to update with new IP address (if gstreamer is running)
		print("this does not properly support UDP gstreamer")
		system("sudo killall gst-launch-1.0")
		state = DISPLAY_STATE
	elif state == VIDEO_MODE_HEADER:
		my_message(lcd,"Video Mode Menu")

	if lcd.is_pressed(LCD.RIGHT) and state == VIDEO_MODE_HEADER:
		state = SELECT_VIDEO_MODE
		video_mode = 0
	elif lcd.is_pressed(LCD.DOWN) and state == SELECT_VIDEO_MODE:
		video_mode = (video_mode + 1)% len(VIDEO_MODES)
	elif lcd.is_pressed(LCD.UP) and state == SELECT_VIDEO_MODE:
		video_mode = (video_mode - 1)% len(video_modes)
	elif lcd.is_pressed(LCD.LEFT) and state == SELECT_VIDEO_MODE:
		state = VIDEO_MODE_HEADER
	elif lcd.is_pressed(LCD.RIGHT) and state == SELECT_VIDEO_MODE:
		state = VIDEO_MODE_RECONFIGURE
	elif lcd.is_pressed(LCD.RIGHT) and state == DISPLAY_STATE:
		state = SELECT_NETWORK_MODE_STATE
		network_mode = MANAGED_MODE
	elif lcd.is_pressed(LCD.DOWN) and state == DISPLAY_STATE:
		state = VIDEO_MODE_HEADER
	elif lcd.is_pressed(LCD.DOWN) and state == VIDEO_MODE_HEADER:
		state = POWER_DOWN_PROMPT_STATE
	elif lcd.is_pressed(LCD.DOWN) and state == POWER_DOWN_PROMPT_STATE:
		state = DISPLAY_STATE
	elif lcd.is_pressed(LCD.UP) and state == DISPLAY_STATE:
		state = POWER_DOWN_PROMPT_STATE
	elif lcd.is_pressed(LCD.UP) and state == VIDEO_MODE_HEADER:
		state = DISPLAY_STATE
	elif lcd.is_pressed(LCD.UP) and state == POWER_DOWN_PROMPT_STATE:
		state = VIDEO_MODE_HEADER
	elif (lcd.is_pressed(LCD.DOWN) or lcd.is_pressed(LCD.UP)) and state == SELECT_NETWORK_MODE_STATE:
		if network_mode == MANAGED_MODE:
			network_mode = ADHOC_MODE
		else:
			network_mode = MANAGED_MODE
	elif lcd.is_pressed(LCD.LEFT) and state == SELECT_NETWORK_MODE_STATE:
		state = DISPLAY_STATE
	elif (lcd.is_pressed(LCD.RIGHT) or lcd.is_pressed(LCD.SELECT)) and state == SELECT_NETWORK_MODE_STATE:
		state = NETWORK_RECONFIGURE_STATE
	elif (lcd.is_pressed(LCD.SELECT) or lcd.is_pressed(LCD.RIGHT)) and state == POWER_DOWN_PROMPT_STATE:
		lcd.set_backlight(False)
		lcd.clear()
		system("sudo pkill -HUP -f hybrid_serial_redirect.py")
		system("shutdown -h now")
	time.sleep(.05)
