// Tests for letterbox, unletterbox, decode, iou and nms (yolo.hpp). Written
// before the implementation, so they start red.

#include <cmath>
#include <cstddef>
#include <vector>

#include <gtest/gtest.h>
#include <opencv2/core.hpp>
#include <opencv2/dnn.hpp>

#include "detector_cpp/yolo.hpp"

namespace detector_cpp {
namespace {

constexpr float kPad = 114.f / 255.f;
constexpr float kGray = 50.f / 255.f;
constexpr float kPixelTol = 1e-6f;

// Channel c at column x, row y of a CHW tensor that is w wide and h tall.
float at(const std::vector<float>& chw, int w, int h, int c, int x, int y) {
  return chw.at(static_cast<size_t>(c) * h * w + static_cast<size_t>(y) * w + x);
}

// ---------------------------------------------------------------- letterbox

TEST(Letterbox, Kitti1242x375) {
  const cv::Mat bgr(375, 1242, CV_8UC3, cv::Scalar::all(50));
  std::vector<float> chw;
  const LetterboxInfo lb = letterbox(bgr, 1280, 384, chw);
  EXPECT_NEAR(lb.scale, 384.f / 375.f, 1e-6);  // 1.024: 1242 * 1.024 = 1271.8 -> 1272 x 384
  EXPECT_EQ(lb.pad_x, 4);                      // (1280 - 1272) / 2
  EXPECT_EQ(lb.pad_y, 0);
  EXPECT_EQ(chw.size(), 3u * 384 * 1280);
}

TEST(Letterbox, Kitti1224x370) {
  const cv::Mat bgr(370, 1224, CV_8UC3, cv::Scalar::all(50));
  std::vector<float> chw;
  const LetterboxInfo lb = letterbox(bgr, 1280, 384, chw);
  EXPECT_NEAR(lb.scale, 384.f / 370.f, 1e-6);  // 1.0378: 1224 * 1.0378 = 1270.3 -> 1270 x 384
  EXPECT_EQ(lb.pad_x, 5);                      // (1280 - 1270) / 2
  EXPECT_EQ(lb.pad_y, 0);
  EXPECT_EQ(chw.size(), 3u * 384 * 1280);
}

TEST(Letterbox, PadsLeftAndRightWith114) {
  // A flat gray image stays exactly gray after a bilinear resize, so every
  // column is either image (50) or padding (114).
  const cv::Mat bgr(375, 1242, CV_8UC3, cv::Scalar::all(50));
  std::vector<float> chw;
  letterbox(bgr, 1280, 384, chw);
  ASSERT_EQ(chw.size(), 3u * 384 * 1280);
  for (int c = 0; c < 3; ++c) {
    for (int y : {0, 200, 383}) {
      SCOPED_TRACE(testing::Message() << "c=" << c << " y=" << y);
      EXPECT_NEAR(at(chw, 1280, 384, c, 3, y), kPad, kPixelTol);      // last left padding column
      EXPECT_NEAR(at(chw, 1280, 384, c, 4, y), kGray, kPixelTol);     // first image column
      EXPECT_NEAR(at(chw, 1280, 384, c, 1275, y), kGray, kPixelTol);  // last image column: 4+1272-1
      EXPECT_NEAR(at(chw, 1280, 384, c, 1276, y), kPad, kPixelTol);   // first right padding column
    }
  }
}

TEST(Letterbox, PadsTopAndBottomWithTheOddRowBelow) {
  // 64x15 into 64x32: scale 1, 17 rows of padding -> 8 above, 9 below.
  const cv::Mat bgr(15, 64, CV_8UC3, cv::Scalar::all(50));
  std::vector<float> chw;
  const LetterboxInfo lb = letterbox(bgr, 64, 32, chw);
  EXPECT_FLOAT_EQ(lb.scale, 1.f);
  EXPECT_EQ(lb.pad_x, 0);
  EXPECT_EQ(lb.pad_y, 8);
  ASSERT_EQ(chw.size(), 3u * 32 * 64);
  for (int c = 0; c < 3; ++c) {
    for (int x : {0, 63}) {
      SCOPED_TRACE(testing::Message() << "c=" << c << " x=" << x);
      EXPECT_NEAR(at(chw, 64, 32, c, x, 7), kPad, kPixelTol);    // last top padding row
      EXPECT_NEAR(at(chw, 64, 32, c, x, 8), kGray, kPixelTol);   // first image row
      EXPECT_NEAR(at(chw, 64, 32, c, x, 22), kGray, kPixelTol);  // last image row, 8 + 15 - 1
      EXPECT_NEAR(at(chw, 64, 32, c, x, 23), kPad, kPixelTol);   // first bottom padding row
    }
  }
}

TEST(Letterbox, BgrRedLandsInChannel0) {
  const cv::Mat bgr(375, 1242, CV_8UC3, cv::Scalar(0, 0, 255));  // pure red, BGR order
  std::vector<float> chw;
  letterbox(bgr, 1280, 384, chw);
  ASSERT_EQ(chw.size(), 3u * 384 * 1280);
  EXPECT_NEAR(at(chw, 1280, 384, 0, 640, 192), 1.f, kPixelTol);  // R
  EXPECT_NEAR(at(chw, 1280, 384, 1, 640, 192), 0.f, kPixelTol);  // G
  EXPECT_NEAR(at(chw, 1280, 384, 2, 640, 192), 0.f, kPixelTol);  // B
}

TEST(Letterbox, MatchesOpenCvBlobWhenNoResizeIsNeeded) {
  // Same size as the input, so letterbox is only BGR->RGB, /255 and
  // HWC->CHW. cv::dnn::blobFromImage does the same conversion on its own.
  cv::Mat bgr(32, 64, CV_8UC3);
  cv::randu(bgr, cv::Scalar::all(0), cv::Scalar::all(256));
  // cv::Mat::at takes (row, col): y = 10, x = 20.
  bgr.at<cv::Vec3b>(10, 20) = cv::Vec3b(10, 20, 30);
  std::vector<float> chw;
  const LetterboxInfo lb = letterbox(bgr, 64, 32, chw);
  EXPECT_FLOAT_EQ(lb.scale, 1.f);
  EXPECT_EQ(lb.pad_x, 0);
  EXPECT_EQ(lb.pad_y, 0);
  ASSERT_EQ(chw.size(), 3u * 32 * 64);

  EXPECT_NEAR(at(chw, 64, 32, 0, 20, 10), 30.f / 255.f, kPixelTol);  // R
  EXPECT_NEAR(at(chw, 64, 32, 1, 20, 10), 20.f / 255.f, kPixelTol);  // G
  EXPECT_NEAR(at(chw, 64, 32, 2, 20, 10), 10.f / 255.f, kPixelTol);  // B

  const cv::Mat blob = cv::dnn::blobFromImage(bgr, 1.0 / 255, cv::Size(), cv::Scalar(),
                                              /*swapRB=*/true, /*crop=*/false);
  ASSERT_EQ(blob.total(), chw.size());
  const float* expected = blob.ptr<float>();
  for (size_t i = 0; i < chw.size(); ++i) {
    ASSERT_NEAR(chw[i], expected[i], kPixelTol) << "index " << i;
  }
}

// -------------------------------------------------------------- unletterbox

// Image pixels -> model-input pixels, the mapping unletterbox() undoes.
Box to_input(const Box& b, const LetterboxInfo& lb) {
  return {b.x1 * lb.scale + lb.pad_x, b.y1 * lb.scale + lb.pad_y, b.x2 * lb.scale + lb.pad_x,
          b.y2 * lb.scale + lb.pad_y};
}

void expect_box_near(const Box& actual, const Box& expected, float tol) {
  EXPECT_NEAR(actual.x1, expected.x1, tol);
  EXPECT_NEAR(actual.y1, expected.y1, tol);
  EXPECT_NEAR(actual.x2, expected.x2, tol);
  EXPECT_NEAR(actual.y2, expected.y2, tol);
}

TEST(Unletterbox, InvertsTheLetterbox) {
  const Box image_box{100.3f, 50.7f, 300.2f, 200.9f};
  {
    SCOPED_TRACE("KITTI 1242x375: padding left and right");
    const LetterboxInfo lb{1.024f, 4, 0};
    expect_box_near(unletterbox(to_input(image_box, lb), lb, 1242, 375), image_box, 0.5f);
  }
  {
    SCOPED_TRACE("tall 640x600: padding above and below");
    const LetterboxInfo lb{0.5f, 0, 10};
    expect_box_near(unletterbox(to_input(image_box, lb), lb, 640, 600), image_box, 0.5f);
  }
}

TEST(Unletterbox, ClipsToTheImage) {
  // Starts in the left padding and above the input, ends past both far edges.
  const LetterboxInfo lb{1.024f, 4, 0};
  expect_box_near(unletterbox({1.f, -5.f, 1279.f, 400.f}, lb, 1242, 375), {0.f, 0.f, 1242.f, 375.f},
                  1e-4f);
}

// ------------------------------------------------------------------- decode

constexpr int kTruck = 7;  // COCO truck, not kept
const std::vector<int> kKeep{kCocoPerson, kCocoCar};

// YOLO11's raw output for one image: 4 box channels + 80 class scores for
// each of n candidates, channel-major. Value c of candidate i is at c * n + i,
// not i * 84 + c. Unset values are 0.
class RawOutput {
 public:
  static constexpr int kChannels = 84;

