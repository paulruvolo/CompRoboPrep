#!/usr/bin/env python

import rospy

from std_msgs.msg import Header, String
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped, PoseArray, Pose, Point, Quaternion
from nav_msgs.srv import GetMap

import tf
from tf import TransformListener
from tf import TransformBroadcaster
from tf.transformations import euler_from_quaternion, rotation_matrix, quaternion_from_matrix
from random import gauss

import math
import time

import numpy as np
from numpy.random import random_sample
from sklearn.neighbors import NearestNeighbors

class TransformHelpers:
	""" Some convenience functions for translating between various represenations of a robot pose """
	@staticmethod
	def convert_translation_rotation_to_pose(translation, rotation):
		""" Convert from representation of a pose as translation and rotation (Quaternion) tuples to a ROS Pose message """
		return Pose(position=Point(x=translation[0],y=translation[1],z=translation[2]), orientation=Quaternion(x=rotation[0],y=rotation[1],z=rotation[2],w=rotation[3]))

	@staticmethod
	def convert_pose_inverse_transform(pose):
		""" Helper method to invert a transform (this is built in to C++ classes, but ommitted from Python) """
		translation = np.zeros((4,1))
		translation[0] = -pose.position.x
		translation[1] = -pose.position.y
		translation[2] = -pose.position.z
		translation[3] = 1.0

		rotation = (pose.orientation.x, pose.orientation.y, pose.orientation.z, pose.orientation.w)
		euler_angle = euler_from_quaternion(rotation)
		rotation = np.transpose(rotation_matrix(euler_angle[2], [0,0,1]))		# the angle is a yaw
		transformed_translation = rotation.dot(translation)

		translation = (transformed_translation[0], transformed_translation[1], transformed_translation[2])
		rotation = quaternion_from_matrix(rotation)
		return (translation, rotation)

	@staticmethod
	def convert_pose_to_xy_and_theta(pose):
		orientation_tuple = (pose.orientation.x, pose.orientation.y, pose.orientation.z, pose.orientation.w)
		angles = euler_from_quaternion(orientation_tuple)
		return (pose.position.x, pose.position.y, angles[2])

class Particle:
	""" Represents a hypothesis (particle) of the robot's pose consisting of x,y and theta (yaw)
		Attributes:
			x: the x-coordinate of the hypothesis relative to the map frame
			y: the y-coordinate of the hypothesis relative ot the map frame
			theta: the yaw of the hypothesis relative to the map frame
			w: the particle weight (the class does not ensure that particle weights are normalized
	"""

	def __init__(self,x=0.0,y=0.0,theta=0.0,w=1.0):
		""" Construct a new Particle
			x: the x-coordinate of the hypothesis relative to the map frame
			y: the y-coordinate of the hypothesis relative ot the map frame
			theta: the yaw of the hypothesis relative to the map frame
			w: the particle weight (the class does not ensure that particle weights are normalized """ 
		self.w = w
		self.theta = theta
		self.x = x
		self.y = y

	def as_pose(self):
		""" A helper function to convert a particle to a ROS Pose message """
		orientation_tuple = tf.transformations.quaternion_from_euler(0,0,self.theta)
		return Pose(position=Point(x=self.x,y=self.y,z=0), orientation=Quaternion(x=orientation_tuple[0], y=orientation_tuple[1], z=orientation_tuple[2], w=orientation_tuple[3]))

	# TODO: define additional helper functions if needed

