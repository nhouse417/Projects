#pragma once
#include <cstdint>

namespace gesture {

enum class Id : uint8_t { Paper = 0, Rock = 1, Scissors = 2, None = 255 };

struct Detection {
  bool valid;           // false when the frame had no box
  uint8_t model_class;  // raw class index from the model
  float score;          // 0 to 1
  float cx, cy;         // normalized box center
};

struct Event {
  Id gesture;
  float confidence;
  float cx, cy;
};

struct Config {
  uint8_t frames_to_confirm = 5;
  float min_score = 0.60f;
  uint32_t none_timeout_ms = 500;
};

class Debouncer {
 public:
  explicit Debouncer(const Config& cfg) : cfg_(cfg) {}
  // Call once per inference frame. Returns true and fills `out`
  // only when the confirmed gesture changes.
  bool update(const Detection& det, uint32_t now_ms, Event& out);
  Id current() const { return state_; }

 private:
  static Id map_class(uint8_t model_class);
  Config cfg_;
  Id state_ = Id::None;
  Id candidate_ = Id::None;
  uint8_t streak_ = 0;
  uint32_t last_seen_ms_ = 0;
};

}  // namespace gesture
