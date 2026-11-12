#include <algorithm>
#include <string>
#include <vector>

#include <cv_bridge/cv_bridge.hpp>
#include <opencv2/imgproc.hpp>

#include "detector_cpp/detector_node.hpp"
#include "detector_cpp/yolo.hpp"

// Steps to complete cv pipeline, subscribe and publish detections
//   1. subscribe to /kitti/camera/image_raw and log the image size
//   2. run the detector on each image (cv_bridge, OnnxModel, yolo.hpp)
//   3. publish /detector/detections (vision_msgs/Detection2DArray)
//   4. publish /detector/image_annotated
//   5. log per-stage latency (mean and p95)

namespace detector_cpp {
namespace {

// COCO classes the node keeps: person becomes Pedestrian, car becomes Car.
const std::vector<int> kKeepClasses{kCocoPerson, kCocoCar};

// returns class_id string needed to fill vision_msgs::msg::ObjectHypothesisWithPose
std::string kitti_class(int coco_id) { return coco_id == kCocoPerson ? "Pedestrian" : "Car"; }

// draws each box and its label on one image
void draw_detections(cv::Mat& image, const std::vector<Detection>& dets) {
  for (const Detection& d : dets) {
    // red color for Pedestrian, green for Car
    const cv::Scalar color =
        (d.class_id == kCocoPerson) ? cv::Scalar(0, 0, 255) : cv::Scalar(0, 255, 0);

    cv::rectangle(image, cv::Point(d.box.x1, d.box.y1), cv::Point(d.box.x2, d.box.y2), color, 2);
    cv::putText(image, cv::format("%s %.2f", kitti_class(d.class_id).c_str(), d.score),
                cv::Point(d.box.x1, std::max(d.box.y1 - 4, 12.f)), cv::FONT_HERSHEY_SIMPLEX, 0.5,
                color, 1);
  }
}

}  // namespace

DetectorNode::DetectorNode() : rclcpp::Node("detector") {
  // ROS2 params don't have a float type so declare double then static_cast<float> to convert
  conf_threshold_ = static_cast<float>(declare_parameter<double>("conf_threshold", 0.25));
  iou_threshold_ = static_cast<float>(declare_parameter<double>("iou_threshold", 0.5));

  const std::string model_path =
      declare_parameter<std::string>("model_path", "models/yolo11n_384x1280.onnx");

  model_ = std::make_unique<OnnxModel>(model_path);

  detections_pub_ =
      create_publisher<vision_msgs::msg::Detection2DArray>("/detector/detections", 10);

  annotated_pub_ = create_publisher<sensor_msgs::msg::Image>("/detector/image_annotated", 10);

  image_sub_ = create_subscription<sensor_msgs::msg::Image>(
      "/kitti/camera/image_raw", 10,
      [this](const sensor_msgs::msg::Image::ConstSharedPtr& msg) { on_image(msg); });
}

void DetectorNode::on_image(const sensor_msgs::msg::Image::ConstSharedPtr& msg) {
  // cv pipeline that converts incoming msg to a Detection
  const cv::Mat bgr = cv_bridge::toCvShare(msg, "bgr8")->image;

  std::vector<float> chw;
  const LetterboxInfo lb = letterbox(bgr, model_->input_w(), model_->input_h(), chw);
  const float* output = model_->run(chw);
  std::vector<Detection> conf_dets = decode(
      output, model_->num_channels(), model_->num_candidates(), conf_threshold_, kKeepClasses);
  std::vector<Detection> final_dets = nms(conf_dets, iou_threshold_);
  for (Detection& d : final_dets) d.box = unletterbox(d.box, lb, bgr.cols, bgr.rows);
  RCLCPP_INFO(get_logger(), "%zu detections", final_dets.size());

  // publishing every frame, even if there's no boxes, so step A3's exact sync sees each frame
  vision_msgs::msg::Detection2DArray out;
  out.header = msg->header;

  for (const Detection& d : final_dets) {
    vision_msgs::msg::Detection2D det;
    det.header = msg->header;

    det.bbox.center.position.x = (d.box.x1 + d.box.x2) / 2;
    det.bbox.center.position.y = (d.box.y1 + d.box.y2) / 2;
    det.bbox.size_x = d.box.x2 - d.box.x1;
    det.bbox.size_y = d.box.y2 - d.box.y1;

    vision_msgs::msg::ObjectHypothesisWithPose hyp;
    hyp.hypothesis.class_id = kitti_class(d.class_id);
    hyp.hypothesis.score = d.score;
    det.results.push_back(hyp);

    out.detections.push_back(det);
  }

  detections_pub_->publish(out);

  // draw on a copy, bgr has the incoming message's pixels
  cv::Mat annotated = bgr.clone();
  draw_detections(annotated, final_dets);
  annotated_pub_->publish(*cv_bridge::CvImage(msg->header, "bgr8", annotated).toImageMsg());
}

}  // namespace detector_cpp

int main(int argc, char** argv) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<detector_cpp::DetectorNode>());
  rclcpp::shutdown();
  return 0;
}
