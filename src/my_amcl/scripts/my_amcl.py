#!/usr/bin/env python

import rospy

from std_msgs.msg import Header, String
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import PoseStamped, PoseArray, Pose, Point, Quaternion
from tf import TransformListener
from tf import TransformBroadcaster
from tf.transformations import euler_from_quaternion, rotation_matrix, quaternion_from_matrix
import tf
from random import gauss
import numpy as np
from nav_msgs.srv import GetMap
from numpy.random import random_sample
import math
import time
from sklearn.neighbors import NearestNeighbors

class Particle:
	def __init__(self,x=0.0,y=0.0,theta=0.0,w=1.0):
		self.w = w
		self.theta = theta
		self.x = x
		self.y = y

	def as_pose(self):
		orientation_tuple = tf.transformations.quaternion_from_euler(0,0,self.theta)
		return Pose(position=Point(x=self.x,y=self.y,z=0), orientation=Quaternion(x=orientation_tuple[0], y=orientation_tuple[1], z=orientation_tuple[2], w=orientation_tuple[3]))

class MyAMCL:
	def __init__(self):
		self.initialized = False
		rospy.init_node('my_amcl')
		print "MY AMCL initialized"
		# todo make this static
		self.n_particles = 100
		self.alpha1 = 0.2
		self.alpha2 = 0.2
		self.alpha3 = 0.2
		self.alpha4 = 0.2

		self.d_thresh = 0.2
		self.a_thresh = math.pi/6

		self.z_hit = 0.5
		self.z_rand = 0.5
		self.sigma_hit = 0.2

		self.laser_max_distance = 2.0

		self.laser_subscriber = rospy.Subscriber("scan", LaserScan, self.scan_received);
		self.tf_listener = TransformListener()
		self.tf_broadcaster = TransformBroadcaster()
		self.particle_pub = rospy.Publisher("particlecloud", PoseArray)
		self.particle_cloud = []
		self.last_transform_valid = False
		self.particle_cloud_initialized = False
		self.current_odom_xy_theta = []

		# request the map
		rospy.wait_for_service("static_map")
		static_map = rospy.ServiceProxy("static_map", GetMap)
		try:
			self.map = static_map().map
		except:
			print "error receiving map"

		self.create_occupancy_field()
		self.initialized = True

	def create_occupancy_field(self):
		X = np.zeros((self.map.info.width*self.map.info.height,2))
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
		t = time.time()
		nbrs = NearestNeighbors(n_neighbors=1,algorithm="ball_tree").fit(O)
		distances, indices = nbrs.kneighbors(X)
		print time.time() -t
		closest_occ = {}
		curr = 0
		for i in range(self.map.info.width):
			for j in range(self.map.info.height):
				ind = i + j*self.map.info.width
				closest_occ[ind] = distances[curr]*self.map.info.resolution
				curr += 1
		# this is a bit adhoc, could probably integrate into an internal map structure
		self.closest_occ = closest_occ

	def update_robot_pose(self):
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
		new_odom_xy_theta = MyAMCL.convert_pose_to_xy_and_theta(self.odom_pose.pose)
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
			delta_rot1 = MyAMCL.angle_diff(math.atan2(delta[1], delta[0]), old_odom_xy_theta[2])

		delta_rot2 = MyAMCL.angle_diff(delta[2], delta_rot1)
    	# We want to treat backward and forward motion symmetrically for the
    	# noise model to be applied below.  The standard model seems to assume
    	# forward motion.
		delta_rot1_noise = min(math.fabs(MyAMCL.angle_diff(delta_rot1,0.0)), math.fabs(MyAMCL.angle_diff(delta_rot1, math.pi)));
		delta_rot2_noise = min(math.fabs(MyAMCL.angle_diff(delta_rot2,0.0)), math.fabs(MyAMCL.angle_diff(delta_rot2, math.pi)));

		for sample in self.particle_cloud:
			# Sample pose differences
			delta_rot1_hat = MyAMCL.angle_diff(delta_rot1, gauss(0, self.alpha1*delta_rot1_noise*delta_rot1_noise + self.alpha2*delta_trans*delta_trans))
			delta_trans_hat = delta_trans - gauss(0, self.alpha3*delta_trans*delta_trans + self.alpha4*delta_rot1_noise*delta_rot1_noise + self.alpha4*delta_rot2_noise*delta_rot2_noise)
			delta_rot2_hat = MyAMCL.angle_diff(delta_rot2, gauss(0, self.alpha1*delta_rot2_noise*delta_rot2_noise + self.alpha2*delta_trans*delta_trans))

			# Apply sampled update to particle pose
			sample.x += delta_trans_hat * math.cos(sample.theta + delta_rot1_hat)
			sample.y += delta_trans_hat * math.sin(sample.theta + delta_rot1_hat)
			sample.theta += delta_rot1_hat + delta_rot2_hat

	def get_map_index(self,x,y):
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
		return ind

	def map_calc_range(self,x,y,theta):
		''' this is for a beam model... this is pretty damn slow...'''
		(x_curr,y_curr) = (x,y)
		ind = self.get_map_index(x_curr, y_curr)

		while not(math.isnan(ind)):
			if self.map.data[ind] > 0:
				return math.sqrt((x - x_curr)**2 + (y - y_curr)**2)

			x_curr += self.map.info.resolution*0.5*math.cos(theta)
			y_curr += self.map.info.resolution*0.5*math.sin(theta)
			ind = self.get_map_index(x_curr, y_curr)

		if math.isnan(ind):
			return float('nan')
		else:
			return self.map.info.range_max

	def resample_particles(self):
		self.normalize_particles()
		values = np.empty(self.n_particles)
		probs = np.empty(self.n_particles)
		for i in range(len(self.particle_cloud)):
			values[i] = i
			probs[i] = self.particle_cloud[i].w

		new_particle_indices = MyAMCL.weighted_values(values,probs,self.n_particles)
		new_particles = []
		for i in new_particle_indices:
			idx = int(i)
			s_p = self.particle_cloud[idx]
			new_particles.append(Particle(x=s_p.x+gauss(0,.025),y=s_p.y+gauss(0,.025),theta=s_p.theta+gauss(0,.025)))

		self.particle_cloud = new_particles
		self.normalize_particles()

	def update_particles_with_laser(self, msg):
		laser_xy_theta = MyAMCL.convert_pose_to_xy_and_theta(self.laser_pose.pose)
		for p in self.particle_cloud:
			adjusted_pose = (p.x+laser_xy_theta[0], p.y+laser_xy_theta[1], p.theta+laser_xy_theta[2])
			# Pre-compute a couple of things
			z_hit_denom = 2*self.sigma_hit**2
			z_rand_mult = 1.0/msg.range_max

			# This assumes quite a bit about the weights beforehand (TODO: could base this on p.w)
			new_prob = 1.0
			for i in range(5,len(msg.ranges),10):
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
				ind = self.get_map_index(end_x,end_y)
				if math.isnan(ind):
					z = self.laser_max_distance
				else:
					z = self.closest_occ[ind]

				pz += self.z_hit * math.exp(-(z * z) / z_hit_denom)
				pz += self.z_rand * z_rand_mult

				new_prob += pz**3
			p.w = new_prob

	@staticmethod
	def normalize(z):
		return math.atan2(math.sin(z), math.cos(z))

	@staticmethod
	def angle_diff(a, b):
		a = MyAMCL.normalize(a)
		b = MyAMCL.normalize(b)
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
		bins = np.add.accumulate(probabilities)
		return values[np.digitize(random_sample(size), bins)]

	@staticmethod
	def convert_pose_to_xy_and_theta(pose):
		orientation_tuple = (pose.orientation.x, pose.orientation.y, pose.orientation.z, pose.orientation.w)
		angles = euler_from_quaternion(orientation_tuple)
		return (pose.position.x, pose.position.y, angles[2])

	def initialize_particle_cloud(self):
		self.particle_cloud_initialized = True
		(x,y,theta) = MyAMCL.convert_pose_to_xy_and_theta(self.odom_pose.pose)

		for i in range(self.n_particles):
			self.particle_cloud.append(Particle(x=x+gauss(0,.25),y=y+gauss(0,.25),theta=theta+gauss(0,.25)))
		self.normalize_particles()

	def normalize_particles(self):
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
		self.particle_pub.publish(PoseArray(header=Header(stamp=rospy.Time.now(),frame_id="map"),poses=particles_conv))

	def scan_received(self, msg):
		if not(self.initialized):
			return

		if not(self.tf_listener.canTransform("base_footprint",msg.header.frame_id,msg.header.stamp)):
			return

		if not(self.tf_listener.canTransform("base_footprint","odom",msg.header.stamp)):
			return

		p = PoseStamped(header=Header(stamp=rospy.Time(0),frame_id=msg.header.frame_id))
		self.laser_pose = self.tf_listener.transformPose("base_footprint",p)

		p = PoseStamped(header=Header(stamp=msg.header.stamp,frame_id="base_footprint"), pose=Pose())
		#p = PoseStamped(header=Header(stamp=msg.header.stamp,frame_id="base_footprint"), pose=Pose(position=Point(x=0.0,y=0.0,z=0.0),orientation=Quaternion(x=0.0,y=0.0,z=0.0,w=0.0)))
		self.odom_pose = self.tf_listener.transformPose("odom", p)
		new_odom_xy_theta = MyAMCL.convert_pose_to_xy_and_theta(self.odom_pose.pose)

		if not(self.particle_cloud_initialized):
			self.initialize_particle_cloud()
			self.update_robot_pose()
			self.current_odom_xy_theta = new_odom_xy_theta
			self.fix_map_to_odom_transform(msg)
		else:
			delta = (new_odom_xy_theta[0] - self.current_odom_xy_theta[0], new_odom_xy_theta[1] - self.current_odom_xy_theta[1], new_odom_xy_theta[2] - self.current_odom_xy_theta[2])
			if math.fabs(delta[0]) > self.d_thresh or math.fabs(delta[1]) > self.d_thresh or math.fabs(delta[2]) > self.a_thresh:
				self.update_particles_with_odom(msg)
				self.update_robot_pose()
				self.update_particles_with_laser(msg)
				self.resample_particles()
				self.update_robot_pose()
				self.fix_map_to_odom_transform(msg)
			else:
				self.fix_map_to_odom_transform(msg, False)

		self.publish_particles(msg)

	def fix_map_to_odom_transform(self, msg, recompute_odom_to_map=True):
		if recompute_odom_to_map:
			(translation, rotation) = MyAMCL.convert_pose_inverse_transform(self.robot_pose)
			p = PoseStamped(pose=MyAMCL.convert_translation_rotation_to_pose(translation,rotation),header=Header(stamp=msg.header.stamp,frame_id="base_footprint"))
			self.odom_to_map = self.tf_listener.transformPose("odom", p)
		(translation, rotation) = MyAMCL.convert_pose_inverse_transform(self.odom_to_map.pose)
		self.tf_broadcaster.sendTransform(translation, rotation, msg.header.stamp+rospy.Duration(1.0), "odom", "map")

	@staticmethod
	def convert_translation_rotation_to_pose(translation,rotation):
		return Pose(position=Point(x=translation[0],y=translation[1],z=translation[2]), orientation=Quaternion(x=rotation[0],y=rotation[1],z=rotation[2],w=rotation[3]))

	@staticmethod
	def convert_pose_inverse_transform(pose):
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

if __name__ == '__main__':
	n = MyAMCL()
	r = rospy.Rate(10)

	while not(rospy.is_shutdown()):
		r.sleep()
