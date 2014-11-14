#!/usr/bin/env python

import rospy
import cv2
import rospkg
import numpy as np
import random

class ObjectTracker:
	def __init__(self):
		rospy.init_node('object_tracker')
		rospack = rospkg.RosPack()

		pkg_path = rospack.get_path('object_tracker')
		im1 = cv2.cvtColor(cv2.imread(pkg_path + '/testimages/frame0000.jpg'), cv2.COLOR_BGR2GRAY)
		im2 = cv2.cvtColor(cv2.imread(pkg_path + '/testimages/frame0001.jpg'), cv2.COLOR_BGR2GRAY)

		sift = cv2.SURF()
		kp1, des1 = sift.detectAndCompute(im1,None)
		kp2, des2 = sift.detectAndCompute(im2,None)

		bf = cv2.BFMatcher()
		matches = bf.knnMatch(des1,des2,k=2)

		good_matches = []
		for m,n in matches:
			if m.distance < 0.5*n.distance:
				good_matches.append((m.queryIdx, m.trainIdx))

		im3 = cv2.cvtColor(np.hstack((im1,im2)), cv2.COLOR_GRAY2BGR)
		pts1 = np.zeros((len(good_matches),2))
		pts2 = np.zeros((len(good_matches),2))

		for idx in range(len(good_matches)):
			match = good_matches[idx]
			cv2.line(im3,
					 (int(kp1[match[0]].pt[0]),int(kp1[match[0]].pt[1])),
					 (int(kp2[match[1]].pt[0])+im1.shape[1],int(kp2[match[1]].pt[1])),
					 (random.randint(0,255),random.randint(0,255),random.randint(0,255)))
			pts1[idx,:] = kp1[match[0]].pt
			pts2[idx,:] = kp2[match[1]].pt

		F, mask = cv2.findFundamentalMat(pts1,pts2,cv2.FM_LMEDS)
		print F
		cv2.imshow('matches',im3)
		cv2.waitKey(0)

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
	cv2.destroyAllWindows()