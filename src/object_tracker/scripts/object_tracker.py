#!/usr/bin/env python

import rospy
import cv2
import rospkg
import math
import numpy as np
import random
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError

class ObjectTracker:

	def image_callback(self,msg):
		try:
			cv_image = self.bridge.imgmsg_to_cv2(msg,'bgr8')
		except CvBridgeError, e:
			print e
		if self.last_image == None:
			self.last_image = cv_image
			self.last_image_time = msg.header.stamp
		else:
			if msg.header.stamp - self.last_image_time > rospy.Duration(1.0):
				self.calc_transformation(self.last_image,cv_image)
				self.last_image_time = msg.header.stamp
				self.last_image = cv_image

	def __init__(self):
		rospy.init_node('object_tracker')
		self.descriptor = cv2.SIFT()
		self.matcher = cv2.BFMatcher()
		cv2.namedWindow('matches')
		rospy.Subscriber('camera/image_raw',Image,self.image_callback,queue_size=1)
		self.bridge = CvBridge()
		self.K = np.array([[633.0243407872103, 0.0, 317.5643084248639],
						   [0.0, 633.7013552813832, 245.3053214040046],
						   [0.0, 0.0, 1.0]])
		self.W = np.array([[0.0, -1.0, 0.0],
						   [1.0, 0.0, 0.0],
						   [0.0, 0.0, 1.0]])
		self.last_image = None

	def calc_transformation(self,im1,im2):
		# first convert to grayscale
		im1 = cv2.cvtColor(im1,cv2.COLOR_BGR2GRAY)
		im2 = cv2.cvtColor(im2,cv2.COLOR_BGR2GRAY)
		kp1, des1 = self.descriptor.detectAndCompute(im1,None)
		kp2, des2 = self.descriptor.detectAndCompute(im2,None)

		matches = self.matcher.knnMatch(des1,des2,k=2)

		good_matches = []
		for m,n in matches:
			if m.distance < 0.75*n.distance:
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
		E = self.K.T.dot(F).dot(self.K)
		U, Sigma, V = np.linalg.svd(E)
		R1 = U.dot(self.W).dot(V)
		R2 = U.dot(self.W.T).dot(V)
		cos1 = (np.trace(R1)-1)/2.0
		cos2 = (np.trace(R2)-1)/2.0
		thetas = []
		if -1 <= cos1 <= 1:
			thetas.append(math.acos(cos1))
		if -1 <= cos2 <= 1:
			thetas.append(math.acos(cos2))
		print thetas
		cv2.imshow('matches',im3)
		cv2.waitKey(50)

	def run(self):
		r = rospy.Rate(5)
		while not(rospy.is_shutdown()):
			r.sleep()

if __name__ == '__main__':
	try:
		n = ObjectTracker()
		n.run()
	except rospy.ROSInterruptException: pass
	cv2.destroyAllWindows()