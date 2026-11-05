#include "detector_cpp/yolo.hpp"

#include <algorithm>
#include <cmath>

#include <opencv2/imgproc.hpp>

// Stubs: they compile and return empty, so the tests start red. Write the
// bodies in data order: letterbox -> unletterbox -> decode -> iou -> nms.
// Parameter names are commented out to keep -Wunused-parameter quiet until
// each body is written.

namespace detector_cpp {

LetterboxInfo letterbox(const cv::Mat& bgr, int input_w, int input_h, std::vector<float>& chw) {
  CV_Assert(!bgr.empty() && bgr.type() == CV_8UC3);

  // get input image size from bgr
  const int W = bgr.cols;
  const int H = bgr.rows;

  // compute uniform scale so image isn't stretched
  const float scale = std::min(static_cast<float>(input_h) / H, static_cast<float>(input_w) / W);

  const int new_w = static_cast<int>(std::round(W * scale));
  const int new_h = static_cast<int>(std::round(H * scale));

  // resize image using new height and width
  cv::Mat resized;
  cv::resize(bgr, resized, cv::Size(new_w, new_h));

  // compute padding
  const int pad_x = (input_w - new_w) / 2;
  const int pad_y = (input_h - new_h) / 2;

  // add padding to resized
  cv::Mat padded;
  cv::copyMakeBorder(resized, padded, pad_y, input_h - new_h - pad_y, pad_x,
                     input_w - new_w - pad_x, cv::BORDER_CONSTANT, cv::Scalar(114, 114, 114));

  // convert colorspace from BGR to RGB
  cv::cvtColor(padded, padded, cv::COLOR_BGR2RGB);

  // convert image library image from CV_8UC3 to CV_32FC3
  // and normalize values from [0, 255] to [0, 1]
  // purpose: so these images are correctly formatted for ML model
  cv::Mat normalized;
  padded.convertTo(normalized, CV_32FC3, 1.0 / 255);

  // reorder pixel data from HWC to CHW for the ML model
  // y = row (vertical position), x = col (horizontal position)
  const int plane = input_h * input_w;
  chw.resize(3 * plane);
  for (int y = 0; y < input_h; ++y) {
    for (int x = 0; x < input_w; ++x) {
      const cv::Vec3f& px = normalized.at<cv::Vec3f>(y, x);
      for (int c = 0; c < 3; ++c) {
        chw[c * plane + y * input_w + x] = px[c];
      }
    }
  }

  return {scale, pad_x, pad_y};
}

Box unletterbox(const Box& b, const LetterboxInfo& lb, int image_w, int image_h) {
  const float x1 = (b.x1 - lb.pad_x) / lb.scale;
  const float y1 = (b.y1 - lb.pad_y) / lb.scale;
  const float x2 = (b.x2 - lb.pad_x) / lb.scale;
  const float y2 = (b.y2 - lb.pad_y) / lb.scale;

  return {std::clamp(x1, 0.f, static_cast<float>(image_w)),
          std::clamp(y1, 0.f, static_cast<float>(image_h)),
          std::clamp(x2, 0.f, static_cast<float>(image_w)),
          std::clamp(y2, 0.f, static_cast<float>(image_h))};
}

std::vector<Detection> decode(const float* output, int num_channels, int num_candidates,
                              float conf_threshold, const std::vector<int>& keep_classes) {
  
  std::vector<Detection> result;

  for (int i = 0; i < num_candidates; i++) {
    float best_score = 0.f;
    int best_class = -1;

    for (int c = 4; c < num_channels; c++) {
      const float score = output[c * num_candidates + i];
      if (score > best_score) {
        best_score = score;
        best_class = c - 4;
      }
    }

    if (best_score < conf_threshold ||
        std::find(keep_classes.begin(), keep_classes.end(), best_class) == keep_classes.end()) {
      continue;
    }

    // x1 = cx (channel 0) - w (channel 2) / 2
    // y1 = cy (channel 1) - h (channel 3) / 2
    // x2 = cx + w / 2
    // y2 = cy + h / 2
    // purpose: to find the corners of the box from the center coords
    const float x1 = output[0 * num_candidates + i] - (output[2 * num_candidates + i] / 2.f);
    const float y1 = output[1 * num_candidates + i] - (output[3 * num_candidates + i] / 2.f);
    const float x2 = output[0 * num_candidates + i] + (output[2 * num_candidates + i] / 2.f);
    const float y2 = output[1 * num_candidates + i] + (output[3 * num_candidates + i] / 2.f);

    result.push_back({{x1, y1, x2, y2}, best_score, best_class});
  }

  return result;
}

float iou(const Box& /*a*/, const Box& /*b*/) { return 0.f; }

std::vector<Detection> nms(std::vector<Detection> /*dets*/, float /*iou_threshold*/) { return {}; }

}  // namespace detector_cpp
