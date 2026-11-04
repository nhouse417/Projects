// Runs the whole C++ pipeline (letterbox -> ONNX Runtime -> decode -> NMS ->
// unletterbox) on real KITTI frames and compares the boxes with Ultralytics'
// own predict, saved by tools/yolo_reference.py. That checks preprocessing
// and decoding against what the model really expects.
//
// KITTI images can't be committed, so the frames are read from KITTI_ROOT
// (default data/kitti_tracking) and the model from DETECTOR_MODEL (default
// models/yolo11n_384x1280.onnx). The test skips when either is missing, which
// is always the case in CI:
//
//   KITTI_ROOT="/Volumes/Extreme SSD/kitti_tracking" pixi run test

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

#include <gtest/gtest.h>
#include <opencv2/imgcodecs.hpp>

#include "detector_cpp/onnx_model.hpp"
#include "detector_cpp/yolo.hpp"

namespace detector_cpp {
namespace {

namespace fs = std::filesystem;

// Must match tools/yolo_reference.py.
constexpr float kConfThreshold = 0.25f;
constexpr float kIouThreshold = 0.5f;
const std::vector<int> kKeepClasses{kCocoPerson, kCocoCar};

// Boxes this close to the threshold can flip in or out between ONNX Runtime
// builds, so only boxes above kConfThreshold + kScoreMargin must match.
constexpr float kScoreMargin = 0.05f;
constexpr float kPixelTolerance = 1.f;
constexpr float kScoreTolerance = 0.01f;

fs::path env_or(const char* name, const fs::path& fallback) {
  const char* value = std::getenv(name);
  return value && *value ? fs::path(value) : fallback;
}

// `class_id score x1 y1 x2 y2` per line; lines starting with # are comments.
std::vector<Detection> read_fixture(const fs::path& path) {
  std::vector<Detection> dets;
  std::ifstream in(path);
  std::string line;
  while (std::getline(in, line)) {
    if (line.empty() || line[0] == '#') continue;
    std::istringstream row(line);
    Detection d{};
    row >> d.class_id >> d.score >> d.box.x1 >> d.box.y1 >> d.box.x2 >> d.box.y2;
    if (row) dets.push_back(d);
  }
  return dets;
}

// Largest corner difference in pixels. Matching uses this rather than iou()
// so a bug in iou() can't hide a mismatch.
float corner_distance(const Box& a, const Box& b) {
  return std::max({std::abs(a.x1 - b.x1), std::abs(a.y1 - b.y1), std::abs(a.x2 - b.x2),
                   std::abs(a.y2 - b.y2)});
}

std::string describe(const Detection& d) {
  std::ostringstream s;
  s << "class " << d.class_id << " score " << d.score << " (" << d.box.x1 << ", " << d.box.y1
    << ", " << d.box.x2 << ", " << d.box.y2 << ")";
  return s.str();
}

// Every confident box in `from` has a same-class box in `in` within the tolerances.
void expect_all_matched(const std::vector<Detection>& from, const char* from_name,
                        const std::vector<Detection>& in, const char* in_name) {
  for (const Detection& f : from) {
    if (f.score < kConfThreshold + kScoreMargin) continue;
    const Detection* nearest = nullptr;
    for (const Detection& d : in) {
      if (d.class_id == f.class_id &&
          (!nearest || corner_distance(d.box, f.box) < corner_distance(nearest->box, f.box))) {
        nearest = &d;
      }
    }
    if (!nearest) {
      ADD_FAILURE() << from_name << " box " << describe(f) << " has no " << in_name << " box of that class";
      continue;
    }
    EXPECT_LE(corner_distance(nearest->box, f.box), kPixelTolerance)
        << from_name << " " << describe(f) << " vs nearest " << in_name << " " << describe(*nearest);
    EXPECT_NEAR(nearest->score, f.score, kScoreTolerance)
        << from_name << " " << describe(f) << " vs nearest " << in_name << " " << describe(*nearest);
  }
}

class Reference : public testing::TestWithParam<std::string> {};

TEST_P(Reference, MatchesUltralyticsPredict) {
  const std::string frame = GetParam();  // "<seq>/<frame>"
  const fs::path project_root = DETECTOR_CPP_PROJECT_ROOT;
  const fs::path model_path = env_or("DETECTOR_MODEL", project_root / "models" / "yolo11n_384x1280.onnx");
  const fs::path image_path =
      env_or("KITTI_ROOT", project_root / "data" / "kitti_tracking") / "training" / "image_02" / (frame + ".png");
  std::string fixture_name = "reference_" + frame + ".txt";
  std::replace(fixture_name.begin(), fixture_name.end(), '/', '_');
  const fs::path fixture_path = fs::path(DETECTOR_CPP_TEST_DATA_DIR) / fixture_name;

  if (!fs::is_regular_file(fixture_path)) {
    GTEST_SKIP() << fixture_path << " not found; run `pixi run yolo-reference`";
  }
  if (!fs::is_regular_file(model_path)) {
    GTEST_SKIP() << model_path << " not found; run `pixi run export-yolo` or set DETECTOR_MODEL";
  }
  if (!fs::is_regular_file(image_path)) {
    GTEST_SKIP() << image_path << " not found; set KITTI_ROOT";
  }

  const std::vector<Detection> expected = read_fixture(fixture_path);
  ASSERT_FALSE(expected.empty()) << fixture_path << " has no boxes";

  OnnxModel model(model_path.string());
  // Ultralytics stores the class names as a Python dict repr.
  const std::string names = model.metadata("names");
  EXPECT_NE(names.find("0: 'person'"), std::string::npos) << names;
  EXPECT_NE(names.find("2: 'car'"), std::string::npos) << names;

  const cv::Mat bgr = cv::imread(image_path.string(), cv::IMREAD_COLOR);
  ASSERT_FALSE(bgr.empty()) << "can't read " << image_path;

  std::vector<float> chw;
  const LetterboxInfo lb = letterbox(bgr, model.input_w(), model.input_h(), chw);
  ASSERT_EQ(chw.size(), 3u * model.input_h() * model.input_w());
  const float* output = model.run(chw);
  std::vector<Detection> actual =
      nms(decode(output, model.num_channels(), model.num_candidates(), kConfThreshold, kKeepClasses),
          kIouThreshold);
  for (Detection& d : actual) d.box = unletterbox(d.box, lb, bgr.cols, bgr.rows);

  expect_all_matched(expected, "Ultralytics", actual, "C++");
  expect_all_matched(actual, "C++", expected, "Ultralytics");
}

// 0000 is 1242x375 (pad_x 4); 0016 is 1224x370 (pad_x 5).
INSTANTIATE_TEST_SUITE_P(Kitti, Reference, testing::Values("0000/000000", "0016/000000"),
                         [](const testing::TestParamInfo<std::string>& info) {
                           std::string name = "seq" + info.param;
                           std::replace(name.begin(), name.end(), '/', '_');
                           return name;
                         });

}  // namespace
}  // namespace detector_cpp
