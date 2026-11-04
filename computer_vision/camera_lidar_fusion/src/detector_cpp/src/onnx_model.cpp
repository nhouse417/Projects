#include "detector_cpp/onnx_model.hpp"

#include <array>
#include <cstdint>
#include <stdexcept>

namespace detector_cpp {
namespace {

std::string shape_str(const std::vector<int64_t>& shape) {
  std::string s = "[";
  for (size_t i = 0; i < shape.size(); ++i) {
    s += (i ? ", " : "") + std::to_string(shape[i]);
  }
  return s + "]";
}

}  // namespace

OnnxModel::OnnxModel(const std::string& path, int intra_op_threads)
    : env_(ORT_LOGGING_LEVEL_WARNING, "detector_cpp") {
  Ort::SessionOptions options;
  options.SetIntraOpNumThreads(intra_op_threads);
  options.SetGraphOptimizationLevel(GraphOptimizationLevel::ORT_ENABLE_ALL);
  session_ = Ort::Session(env_, path.c_str(), options);

  if (session_.GetInputCount() != 1 || session_.GetOutputCount() != 1) {
    throw std::runtime_error(path + ": expected one input and one output");
  }
  Ort::AllocatorWithDefaultOptions allocator;
  input_name_ = session_.GetInputNameAllocated(0, allocator).get();
  output_name_ = session_.GetOutputNameAllocated(0, allocator).get();

  // A dynamic dimension reads as -1, so this also rejects dynamic exports.
  const std::vector<int64_t> in = session_.GetInputTypeInfo(0).GetTensorTypeAndShapeInfo().GetShape();
  if (in.size() != 4 || in[0] != 1 || in[1] != 3 || in[2] <= 0 || in[3] <= 0) {
    throw std::runtime_error(path + ": expected a static input [1, 3, H, W], got " + shape_str(in));
  }
  input_h_ = static_cast<int>(in[2]);
  input_w_ = static_cast<int>(in[3]);

  const std::vector<int64_t> out = session_.GetOutputTypeInfo(0).GetTensorTypeAndShapeInfo().GetShape();
  if (out.size() != 3 || out[0] != 1 || out[1] <= 4 || out[2] <= 0) {
    throw std::runtime_error(path + ": expected an output [1, 4 + classes, candidates], got " +
                             shape_str(out));
  }
  num_channels_ = static_cast<int>(out[1]);
  num_candidates_ = static_cast<int>(out[2]);
}

std::string OnnxModel::metadata(const std::string& key) const {
  Ort::AllocatorWithDefaultOptions allocator;
  const Ort::ModelMetadata meta = session_.GetModelMetadata();
  const Ort::AllocatedStringPtr value = meta.LookupCustomMetadataMapAllocated(key.c_str(), allocator);
  return value ? std::string(value.get()) : std::string();
}

const float* OnnxModel::run(std::vector<float>& chw) {
  const size_t expected = 3u * input_h_ * input_w_;
  if (chw.size() != expected) {
    throw std::invalid_argument("OnnxModel::run: expected " + std::to_string(expected) +
                                " floats, got " + std::to_string(chw.size()));
  }
  const std::array<int64_t, 4> shape{1, 3, input_h_, input_w_};
  const Ort::MemoryInfo memory = Ort::MemoryInfo::CreateCpu(OrtArenaAllocator, OrtMemTypeDefault);
  const Ort::Value input =
      Ort::Value::CreateTensor<float>(memory, chw.data(), chw.size(), shape.data(), shape.size());
  const char* input_names[] = {input_name_.c_str()};
  const char* output_names[] = {output_name_.c_str()};
  outputs_ = session_.Run(Ort::RunOptions{nullptr}, input_names, &input, 1, output_names, 1);
  return outputs_.front().GetTensorData<float>();
}

}  // namespace detector_cpp