""" Difficulty Level 2 """
class OccupancyField:
	""" Stores an occupancy field for an input map.  An occupancy field returns the distance to the closest
		obstacle for any coordinate in the map
		Attributes:
			map: TODO
			closest_occ: TODO
	"""

	def __init__(self, map):
		self.map = map		# save this for later
		# build up a numpy array of the coordinates of each grid cell in the map
		X = np.zeros((self.map.info.width*self.map.info.height,2))

		# while we're at it let's count the number of occupied cells
		total_occupied = 0
		curr = 0
		for i in range(self.map.info.width):
			for j in range(self.map.info.height):
				# occupancy grids are stored in row major order, if you go through this right, you might be able to use curr
				ind = i + j*self.map.info.width
				if self.map.data[ind] > 0:
					total_occupied += 1
				X[curr,0] = float(i)
				X[curr,1] = float(j)
				curr += 1

		# build up a numpy array of the coordinates of each occupied grid cell in the map
		O = np.zeros((total_occupied,2))
		curr = 0
		for i in range(self.map.info.width):
			for j in range(self.map.info.height):
				# occupancy grids are stored in row major order, if you go through this right, you might be able to use curr
				ind = i + j*self.map.info.width
				if self.map.data[ind] > 0:
					O[curr,0] = float(i)
					O[curr,1] = float(j)
					curr += 1

		# use super fast scikit learn nearest neighbor algorithm
		nbrs = NearestNeighbors(n_neighbors=1,algorithm="ball_tree").fit(O)
		distances, indices = nbrs.kneighbors(X)

		self.closest_occ = {}
		curr = 0
		for i in range(self.map.info.width):
			for j in range(self.map.info.height):
				ind = i + j*self.map.info.width
				self.closest_occ[ind] = distances[curr]*self.map.info.resolution
				curr += 1

	def get_closest_obstacle_distance(self,x,y):
		""" Compute the closest obstacle to the specified (x,y) coordinate in the map.  If the (x,y) coordinate
			is out of the map boundaries, nan will be returned. """
		x_coord = int((x - self.map.info.origin.position.x)/self.map.info.resolution)
		y_coord = int((y - self.map.info.origin.position.y)/self.map.info.resolution)

		# check if we are in bounds
		if x_coord > self.map.info.width or x_coord < 0:
			return float('nan')
		if y_coord > self.map.info.height or y_coord < 0:
			return float('nan')

		ind = x_coord + y_coord*self.map.info.width
		if ind >= self.map.info.width*self.map.info.height or ind < 0:
			return float('nan')
		return self.closest_occ[ind]

