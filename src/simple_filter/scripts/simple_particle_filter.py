#!/usr/bin/env python

""" TODO: * have multiple sensations.
          * add multiple walls and do a multi-modal density
          * add the ability to move the robot around
"""


import matplotlib.pyplot as plt
import numpy as np
import rospy
from numpy.random import randn, random_sample
from scipy.stats import norm
import time
from copy import deepcopy
from simple_filter.msg import LaserSimple, OdometrySimple

n_particles = 20

class SimpleParticleFilter(object):
    def __init__(self):
        walls = [0.0, 0.5, 1.0]

        self.world_model = WorldModel(walls)
        sensor_model = SensorModel(model_noise_rate=0.05,
                                   odom_noise_rate=0.05,
                                   world_model=self.world_model)

        self.fig = plt.figure()
        self.fig.show()
        self.pf = ParticleFilter()

        for i in range(n_particles):
            self.pf.add_particle(Particle(position=randn()*0.4+0.5,
                                          weight=1/float(n_particles),
                                          sensor_model=sensor_model))
        draw_map(self.fig, self.pf, self.world_model)
        self.last_scan = None
        self.last_odom = None
        rospy.init_node('simple_particle_filter')
        rospy.Subscriber('/simple_scan', LaserSimple, self.process_scan)
        rospy.Subscriber('/simple_odom', OdometrySimple, self.process_odom)
        rospy.Subscriber('/true_pos')

    def process_scan(self, msg):
        self.last_scan = msg

    def process_odom(self, msg):
        if (self.last_odom != None  and
            msg.west_to_east_position != self.last_odom.west_to_east_position):
            delta = msg.west_to_east_position - self.last_odom.west_to_east_position
            self.pf.predict(delta)
            # do an update
        self.last_odom = msg

    def run(self):
        r = rospy.Rate(10)
        while not rospy.is_shutdown():
            if self.last_scan != None:
                self.pf.integrate_observation(self.last_scan)
                self.last_scan = None
            self.pf.normalize()
            self.pf.resample()
            draw_map(self.fig, self.pf, self.world_model)
            r.sleep()

class ParticleFilter(object):
    def __init__(self):
        self.particles = []

    def add_particle(self, p):
        self.particles.append(p)

    def normalize(self):
        w_sum = sum([p.weight for p in self.particles])
        [p.normalize_weight(w_sum) for p in self.particles]

    def integrate_observation(self, observation):
        for p in self.particles:
            p.integrate_observation(observation)

    def predict(self, delta):
        for p in self.particles:
            p.predict(delta)

    @staticmethod
    def weighted_values(values, probabilities, size):
        """ Return a random sample of size elements from the set values with the specified probabilities
            values: the values to sample from (numpy.ndarray)
            probabilities: the probability of selecting each element in values (numpy.ndarray)
            size: the number of samples
        """
        bins = np.add.accumulate(probabilities)
        indices = np.digitize(random_sample(size), bins)
        sample = []
        for ind in indices:
            sample.append(deepcopy(values[ind]))
        return sample

    def resample(self):
        self.particles = ParticleFilter.weighted_values(self.particles,
                                                        [p.weight for p in self.particles],
                                                        len(self.particles))
        for p in self.particles:
            p.weight = 1./len(self.particles)

class SensorModel(object):
    def __init__(self, model_noise_rate, odom_noise_rate, world_model):
        self.model_noise_rate = model_noise_rate
        self.odom_noise_rate = odom_noise_rate
        self.world_model = world_model

    def get_likelihood(self, observation, position, direction):
        closest = self.world_model.get_closest_obstacle(position, direction)
        if closest == None and observation == 0.0:
            return 1.0
        if closest == None or observation == 0.0:
            # no chance of missing a reading or of generating a false reading
            return 0.0
        return norm(0, self.model_noise_rate).pdf(abs(position - closest) - observation)

    def sample_prediction(self, predicted_position):
        """ Sample a potential next state based on a predicted position
            based off of the Odometry """
        return predicted_position + randn()*self.odom_noise_rate

class WorldModel(object):
    def __init__(self, walls=None):
        if walls == None:
            self.walls = []
        else:
            self.walls = walls

    def add_wall(self, wall_position):
        self.walls.append(wall_position)

    def get_closest_obstacle(self, position, direction):
        if direction == -1:
            positions = [(position - w, idx) for idx, w in enumerate(self.walls) if position - w >= 0]
            if len(positions) == 0:
                return None
            min_idx = np.argmin([p[0] for p in positions])
            return self.walls[positions[min_idx][1]]
        else:
            positions = [(w - position, idx) for idx, w in enumerate(self.walls) if w - position >= 0]
            if len(positions) == 0:
                return None
            min_idx = np.argmin([p[0] for p in positions])
            return self.walls[positions[min_idx][1]]

class Particle(object):
    def __init__(self, position, weight, sensor_model):
        self.position = position
        self.weight = weight
        self.sensor_model = sensor_model

    def integrate_observation(self, observation):
        self.weight *= self.sensor_model.get_likelihood(observation.west_laser, self.position, -1)
        self.weight *= self.sensor_model.get_likelihood(observation.east_laser, self.position, 1)

    def predict(self, delta):
        """ Update the predicted position based on an odometry reading
            TODO: currently we are not supporting 2d, just 1d """
        self.position  = self.sensor_model.sample_prediction(self.position+delta)

    def normalize_weight(self, Z):
        self.weight /= Z

def draw_map(fig, pf, world_model):
    fig.clf()
    t = time.time()
    subplot = fig.add_subplot(2,1,1)
    for w in world_model.walls:
        subplot.plot([w,w],[0,1],'b-')
        subplot.hold(True)
    subplot.set_xlim([-0.2,1.2])
    subplot.set_ylim([0,1])
    subplot.scatter([p.position for p in pf.particles],
                    [0.5]*len(pf.particles),
                    c='r',
                    s=[p.weight*1000 for p in pf.particles])

    subplot.scatter([p.position for p in pf.particles],
                    [0.2]*len(pf.particles),
                    c='k',
                    s=[100]*len(pf.particles))

    histogram = fig.add_subplot(2,1,2)

    histogram.hist([p.position for p in pf.particles],
                   weights=[p.weight for p in pf.particles],
                   bins=np.arange(-0.5,1.5,.01))

    histogram.set_xlim([-.2,1.2])
    histogram.set_ylim([0,1])
    plt.draw()

if __name__ == '__main__':
    node = SimpleParticleFilter()
    node.run()