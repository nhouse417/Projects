#include <vector>

#include <cv_bridge/cv_bridge.hpp>

#include "detector_cpp/detector_node.hpp"
#include "detector_cpp/yolo.hpp"

// Skeleton: it builds and does nothing yet. Build it up step by step:
//   1. subscribe to /kitti/camera/image_raw and log the image size
//   2. run the detector on each image (cv_bridge, OnnxModel, yolo.hpp)
//   3. publish /detector/detections (vision_msgs/Detection2DArray)
//   4. publish /detector/image_annotated
//   5. log per-stage latency (mean and p95)

namespace detector_cpp {
namespace {

// COCO classes the node keeps: person becomes Pedestrian, car becomes Car.
const std::vector<int> kKeepClasses{kCocoPerson, kCocoCar};

}  // namespace

DetectorNode::DetectorNode() : rclcpp::Node("detector") {
  // ROS2 params don't have a float type so declare double then static_cast<float> to convert
  conf_threshold_ = static_cast<float>(declare_parameter<double>("conf_threshold", 0.25));
  iou_threshold_ = static_cast<float>(declare_parameter<double>("iou_threshold", 0.5));

  const std::string model_path =
      declare_parameter<std::string>("model_path", "models/yolo11n_384x1280.onnx");

  model_ = std::make_unique<OnnxModel>(model_path);

  image_sub_ = create_subscription<sensor_msgs::msg::Image>(
      "/kitti/camera/image_raw", 10,
      [this](const sensor_msgs::msg::Image::ConstSharedPtr& msg) { on_image(msg); });
}

void DetectorNode::on_image(const sensor_msgs::msg::Image::ConstSharedPtr& msg) {
  // start of cv pipeline
  // get immutable raw image converted to bgr8 so we can run it through cv pipeline
  const cv::Mat bgr = cv_bridge::toCvShare(msg, "bgr8")->image;

  std::vector<float> chw;
  const LetterboxInfo lb = letterbox(bgr, model_->input_w(), model_->input_h(), chw);
  const float* output = model_->run(chw);
  std::vector<Detection> conf_dets = decode(
      output, model_->num_channels(), model_->num_candidates(), conf_threshold_, kKeepClasses);
  std::vector<Detection> final_dets = nms(conf_dets, iou_threshold_);
  for (Detection& d : final_dets) d.box = unletterbox(d.box, lb, bgr.cols, bgr.rows);
  RCLCPP_INFO(get_logger(), "%zu detections", final_dets.size());
}

}  // namespace detector_cpp

int main(int argc, char** argv) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<detector_cpp::DetectorNode>());
  rclcpp::shutdown();
  return 0;
}
