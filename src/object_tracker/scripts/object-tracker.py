#!/usr/bin/env python

import rospy

class ObjectTracker:
	def __init__(self):
		rospy.init_node('object_tracker')

	def run(self):
		r = rospy.Rate(5)
		while not(rospy.is_shutdown()):
			print "hello"
			r.sleep()

if __name__ == '__main__':
	try:
		n = ObjectTracker()
		n.run()
	except rospy.ROSInterruptException: pass