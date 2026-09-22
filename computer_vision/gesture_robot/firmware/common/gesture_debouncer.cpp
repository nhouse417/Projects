#include "gesture_debouncer.h"

namespace gesture {

// The only place that knows the model's class order.
Id Debouncer::map_class(uint8_t model_class) {
  static const Id kMap[] = {Id::Paper, Id::Rock, Id::Scissors};
  return model_class < 3 ? kMap[model_class] : Id::None;
}

bool Debouncer::update(const Detection& det, uint32_t now_ms, Event& out) {
  // Unsigned subtraction stays correct across millis() wraparound.
  const bool gap = now_ms - last_seen_ms_ > cfg_.none_timeout_ms;
  if (gap) {
    // Frames on either side of a long gap are never consecutive.
    candidate_ = Id::None;
    streak_ = 0;
  }

  if (det.valid && det.score >= cfg_.min_score) {
    Id id = map_class(det.model_class);
    last_seen_ms_ = now_ms;
    if (id == candidate_) {
      if (streak_ < 255) ++streak_;
    } else {
      candidate_ = id;
      streak_ = 1;
    }
    if (streak_ >= cfg_.frames_to_confirm && id != state_) {
      state_ = id;
      out = {id, det.score, det.cx, det.cy};
      return true;
    }
    return false;
  }

  // Frames without a usable box don't break the streak on their own.
  if (gap && state_ != Id::None) {
    state_ = Id::None;
    out = {Id::None, 0.0f, 0.0f, 0.0f};
    return true;
  }
  return false;
}

}  // namespace gesture
