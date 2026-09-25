cmake_minimum_required(VERSION 3.8)
project(gesture_sim)

find_package(ament_cmake REQUIRED)

install(DIRECTORY urdf config rviz
  DESTINATION share/${PROJECT_NAME})

ament_package()
