cmake_minimum_required(VERSION 3.8)
project(gesture_behavior)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(gesture_msgs REQUIRED)

add_executable(gesture_behavior_node src/behavior_node.cpp)
# Link only the C++ typesupport target of each message package. Neither
# ament_target_dependencies nor ${<pkg>_TARGETS} works here: both pull in the
# package's rosidl_generator_py library, which a standalone C++ node must not
# load (it needs libpython and aborts at startup on macOS with a flat-namespace
# _PyExc_RuntimeError). The __rosidl_typesupport_cpp target brings the C++
# typesupport and nothing Python.
target_link_libraries(gesture_behavior_node
  rclcpp::rclcpp
  geometry_msgs::geometry_msgs__rosidl_typesupport_cpp
  gesture_msgs::gesture_msgs__rosidl_typesupport_cpp
)

# Drop dylibs whose symbols we never use from the load commands. Message
# packages transitively list their rosidl_generator_py libraries, which would
# otherwise load at startup and abort (they need libpython). The real
# typesupport is dlopen'd by the middleware at runtime, so stripping is safe;
# this matches how the prebuilt RoboStack binaries are linked.
if(APPLE)
  target_link_options(gesture_behavior_node PRIVATE -Wl,-dead_strip_dylibs)
endif()

install(TARGETS gesture_behavior_node
  DESTINATION lib/${PROJECT_NAME})

install(DIRECTORY config
  DESTINATION share/${PROJECT_NAME})

ament_package()
