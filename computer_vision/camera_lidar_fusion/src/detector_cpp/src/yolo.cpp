#include "detector_cpp/yolo.hpp"

#include <algorithm>
#include <cmath>

#include <opencv2/imgproc.hpp>

// Stubs: they compile and return empty, so the tests start red. Write the
// bodies in data order: letterbox -> unletterbox -> decode -> iou -> nms.
// Parameter names are commented out to keep -Wunused-parameter quiet until
// each body is written.

namespace detector_cpp {

LetterboxInfo letterbox(const cv::Mat& /*bgr*/, int /*input_w*/, int /*input_h*/,
                        std::vector<float>& /*chw*/) {
  return {};
}

Box unletterbox(const Box& /*b*/, const LetterboxInfo& /*lb*/, int /*image_w*/, int /*image_h*/) {
  return {};
}

std::vector<Detection> decode(const float* /*output*/, int /*num_channels*/, int /*num_candidates*/,
                              float /*conf_threshold*/, const std::vector<int>& /*keep_classes*/) {
  return {};
}

float iou(const Box& /*a*/, const Box& /*b*/) {
  return 0.f;
}

std::vector<Detection> nms(std::vector<Detection> /*dets*/, float /*iou_threshold*/) {
  return {};
}

}  // namespace detector_cpp
