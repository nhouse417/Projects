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
