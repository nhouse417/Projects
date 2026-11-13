#include <algorithm>
#include <cmath>
#include <numeric>

#include "detector_cpp/latency_stats.hpp"

namespace detector_cpp {

void LatencyStats::add(double ms) { samples_.push_back(ms); }

double LatencyStats::mean() const {
  if (samples_.empty()) return 0;
  return (std::accumulate(samples_.begin(), samples_.end(), 0.) / samples_.size());
}

double LatencyStats::p95() const {
  if (samples_.empty()) return 0;

  std::vector<double> samples_copy = samples_;
  std::sort(samples_copy.begin(), samples_copy.end());
  const size_t index = static_cast<size_t>(std::round(0.95 * (samples_.size() - 1)));
  return samples_copy[index];
}

size_t LatencyStats::size() const { return samples_.size(); }

void LatencyStats::clear() { samples_.clear(); }

}  // namespace detector_cpp
