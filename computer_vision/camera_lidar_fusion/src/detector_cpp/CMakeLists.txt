cmake_minimum_required(VERSION 3.10)
project(detector_cpp)

# C++17, as ROS 2 Jazzy uses. Named explicitly so compile_commands.json carries
# -std=c++17 and IntelliSense doesn't fall back to an older standard.
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(OpenCV REQUIRED COMPONENTS core imgproc imgcodecs dnn)
find_package(onnxruntime REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(vision_msgs REQUIRED)
find_package(cv_bridge REQUIRED)

# Letterbox, decode, IoU and NMS. OpenCV only, so the tests link it without
# ROS or ONNX Runtime.
add_library(yolo src/yolo.cpp)
target_include_directories(yolo PUBLIC include)
target_link_libraries(yolo PUBLIC opencv_core opencv_imgproc)
target_compile_features(yolo PUBLIC cxx_std_17)

# ONNX Runtime session, shared by the node and the reference test.
add_library(onnx_model src/onnx_model.cpp)
target_include_directories(onnx_model PUBLIC include)
target_link_libraries(onnx_model PUBLIC onnxruntime::onnxruntime)
target_compile_features(onnx_model PUBLIC cxx_std_17)

# The ROS node: camera image in, Detection2DArray and an annotated image out.
add_executable(detector_node src/detector_node.cpp)
# Link only the C++ typesupport target of each message package. Neither
# ament_target_dependencies nor ${<pkg>_TARGETS} works on macOS: both pull in
# the package's rosidl_generator_py library, which needs libpython, and a
# standalone C++ node then aborts at startup (same fix as gesture_robot).
target_link_libraries(detector_node
  yolo
  onnx_model
  rclcpp::rclcpp
  cv_bridge::cv_bridge
  sensor_msgs::sensor_msgs__rosidl_typesupport_cpp
  vision_msgs::vision_msgs__rosidl_typesupport_cpp)
# cv_bridge and the message packages still list their Python libraries
# transitively. Drop dylibs whose symbols the node never uses; the middleware
# dlopens the real typesupport at runtime, as in the prebuilt RoboStack nodes.
if(APPLE)
  target_link_options(detector_node PRIVATE -Wl,-dead_strip_dylibs)
endif()

install(TARGETS detector_node DESTINATION lib/${PROJECT_NAME})

if(BUILD_TESTING)
  # Not ament_add_gtest(): it compiles gtest_vendor's 1.14 sources, but the
  # conda compiler puts $CONDA_PREFIX/include ahead of every -isystem, so they
  # see conda-forge's gtest 1.18 headers and fail. Link conda-forge's gtest
  # (an ament_cmake_gtest dependency in RoboStack) and register the tests
  # with ament_add_gtest_test() instead.
  find_package(ament_cmake_gtest REQUIRED)
  find_package(GTest REQUIRED)

  # cv::dnn::blobFromImage cross-checks the CHW layout.
  add_executable(test_yolo test/test_yolo.cpp)
  target_link_libraries(test_yolo yolo opencv_dnn GTest::gtest_main)
  ament_add_gtest_test(test_yolo)

  # The whole pipeline against Ultralytics' predict on real KITTI frames. Skips
  # when the model, the frames or the fixtures are missing, as in CI.
  add_executable(test_reference test/test_reference.cpp)
  target_link_libraries(test_reference yolo onnx_model opencv_imgcodecs GTest::gtest_main)
  target_compile_definitions(test_reference PRIVATE
    DETECTOR_CPP_PROJECT_ROOT="${CMAKE_CURRENT_SOURCE_DIR}/../.."
    DETECTOR_CPP_TEST_DATA_DIR="${CMAKE_CURRENT_SOURCE_DIR}/test/data")
  ament_add_gtest_test(test_reference)
endif()

ament_package()
