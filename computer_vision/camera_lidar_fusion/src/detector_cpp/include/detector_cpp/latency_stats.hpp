// Per-frame latency of one pipeline stage, summarized as mean and p95.
// Plain C++ (no ROS or OpenCV), so gtest links it directly.
#pragma once

#include <cstddef>
#include <vector>

namespace detector_cpp {

// One stage's per-frame times in milliseconds. The node keeps one per stage,
// logs a summary every few seconds, then clears it for the next window.
class LatencyStats {
 public:
  // Adds one frame's time for this stage.
  void add(double ms);

  // Mean of the samples, or 0 when there are none.
  double mean() const;

  // 95th percentile: with the samples sorted ascending, the one at index
  // round(0.95 * (n - 1)). 0 when there are none. The method is const, so it
  // sorts a copy.
  double p95() const;

  // Number of samples in the current window.
  size_t size() const;

  // Drops all samples, starting a new window.
  void clear();

 private:
  std::vector<double> samples_;
};

}  // namespace detector_cpp
