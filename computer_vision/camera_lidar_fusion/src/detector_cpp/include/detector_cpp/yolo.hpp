// YOLO11 pre- and post-processing: letterbox, unletterbox, decode, IoU, NMS.
// OpenCV only (no ROS, no ONNX Runtime), so gtest links it directly.
#pragma once

#include <vector>

#include <opencv2/core.hpp>

namespace detector_cpp {

// COCO class ids the node keeps. YOLO11 is trained on COCO's 80 classes.
constexpr int kCocoPerson = 0;
constexpr int kCocoCar = 2;

struct Box { float x1, y1, x2, y2; };                      // corner format, pixels
struct Detection { Box box; float score; int class_id; };  // COCO class id
struct LetterboxInfo { float scale; int pad_x; int pad_y; };

/*
   Fits a BGR image into the model input without distorting it, then converts
   it to the model's input layout.
     - Uniform scale = min(input_w / W, input_h / H); the resized size is rounded
       to whole pixels and resized bilinearly.
     - The resized image is centered; the left/top padding is
       (input - resized) / 2, rounded down. Padding is gray 114.
     - chw is resized to 3 * input_h * input_w floats: RGB, values in [0, 1],
       planar, with channel c, row y, column x at c * input_h * input_w + y * input_w + x.
    Returns what unletterbox() needs to map boxes back to the image.
*/
LetterboxInfo letterbox(const cv::Mat& bgr, int input_w, int input_h, std::vector<float>& chw);

// Maps a box from model-input pixels back to image pixels, clipped to
// [0, image_w] x [0, image_h].
Box unletterbox(const Box& b, const LetterboxInfo& lb, int image_w, int image_h);

/* Decodes YOLO11's raw output for one image, shape [num_channels, num_candidates]
   and channel-major: value c of candidate i is output[c * num_candidates + i].
   Channels 0-3 are the box center and size (cx, cy, w, h) in model-input
   pixels; the rest are class scores, already sigmoided, with no objectness.
   A candidate is kept when its best class over all classes scores at least
   conf_threshold and is one of keep_classes. Boxes come back in corner format.
*/
std::vector<Detection> decode(const float* output, int num_channels, int num_candidates,
                              float conf_threshold, const std::vector<int>& keep_classes);

// Intersection over union of two corner-format boxes. 0 when they don't
// overlap or the union is empty, never NaN.
float iou(const Box& a, const Box& b);

// Greedy per-class non-maximum suppression. A detection is dropped when its
// IoU with a higher-scoring kept detection of the same class is above
// iou_threshold. Returns the kept detections, highest score first.
std::vector<Detection> nms(std::vector<Detection> dets, float iou_threshold);

}  // namespace detector_cpp
