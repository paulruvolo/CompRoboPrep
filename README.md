CompRoboPrep
============

This repository is used for course prep for the Olin Computational Introduction to Robotics Class.

Currently contains two packages. One package is a simulated version of the Neato XV-21, this package contains a model of the XV-21, and three example launch files.

amcl_demo.launch: launches the Neato in a playground world with a particle filter and currently a not working path planning app. 

playground.launch: launches the Neato in a playground with no extra features running

SLAM.launch: launches a Neato in a palyground running the gmapping slam package to generate a map

There is an exacutable file within the control file, teleop_twist_keyboard.py, that can be used to control the simulator with the keyboard.