  explicit RawOutput(int n) : n_(n), data_(static_cast<size_t>(kChannels) * n, 0.f) {}

  void set_box(int i, float cx, float cy, float w, float h) {
    set(i, 0, cx);
    set(i, 1, cy);
    set(i, 2, w);
    set(i, 3, h);
  }
  void set_score(int i, int class_id, float score) { set(i, 4 + class_id, score); }

  const float* data() const { return data_.data(); }
  int n() const { return n_; }

 private:
  void set(int i, int c, float v) { data_.at(static_cast<size_t>(c) * n_ + i) = v; }

  int n_;
  std::vector<float> data_;
};

std::vector<Detection> decode_raw(const RawOutput& out, float conf_threshold = 0.25f) {
  return decode(out.data(), RawOutput::kChannels, out.n(), conf_threshold, kKeep);
}

TEST(Decode, KeepsCarAndConvertsCenterToCorners) {
  RawOutput out(5);
  out.set_box(3, 100.f, 50.f, 40.f, 20.f);
  out.set_score(3, kCocoCar, 0.9f);
  const std::vector<Detection> dets = decode_raw(out);
  ASSERT_EQ(dets.size(), 1u);
  EXPECT_EQ(dets[0].class_id, kCocoCar);
  EXPECT_FLOAT_EQ(dets[0].score, 0.9f);
  expect_box_near(dets[0].box, {80.f, 40.f, 120.f, 60.f}, 1e-4f);
}

TEST(Decode, KeepsPerson) {
  RawOutput out(5);
  out.set_box(1, 300.f, 200.f, 20.f, 60.f);
  out.set_score(1, kCocoPerson, 0.5f);
  const std::vector<Detection> dets = decode_raw(out);
  ASSERT_EQ(dets.size(), 1u);
  EXPECT_EQ(dets[0].class_id, kCocoPerson);
  EXPECT_FLOAT_EQ(dets[0].score, 0.5f);
  expect_box_near(dets[0].box, {290.f, 170.f, 310.f, 230.f}, 1e-4f);
}

TEST(Decode, DropsScoreBelowThreshold) {
  RawOutput out(5);
  out.set_box(2, 100.f, 50.f, 40.f, 20.f);
  out.set_score(2, kCocoPerson, 0.1f);
  EXPECT_TRUE(decode_raw(out).empty());
}

TEST(Decode, DropsCandidateWhoseBestClassIsNotKept) {
  // A van scored truck 0.6 / car 0.3. The best class is truck, so it's
  // dropped, not turned into a weak Car.
  RawOutput out(5);
  out.set_box(0, 100.f, 50.f, 40.f, 20.f);
  out.set_score(0, kTruck, 0.6f);
  out.set_score(0, kCocoCar, 0.3f);
  EXPECT_TRUE(decode_raw(out).empty());
}

TEST(Decode, OneDetectionPerCandidateFromTheBestClass) {
  RawOutput out(5);
  out.set_box(4, 100.f, 50.f, 40.f, 20.f);
  out.set_score(4, kCocoCar, 0.7f);
  out.set_score(4, kCocoPerson, 0.4f);  // above threshold, but not the best class
  const std::vector<Detection> dets = decode_raw(out);
  ASSERT_EQ(dets.size(), 1u);
  EXPECT_EQ(dets[0].class_id, kCocoCar);
  EXPECT_FLOAT_EQ(dets[0].score, 0.7f);
}

TEST(Decode, MixedCandidates) {
  RawOutput out(6);
  out.set_box(0, 100.f, 50.f, 40.f, 20.f);  // kept car
  out.set_score(0, kCocoCar, 0.9f);
  out.set_box(1, 200.f, 50.f, 20.f, 60.f);  // person below threshold
  out.set_score(1, kCocoPerson, 0.1f);
  out.set_box(2, 300.f, 50.f, 60.f, 40.f);  // best class truck
  out.set_score(2, kTruck, 0.6f);
  out.set_score(2, kCocoCar, 0.3f);
  out.set_box(3, 400.f, 50.f, 20.f, 60.f);  // kept person
  out.set_score(3, kCocoPerson, 0.5f);
  // Candidates 4 and 5 stay all zero.
  const std::vector<Detection> dets = decode_raw(out);
  ASSERT_EQ(dets.size(), 2u);
  const bool car_first = dets[0].class_id == kCocoCar;
  const Detection& car = car_first ? dets[0] : dets[1];
  const Detection& person = car_first ? dets[1] : dets[0];
  EXPECT_EQ(car.class_id, kCocoCar);
  EXPECT_EQ(person.class_id, kCocoPerson);
  expect_box_near(car.box, {80.f, 40.f, 120.f, 60.f}, 1e-4f);
  expect_box_near(person.box, {390.f, 20.f, 410.f, 80.f}, 1e-4f);
}

// ---------------------------------------------------------------------- iou

TEST(Iou, IdenticalBoxesIsOne) {
  const Box a{10.f, 20.f, 50.f, 80.f};
  EXPECT_FLOAT_EQ(iou(a, a), 1.f);
}

TEST(Iou, DisjointBoxesIsZero) {
  EXPECT_FLOAT_EQ(iou({0.f, 0.f, 10.f, 10.f}, {20.f, 20.f, 30.f, 30.f}), 0.f);
}

TEST(Iou, TouchingEdgesIsZero) {
  EXPECT_FLOAT_EQ(iou({0.f, 0.f, 10.f, 10.f}, {10.f, 0.f, 20.f, 10.f}), 0.f);
  EXPECT_FLOAT_EQ(iou({0.f, 0.f, 10.f, 10.f}, {0.f, 10.f, 10.f, 20.f}), 0.f);
}

TEST(Iou, PartialOverlap) {
  // Intersection 5x5 = 25, union 100 + 100 - 25 = 175.
  const Box a{0.f, 0.f, 10.f, 10.f};
  const Box b{5.f, 5.f, 15.f, 15.f};
  EXPECT_NEAR(iou(a, b), 25.f / 175.f, 1e-6);
  EXPECT_NEAR(iou(b, a), 25.f / 175.f, 1e-6);
}

TEST(Iou, ZeroAreaBoxesGiveZeroNotNaN) {
  const Box point{5.f, 5.f, 5.f, 5.f};
  const float same = iou(point, point);  // union 0
  EXPECT_FALSE(std::isnan(same));
  EXPECT_FLOAT_EQ(same, 0.f);
  EXPECT_FLOAT_EQ(iou(point, {0.f, 0.f, 10.f, 10.f}), 0.f);
}

// ---------------------------------------------------------------------- nms

Detection det(float x1, float y1, float x2, float y2, float score, int class_id) {
  return {{x1, y1, x2, y2}, score, class_id};
}

TEST(Nms, KeepsTheHigherOfTwoOverlappingCars) {
  // IoU 90 / 110 = 0.82. The lower score comes first in the input.
  const std::vector<Detection> kept =
      nms({det(1, 0, 11, 10, 0.8f, kCocoCar), det(0, 0, 10, 10, 0.9f, kCocoCar)}, 0.5f);
  ASSERT_EQ(kept.size(), 1u);
  EXPECT_FLOAT_EQ(kept[0].score, 0.9f);
}

TEST(Nms, DifferentClassesDoNotSuppressEachOther) {
  const std::vector<Detection> kept =
      nms({det(0, 0, 10, 10, 0.9f, kCocoCar), det(1, 0, 11, 10, 0.8f, kCocoPerson)}, 0.5f);
  ASSERT_EQ(kept.size(), 2u);
  EXPECT_EQ(kept[0].class_id, kCocoCar);
  EXPECT_EQ(kept[1].class_id, kCocoPerson);
}

TEST(Nms, OnlyKeptBoxesSuppress) {
  // IoU(A, B) = IoU(B, C) = 70 / 130 = 0.54, IoU(A, C) = 40 / 160 = 0.25.
  // A suppresses B. B was dropped, so it can't suppress C, and C stays.
  const Detection a = det(0, 0, 10, 10, 0.9f, kCocoCar);
  const Detection b = det(3, 0, 13, 10, 0.8f, kCocoCar);
  const Detection c = det(6, 0, 16, 10, 0.7f, kCocoCar);
  const std::vector<Detection> kept = nms({c, a, b}, 0.5f);
  ASSERT_EQ(kept.size(), 2u);
  EXPECT_FLOAT_EQ(kept[0].score, 0.9f);  // A
  EXPECT_FLOAT_EQ(kept[1].score, 0.7f);  // C
}

TEST(Nms, EmptyInEmptyOut) { EXPECT_TRUE(nms({}, 0.5f).empty()); }

TEST(Nms, OutputIsSortedByScore) {
  const std::vector<Detection> kept =
      nms({det(0, 0, 10, 10, 0.5f, kCocoCar), det(20, 0, 30, 10, 0.9f, kCocoCar),
           det(40, 0, 50, 10, 0.7f, kCocoPerson)},
          0.5f);
  ASSERT_EQ(kept.size(), 3u);
  EXPECT_FLOAT_EQ(kept[0].score, 0.9f);
  EXPECT_FLOAT_EQ(kept[1].score, 0.7f);
  EXPECT_FLOAT_EQ(kept[2].score, 0.5f);
}

}  // namespace
}  // namespace detector_cpp
