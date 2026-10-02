# Gesture firmware v2 (micro-ROS over Wi-Fi), ESP-IDF project.
#
# Build from a terminal OUTSIDE `pixi shell`, so no ROS 2 environment is active:
# the micro_ros_espidf_component builds its own ROS 2 libraries from source and a
# sourced Jazzy env confuses that build (component README advises the same).
#
# The micro-ROS component lives under components/ as a git submodule and is
# auto-discovered by ESP-IDF. The custom Gesture message is synced into the
# component's extra_packages/ by scripts/sync_msgs.sh before the first build.
cmake_minimum_required(VERSION 3.16)

include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(gesture_camera_v2)
