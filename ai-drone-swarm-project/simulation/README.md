# Simulation Module

## Responsible Member
Member 4

## Purpose
This module is responsible for ROS2/Gazebo simulation and testing.

## Responsibilities
- Create ROS2 workspace and packages.
- Spawn multiple drones in Gazebo.
- Use namespaces such as `/drone1`, `/drone2`, `/drone3`.
- Connect camera/sensor topics to the object detection module.
- Connect detections to communication and LLM modules.

## Suggested ROS2 Topics
- `/drone1/camera/image_raw`
- `/drone1/detections`
- `/drone1/cmd_vel`
- `/drone1/gps/fix`
