// ONNX Runtime session for a YOLO model with one static input [1, 3, H, W] and
// one output [1, channels, candidates]. ROS-free, so the node and the
// reference test share it.
#pragma once

#include <string>
#include <vector>

#include <core/session/onnxruntime_cxx_api.h>

namespace detector_cpp {

class OnnxModel {
 public:
  // Loads the model for the CPU. intra_op_threads = 0 lets ONNX Runtime pick.
  // Throws Ort::Exception if the file doesn't load, std::runtime_error if the
  // shapes aren't the ones above.
  explicit OnnxModel(const std::string& path, int intra_op_threads = 0);

  int input_w() const { return input_w_; }
  int input_h() const { return input_h_; }
  int num_channels() const { return num_channels_; }
  int num_candidates() const { return num_candidates_; }

  // Custom metadata value, or "" when the key is missing. Ultralytics stores
  // "names", "imgsz" and "stride".
  std::string metadata(const std::string& key) const;

  // Runs one image. chw holds 3 * input_h * input_w floats, as letterbox()
  // writes them. Returns the output [num_channels, num_candidates], valid
  // until the next run().
  const float* run(std::vector<float>& chw);

 private:
  Ort::Env env_;  // must outlive session_, so it's declared first
  Ort::Session session_{nullptr};
  std::string input_name_;
  std::string output_name_;
  int input_w_ = 0;
  int input_h_ = 0;
  int num_channels_ = 0;
  int num_candidates_ = 0;
  std::vector<Ort::Value> outputs_;
};

}  // namespace detector_cpp