class ParticleFilter:
	""" The class that represents a Particle Filter ROS Node
		Attributes list:
			initialized: a Boolean flag to communicate to other class methods that initializaiton is complete
			base_frame: the name of the robot base coordinate frame (should be "base_link" for most robots)
			map_frame: the name of the map coordinate frame (should be "map" in most cases)
			odom_frame: the name of the odometry coordinate frame (should be "odom" in most cases)
			scan_topic: the name of the scan topic to listen to (should be "scan" in most cases)
			n_particles: the number of particles in the filter
			d_thresh: the amount of linear movement before triggering a filter update
			a_thresh: the amount of angular movement before triggering a filter update
			laser_max_distance: the maximum distance to an obstacle we should use in a likelihood calculation
			pose_listener: a subscriber that listens for new approximate pose estimates (i.e. generated through the rviz GUI)
			particle_pub: a publisher for the particle cloud
			laser_subscriber: listens for new scan data on topic self.scan_topic
			tf_listener: listener for coordinate transforms
			tf_broadcaster: broadcaster for coordinate transforms
			particle_cloud: a list of particles representing a probability distribution over robot poses
			current_odom_xy_theta: the pose of the robot in the odometry frame when the last filter update was performed.
								   The pose is expressed as a list [x,y,theta] (where theta is the yaw)
			map: the map we will be localizing ourselves in.  The map should be of type nav_msgs/OccupancyGrid
	"""
	def __init__(self):
		self.initialized = False		# make sure we don't perform updates before everything is setup
		rospy.init_node('pf')			# tell roscore that we are creating a new node named "pf"

		self.base_frame = "base_link"	# the frame of the robot base
		self.map_frame = "map"			# the name of the map coordinate frame
		self.odom_frame = "odom"		# the name of the odometry coordinate frame
		self.scan_topic = "scan"		# the topic where we will get laser scans from 

		self.n_particles = 300			# the number of particles to use

		self.d_thresh = 0.2				# the amount of linear movement before performing an update
		self.a_thresh = math.pi/6		# the amount of angular movement before performing an update

		self.laser_max_distance = 2.0	# maximum penalty to assess in the likelihood field model

		# TODO: define additional constants if needed

		#### DELETE BEFORE POSTING
		self.alpha1 = 0.2
		self.alpha2 = 0.2
		self.alpha3 = 0.2
		self.alpha4 = 0.2
		self.z_hit = 0.5
		self.z_rand = 0.5
		self.sigma_hit = 0.1
		##### DELETE BEFORE POSTING

		# Setup pubs and subs

		# pose_listener responds to selection of a new approximate robot location (for instance using rviz)
		self.pose_listener = rospy.Subscriber("initialpose", PoseWithCovarianceStamped, self.update_initial_pose)
		# publish the current particle cloud.  This enables viewing particles in rviz.
		self.particle_pub = rospy.Publisher("particlecloud", PoseArray)

		# laser_subscriber listens for data from the lidar
		self.laser_subscriber = rospy.Subscriber(self.scan_topic, LaserScan, self.scan_received)

		# enable listening for and broadcasting coordinate transforms
		self.tf_listener = TransformListener()
		self.tf_broadcaster = TransformBroadcaster()

		self.particle_cloud = []

		self.current_odom_xy_theta = []

		# request the map
		# Difficulty level 2

		rospy.wait_for_service("static_map")
		static_map = rospy.ServiceProxy("static_map", GetMap)
		try:
			map = static_map().map
		except:
			print "error receiving map"

		self.occupancy_field = OccupancyField(map)
		self.initialized = True

	def update_robot_pose(self):
		""" Update the estimate of the robot's pose given the updated particles.
			There are two logical methods for this:
				(1): compute the mean pose
				(2): compute the most likely pose (i.e. the mode of the distribution)
		"""
		""" Difficulty level 2 """
		# first make sure that the particle weights are normalized
		self.normalize_particles()
		use_mean = True
		if use_mean:
			mean_x = 0.0
			mean_y = 0.0
			mean_theta = 0.0
			theta_list = []
			weighted_orientation_vec = np.zeros((2,1))
			for p in self.particle_cloud:
				mean_x += p.x*p.w
				mean_y += p.y*p.w
				weighted_orientation_vec[0] += p.w*math.cos(p.theta)
				weighted_orientation_vec[1] += p.w*math.sin(p.theta)
			mean_theta = math.atan2(weighted_orientation_vec[1],weighted_orientation_vec[0])
			self.robot_pose = Particle(x=mean_x,y=mean_y,theta=mean_theta).as_pose()
		else:
			weights = []
			for p in self.particle_cloud:
				weights.append(p.w)
			best_particle = np.argmax(weights)
			self.robot_pose = self.particle_cloud[best_particle].as_pose()

	def update_particles_with_odom(self, msg):
		""" Implement a simple version of this (Level 1) or a more complex one (Level 2) """
		new_odom_xy_theta = TransformHelpers.convert_pose_to_xy_and_theta(self.odom_pose.pose)
		if self.current_odom_xy_theta:
			old_odom_xy_theta = self.current_odom_xy_theta
			delta = (new_odom_xy_theta[0] - self.current_odom_xy_theta[0], new_odom_xy_theta[1] - self.current_odom_xy_theta[1], new_odom_xy_theta[2] - self.current_odom_xy_theta[2])
			self.current_odom_xy_theta = new_odom_xy_theta
		else:
			self.current_odom_xy_theta = new_odom_xy_theta
			return
		# Implement sample_motion_odometry (Prob Rob p 136)
		# Avoid computing a bearing from two poses that are extremely near each
		# other (happens on in-place rotation).
		delta_trans = math.sqrt(delta[0]*delta[0] + delta[1]*delta[1])
		if delta_trans < 0.01:
			delta_rot1 = 0.0
		else:
			delta_rot1 = ParticleFilter.angle_diff(math.atan2(delta[1], delta[0]), old_odom_xy_theta[2])

		delta_rot2 = ParticleFilter.angle_diff(delta[2], delta_rot1)
    	# We want to treat backward and forward motion symmetrically for the
    	# noise model to be applied below.  The standard model seems to assume
    	# forward motion.
		delta_rot1_noise = min(math.fabs(ParticleFilter.angle_diff(delta_rot1, 0.0)), math.fabs(ParticleFilter.angle_diff(delta_rot1, math.pi)));
		delta_rot2_noise = min(math.fabs(ParticleFilter.angle_diff(delta_rot2, 0.0)), math.fabs(ParticleFilter.angle_diff(delta_rot2, math.pi)));

		for sample in self.particle_cloud:
			# Sample pose differences
			delta_rot1_hat = ParticleFilter.angle_diff(delta_rot1, gauss(0, self.alpha1*delta_rot1_noise*delta_rot1_noise + self.alpha2*delta_trans*delta_trans))
			delta_trans_hat = delta_trans - gauss(0, self.alpha3*delta_trans*delta_trans + self.alpha4*delta_rot1_noise*delta_rot1_noise + self.alpha4*delta_rot2_noise*delta_rot2_noise)
			delta_rot2_hat = ParticleFilter.angle_diff(delta_rot2, gauss(0, self.alpha1*delta_rot2_noise*delta_rot2_noise + self.alpha2*delta_trans*delta_trans))

			# Apply sampled update to particle pose
			sample.x += delta_trans_hat * math.cos(sample.theta + delta_rot1_hat)
			sample.y += delta_trans_hat * math.sin(sample.theta + delta_rot1_hat)
			sample.theta += delta_rot1_hat + delta_rot2_hat

	def map_calc_range(self,x,y,theta):
		""" Difficulty Level 3: implement a ray tracing likelihood model... Let me know if you are interested """
		pass

	def resample_particles(self):
		self.normalize_particles()
		values = np.empty(self.n_particles)
		probs = np.empty(self.n_particles)
		for i in range(len(self.particle_cloud)):
			values[i] = i
			probs[i] = self.particle_cloud[i].w

		new_particle_indices = ParticleFilter.weighted_values(values,probs,self.n_particles)
		new_particles = []
		for i in new_particle_indices:
			idx = int(i)
			s_p = self.particle_cloud[idx]
			new_particles.append(Particle(x=s_p.x+gauss(0,.025),y=s_p.y+gauss(0,.025),theta=s_p.theta+gauss(0,.025)))

		self.particle_cloud = new_particles
		self.normalize_particles()

	# Difficulty level 1
	def update_particles_with_laser(self, msg):
		""" Updates the particle weights in response to the scan contained in the msg """
		laser_xy_theta = TransformHelpers.convert_pose_to_xy_and_theta(self.laser_pose.pose)
		for p in self.particle_cloud:
			adjusted_pose = (p.x+laser_xy_theta[0], p.y+laser_xy_theta[1], p.theta+laser_xy_theta[2])
			# Pre-compute a couple of things
			z_hit_denom = 2*self.sigma_hit**2
			z_rand_mult = 1.0/msg.range_max

			# This assumes quite a bit about the weights beforehand (TODO: could base this on p.w)
			new_prob = 1.0	# more agressive DEBUG, was 1.0
			for i in range(0,len(msg.ranges),6):
				pz = 1.0

				obs_range = msg.ranges[i]
				obs_bearing = i*msg.angle_increment+msg.angle_min

				if math.isnan(obs_range):
					continue

				if obs_range >= msg.range_max:
					continue

				# compute the endpoint of the laser
				end_x = p.x + obs_range*math.cos(p.theta+obs_bearing)
				end_y = p.y + obs_range*math.sin(p.theta+obs_bearing)
				z = self.occupancy_field.get_closest_obstacle_distance(end_x,end_y)
				if math.isnan(z):
					z = self.laser_max_distance
				else:
					z = z[0]	# not sure why this is happening

				pz += self.z_hit * math.exp(-(z * z) / z_hit_denom) / (math.sqrt(2*math.pi)*self.sigma_hit)
				pz += self.z_rand * z_rand_mult

				new_prob += pz**3
			p.w = new_prob
		pass

	@staticmethod
	def angle_normalize(z):
		""" convenience function to map an angle to the range [-pi,pi] """
		return math.atan2(math.sin(z), math.cos(z))

	@staticmethod
	def angle_diff(a, b):
		""" Calculates the difference between angle a and angle b (both should be in radians)
			the difference is always based on the closest rotation from angle a to angle b
			examples:
				angle_diff(.1,.2) -> -.1
				angle_diff(.1, 2*math.pi - .1) -> .2
				angle_diff(.1, .2+2*math.pi) -> -.1
		"""
		a = ParticleFilter.angle_normalize(a)
		b = ParticleFilter.angle_normalize(b)
		d1 = a-b
		d2 = 2*math.pi - math.fabs(d1)
		if d1 > 0:
			d2 *= -1.0
		if math.fabs(d1) < math.fabs(d2):
			return d1
		else:
			return d2

	@staticmethod
	def weighted_values(values, probabilities, size):
		""" Return a random sample of size elements form the set values with the specified probabilities
			values: the values to sample from (numpy.ndarray)
			probabilities: the probability of selecting each element in values (numpy.ndarray)
			size: the number of samples
		"""
		bins = np.add.accumulate(probabilities)
		return values[np.digitize(random_sample(size), bins)]

	def update_initial_pose(self, msg):
		""" Callback function to handle re-initializing the particle filter based on a pose estimate.
			These pose estimates could be generated by another ROS Node or could come from the rviz GUI """
		xy_theta = TransformHelpers.convert_pose_to_xy_and_theta(msg.pose.pose)
		self.initialize_particle_cloud(xy_theta)
		self.fix_map_to_odom_transform(msg)

	def initialize_particle_cloud(self, xy_theta=None):
		""" Initialize the particle cloud.
			Arguments
			xy_theta: a triple consisting of the mean x, y, and theta (yaw) to initialize the
					  particle cloud around.  If this input is ommitted, the odometry will be used """
		if xy_theta == None:
			xy_theta = TransformHelpers.convert_pose_to_xy_and_theta(self.odom_pose.pose)
		self.particle_cloud = []
		for i in range(self.n_particles):
			self.particle_cloud.append(Particle(x=xy_theta[0]+gauss(0,.25),y=xy_theta[1]+gauss(0,.25),theta=xy_theta[2]+gauss(0,.25)))
		self.normalize_particles()
		self.update_robot_pose()

	""" Level 1 """
	def normalize_particles(self):
		""" Make sure the particle weights define a valid distribution (i.e. sum to 1.0) """
		z = 0.0
		for p in self.particle_cloud:
			z += p.w
		for i in range(len(self.particle_cloud)):
			self.particle_cloud[i].w /= z

	def publish_particles(self, msg):
		particles_conv = []
		for p in self.particle_cloud:
			particles_conv.append(p.as_pose())
		# actually send the message so that we can view it in rviz
		self.particle_pub.publish(PoseArray(header=Header(stamp=rospy.Time.now(),frame_id=self.map_frame),poses=particles_conv))

	def scan_received(self, msg):
		""" This is the default logic for what to do when processing scan data.  Feel free to modify this, however,
			I hope it will provide a good guide.  The input msg is an object of type sensor_msgs/LaserScan """
		if not(self.initialized):
			# wait for initialization to complete
			return

		if not(self.tf_listener.canTransform(self.base_frame,msg.header.frame_id,msg.header.stamp)):
			# need to know how to transform the laser to the base frame
			# this will be given by either Gazebo or neato_node
			return

		if not(self.tf_listener.canTransform(self.base_frame,self.odom_frame,msg.header.stamp)):
			# need to know how to transform between base and odometric frames
			# this will eventually be published by either Gazebo or neato_node
			return

		# calculate pose of laser relative ot the robot base
		p = PoseStamped(header=Header(stamp=rospy.Time(0),frame_id=msg.header.frame_id))
		self.laser_pose = self.tf_listener.transformPose(self.base_frame,p)

		# find out where the robot thinks it is based on its odometry
		p = PoseStamped(header=Header(stamp=msg.header.stamp,frame_id=self.base_frame), pose=Pose())
		self.odom_pose = self.tf_listener.transformPose(self.odom_frame, p)
		# store the the odometry pose in a more convenient format (x,y,theta)
		new_odom_xy_theta = TransformHelpers.convert_pose_to_xy_and_theta(self.odom_pose.pose)

		if not(self.particle_cloud):
			# now that we have all of the necessary transforms we can update the particle cloud
			self.initialize_particle_cloud()
			# cache the last odometric pose so we can only update our particle filter if we move more than self.d_thresh or self.a_thresh
			self.current_odom_xy_theta = new_odom_xy_theta
			# update our map to odom transform now that the particles are initialized
			self.fix_map_to_odom_transform(msg)
		elif (math.fabs(new_odom_xy_theta[0] - self.current_odom_xy_theta[0]) > self.d_thresh or
			  math.fabs(new_odom_xy_theta[1] - self.current_odom_xy_theta[1]) > self.d_thresh or
			  math.fabs(new_odom_xy_theta[2] - self.current_odom_xy_theta[2]) > self.a_thresh):
			# we have moved far enough to do an update!
			self.update_particles_with_odom(msg)	# update based on odometry
			self.update_particles_with_laser(msg)	# update based on laser scan
			self.resample_particles()				# resample particles to focus on areas of high density
			self.update_robot_pose()				# update robot's pose
			self.fix_map_to_odom_transform(msg)		# update map to odom transform now that we have new particles
		# publish particles (so things like rviz can see them)
		self.publish_particles(msg)

	def fix_map_to_odom_transform(self, msg):
		""" Super tricky code to properly update map to odom transform... do not modify this... Difficulty level infinity. """
		(translation, rotation) = TransformHelpers.convert_pose_inverse_transform(self.robot_pose)
		p = PoseStamped(pose=TransformHelpers.convert_translation_rotation_to_pose(translation,rotation),header=Header(stamp=msg.header.stamp,frame_id=self.base_frame))
		self.odom_to_map = self.tf_listener.transformPose(self.odom_frame, p)
		(self.translation, self.rotation) = TransformHelpers.convert_pose_inverse_transform(self.odom_to_map.pose)

	def broadcast_last_transform(self):
		""" Make sure that we are always broadcasting the last map to odom transformation.
			This is necessary so things like move_base can work properly. """
		if not(hasattr(self,'translation') and hasattr(self,'rotation')):
			return
		self.tf_broadcaster.sendTransform(self.translation, self.rotation, rospy.get_rostime(), self.odom_frame, self.map_frame)

if __name__ == '__main__':
	n = ParticleFilter()
	r = rospy.Rate(5)

	while not(rospy.is_shutdown()):
		n.broadcast_last_transform()
		r.sleep()