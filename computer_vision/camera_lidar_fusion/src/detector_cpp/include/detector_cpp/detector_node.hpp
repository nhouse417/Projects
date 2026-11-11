// ROS 2 node around the YOLO11 pipeline in yolo.hpp: subscribes to the KITTI
// camera image, runs letterbox -> OnnxModel -> decode -> nms -> unletterbox,
// and publishes vision_msgs/Detection2DArray plus an annotated image.
#pragma once

#include "detector_cpp/onnx_model.hpp"

#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/image.hpp>
#include <vision_msgs/msg/detection2_d_array.hpp>

#include <memory>

namespace detector_cpp {

class DetectorNode : public rclcpp::Node {
 public:
  DetectorNode();

 private:
  void on_image(const sensor_msgs::msg::Image::ConstSharedPtr& msg);
  rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr image_sub_;
  rclcpp::Publisher<vision_msgs::msg::Detection2DArray>::SharedPtr detections_pub_;
  float conf_threshold_ = 0.f;
  float iou_threshold_ = 0.f;
  std::unique_ptr<OnnxModel> model_;
};

}  // namespace detector_cpp
