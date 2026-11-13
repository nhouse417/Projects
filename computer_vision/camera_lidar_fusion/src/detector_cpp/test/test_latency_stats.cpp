// Tests for LatencyStats (latency_stats.hpp). Written before the
// implementation, so they start red.

#include <gtest/gtest.h>

#include "detector_cpp/latency_stats.hpp"

namespace detector_cpp {
namespace {

TEST(LatencyStats, EmptyIsZero) {
  const LatencyStats stats;
  EXPECT_EQ(stats.size(), 0u);
  EXPECT_EQ(stats.mean(), 0.0);
  EXPECT_EQ(stats.p95(), 0.0);
}

TEST(LatencyStats, OneSample) {
  LatencyStats stats;
  stats.add(12.5);
  EXPECT_EQ(stats.size(), 1u);
  EXPECT_DOUBLE_EQ(stats.mean(), 12.5);
  EXPECT_DOUBLE_EQ(stats.p95(), 12.5);
}

// Added largest first, so p95 is only right if it sorts. Index
// round(0.95 * 99) = round(94.05) = 94 holds 95.
TEST(LatencyStats, OneToHundred) {
  LatencyStats stats;
  for (int ms = 100; ms >= 1; --ms) stats.add(ms);
  EXPECT_EQ(stats.size(), 100u);
  EXPECT_DOUBLE_EQ(stats.mean(), 50.5);
  EXPECT_DOUBLE_EQ(stats.p95(), 95.0);
}

// Two slow frames out of 20: the mean barely moves, p95 lands on them.
// Index round(0.95 * 19) = round(18.05) = 18.
TEST(LatencyStats, P95CatchesSlowFrames) {
  LatencyStats stats;
  stats.add(80.0);
  stats.add(80.0);
  for (int i = 0; i < 18; ++i) stats.add(20.0);
  EXPECT_DOUBLE_EQ(stats.mean(), 26.0);
  EXPECT_DOUBLE_EQ(stats.p95(), 80.0);
}

// Index round(0.95 * 2) = round(1.9) = 2, the largest. Truncating to int
// instead of rounding gives index 1.
TEST(LatencyStats, P95RoundsTheIndex) {
  LatencyStats stats;
  stats.add(30.0);
  stats.add(10.0);
  stats.add(20.0);
  EXPECT_DOUBLE_EQ(stats.p95(), 30.0);
}

TEST(LatencyStats, ClearStartsANewWindow) {
  LatencyStats stats;
  stats.add(50.0);
  stats.add(70.0);
  stats.clear();
  EXPECT_EQ(stats.size(), 0u);
  EXPECT_EQ(stats.mean(), 0.0);
  EXPECT_EQ(stats.p95(), 0.0);
  stats.add(5.0);
  EXPECT_DOUBLE_EQ(stats.mean(), 5.0);
  EXPECT_DOUBLE_EQ(stats.p95(), 5.0);
}

}  // namespace
}  // namespace detector_cpp
