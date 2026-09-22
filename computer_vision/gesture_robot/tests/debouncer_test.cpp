// Host unit tests for firmware/common/gesture_debouncer. From the repo root:
//   mkdir -p build && g++ -std=c++17 -Wall -Wextra -Werror -Ifirmware/common \
//     tests/debouncer_test.cpp firmware/common/gesture_debouncer.cpp \
//     -o build/debouncer_test && build/debouncer_test

#include <cstdint>
#include <cstdio>
#include <string>

#include "gesture_debouncer.h"

namespace {

using gesture::Config;
using gesture::Debouncer;
using gesture::Detection;
using gesture::Event;
using gesture::Id;

static_assert(static_cast<uint8_t>(Id::Paper) == 0, "must match Gesture.msg PAPER");
static_assert(static_cast<uint8_t>(Id::Rock) == 1, "must match Gesture.msg ROCK");
static_assert(static_cast<uint8_t>(Id::Scissors) == 2, "must match Gesture.msg SCISSORS");
static_assert(static_cast<uint8_t>(Id::None) == 255, "must match Gesture.msg NONE");

constexpr uint8_t kPaper = 0;
constexpr uint8_t kRock = 1;
constexpr uint8_t kScissors = 2;
constexpr uint32_t kFrameMs = 33;  // about 30 fps

int g_checks = 0;
int g_failures = 0;
std::string g_detail;

const char* name(Id id) {
  switch (id) {
    case Id::Paper: return "paper";
    case Id::Rock: return "rock";
    case Id::Scissors: return "scissors";
    case Id::None: return "none";
  }
  return "?";
}

void report_failure(const char* file, int line, const std::string& what) {
  ++g_failures;
  char buf[512];
  std::snprintf(buf, sizeof buf, "      %s:%d  %s\n", file, line, what.c_str());
  g_detail += buf;
}

#define CHECK(cond)                                           \
  do {                                                        \
    ++g_checks;                                               \
    if (!(cond)) report_failure(__FILE__, __LINE__, #cond);   \
  } while (0)

#define CHECK_ID(actual, expected)                                          \
  do {                                                                      \
    ++g_checks;                                                             \
    const Id a_ = (actual), e_ = (expected);                                \
    if (a_ != e_)                                                           \
      report_failure(__FILE__, __LINE__,                                    \
                     std::string(#actual) + " is " + name(a_) +             \
                         ", expected " + name(e_));                         \
  } while (0)

Detection box(uint8_t cls, float score = 0.9f, float cx = 0.5f, float cy = 0.5f) {
  return {true, cls, score, cx, cy};
}

Detection no_box() { return {false, 0, 0.0f, 0.0f, 0.0f}; }

// Feeds frames at a fixed rate and records every reported change.
class Rig {
 public:
  explicit Rig(uint32_t start_ms = 10000) : now_(start_ms) {}

  // Sends one frame at the current time, then advances one frame period.
  bool frame(const Detection& det) {
    Event ev{};
    const bool changed = deb_.update(det, now_, ev);
    last_frame_ms_ = now_;
    now_ += kFrameMs;
    if (changed) {
      ++events;
      last = ev;
    }
    return changed;
  }

  bool frame_at(const Detection& det, uint32_t t) {
    now_ = t;
    return frame(det);
  }

  // Sends `n` identical frames and returns how many changes they reported.
  int frames(const Detection& det, int n) {
    const int before = events;
    for (int i = 0; i < n; ++i) frame(det);
    return events - before;
  }

  uint32_t now() const { return now_; }
  uint32_t last_frame_ms() const { return last_frame_ms_; }
  Id current() const { return deb_.current(); }

  int events = 0;
  Event last{Id::None, 0.0f, 0.0f, 0.0f};

 private:
  Debouncer deb_{Config{}};
  uint32_t now_;
  uint32_t last_frame_ms_ = 0;
};

// --- Basics -----------------------------------------------------------------

void test_starts_as_none() {
  Rig rig;
  CHECK_ID(rig.current(), Id::None);
  CHECK(rig.frames(no_box(), 100) == 0);
  CHECK_ID(rig.current(), Id::None);
}

void test_five_matching_frames_confirm_once() {
  Rig rig;
  CHECK(rig.frames(box(kRock), 4) == 0);
  CHECK_ID(rig.current(), Id::None);
  CHECK(rig.frame(box(kRock, 0.87f, 0.25f, 0.75f)));
  CHECK_ID(rig.last.gesture, Id::Rock);
  CHECK(rig.last.confidence == 0.87f);
  CHECK(rig.last.cx == 0.25f);
  CHECK(rig.last.cy == 0.75f);
  CHECK_ID(rig.current(), Id::Rock);
  // Holding the gesture reports nothing more.
  CHECK(rig.frames(box(kRock), 200) == 0);
  CHECK(rig.events == 1);
}

void test_model_classes_map_to_gestures() {
  const struct {
    uint8_t cls;
    Id expected;
  } cases[] = {{0, Id::Paper}, {1, Id::Rock}, {2, Id::Scissors}};
  for (const auto& c : cases) {
    Rig rig;
    CHECK(rig.frames(box(c.cls), 5) == 1);
    CHECK_ID(rig.last.gesture, c.expected);
  }
}

// --- Flicker ----------------------------------------------------------------

void test_flicker_never_confirms() {
  Rig rig;
  const uint8_t pattern[] = {kRock, kPaper, kRock, kScissors, kPaper, kPaper, kRock};
  for (int rep = 0; rep < 30; ++rep) {
    for (uint8_t cls : pattern) rig.frame(box(cls));
  }
  CHECK(rig.events == 0);
  CHECK_ID(rig.current(), Id::None);
}

void test_runs_of_four_never_confirm() {
  Rig rig;
  for (int rep = 0; rep < 30; ++rep) {
    rig.frames(box(kRock), 4);
    rig.frame(box(kPaper));
  }
  CHECK(rig.events == 0);
  CHECK_ID(rig.current(), Id::None);
}

void test_flicker_keeps_confirmed_gesture() {
  Rig rig;
  rig.frames(box(kRock), 5);
  for (int rep = 0; rep < 30; ++rep) {
    rig.frames(box(kPaper), 4);
    rig.frame(box(kScissors));
  }
  CHECK(rig.events == 1);
  CHECK_ID(rig.current(), Id::Rock);
}

// --- Low scores -------------------------------------------------------------

void test_low_scores_never_confirm() {
  Rig rig;
  // Scores arrive as 0-100 and the sketch divides by 100.
  CHECK(rig.frames(box(kRock, 59 / 100.0f), 100) == 0);
  CHECK_ID(rig.current(), Id::None);
}

void test_threshold_score_confirms() {
  Rig rig;
  CHECK(rig.frames(box(kScissors, 60 / 100.0f), 5) == 1);
  CHECK_ID(rig.current(), Id::Scissors);
}

void test_low_score_frames_act_like_missing_frames() {
  Rig rig;
  rig.frames(box(kRock), 4);
  // Unsure frames of another class neither count nor break the run.
  CHECK(rig.frames(box(kPaper, 0.30f), 3) == 0);
  CHECK(rig.frame(box(kRock)));
  CHECK_ID(rig.current(), Id::Rock);
}

void test_low_scores_alone_time_out() {
  Rig rig;
  rig.frames(box(kRock), 5);
  // Hand still in view but the model is unsure: after 500 ms that's no hand.
  CHECK(rig.frames(box(kRock, 0.40f), 20) == 1);
  CHECK_ID(rig.last.gesture, Id::None);
}

// --- Missed frames ----------------------------------------------------------

void test_single_missed_frame_keeps_streak() {
  Rig rig;
  rig.frames(box(kRock), 4);
  CHECK(!rig.frame(no_box()));  // a missed frame doesn't count toward 5
  CHECK(rig.frame(box(kRock)));
  CHECK_ID(rig.current(), Id::Rock);
}

void test_single_missed_frames_keep_confirmed_gesture() {
  Rig rig;
  rig.frames(box(kPaper), 5);
  for (int rep = 0; rep < 50; ++rep) {
    rig.frames(box(kPaper), 3);
    rig.frame(no_box());
  }
  CHECK(rig.events == 1);
  CHECK_ID(rig.current(), Id::Paper);
}

void test_dropout_up_to_timeout_keeps_streak() {
  Rig rig;
  rig.frames(box(kRock), 4);
  const uint32_t seen = rig.last_frame_ms();
  rig.frame_at(no_box(), seen + 250);
  rig.frame_at(no_box(), seen + 499);
  CHECK(rig.frame_at(box(kRock), seen + 500));
}

void test_long_gap_breaks_partial_streak() {
  Rig rig;
  rig.frames(box(kRock), 3);
  rig.frame_at(no_box(), rig.last_frame_ms() + 501);
  CHECK(rig.frames(box(kRock), 4) == 0);  // 3 + 4 across the gap aren't consecutive
  CHECK(rig.frame(box(kRock)));           // a fresh run of 5 is
}

void test_gap_without_any_frames_breaks_partial_streak() {
  Rig rig;
  rig.frames(box(kRock), 3);
  // Camera stalled, so update() wasn't called at all for 2 s.
  rig.frame_at(box(kRock), rig.last_frame_ms() + 2000);
  CHECK(rig.frames(box(kRock), 3) == 0);
  CHECK(rig.frame(box(kRock)));
}

// --- Timeout ----------------------------------------------------------------

void test_timeout_reports_none_once() {
  Rig rig;
  rig.frames(box(kRock), 5);
  const uint32_t seen = rig.last_frame_ms();
  for (uint32_t t = seen + kFrameMs; t < seen + 500; t += kFrameMs) {
    CHECK(!rig.frame_at(no_box(), t));
  }
  CHECK(!rig.frame_at(no_box(), seen + 500));
  CHECK_ID(rig.current(), Id::Rock);

  CHECK(rig.frame_at(no_box(), seen + 501));
  CHECK_ID(rig.last.gesture, Id::None);
  CHECK(rig.last.confidence == 0.0f);
  CHECK(rig.last.cx == 0.0f);
  CHECK(rig.last.cy == 0.0f);
  CHECK_ID(rig.current(), Id::None);

  // Ten more seconds of nothing: still reported only once.
  CHECK(rig.frames(no_box(), 300) == 0);
  CHECK(rig.events == 2);

  CHECK(rig.frames(box(kRock), 5) == 1);
  CHECK_ID(rig.current(), Id::Rock);
}

// --- Switching --------------------------------------------------------------

void test_switching_gestures() {
  Rig rig;
  CHECK(rig.frames(box(kRock), 5) == 1);
  CHECK(rig.frames(box(kPaper), 4) == 0);
  CHECK_ID(rig.current(), Id::Rock);

  // Goes straight to paper, with no NONE in between.
  CHECK(rig.frame(box(kPaper, 0.8f, 0.3f, 0.6f)));
  CHECK_ID(rig.last.gesture, Id::Paper);
  CHECK(rig.last.confidence == 0.8f);
  CHECK(rig.last.cx == 0.3f);
  CHECK(rig.last.cy == 0.6f);

  CHECK(rig.frames(box(kScissors), 5) == 1);
  CHECK_ID(rig.last.gesture, Id::Scissors);
  CHECK(rig.frames(box(kRock), 5) == 1);
  CHECK_ID(rig.last.gesture, Id::Rock);
  CHECK(rig.events == 4);
}

void test_returning_to_same_gesture_is_not_a_change() {
  Rig rig;
  rig.frames(box(kRock), 5);
  rig.frames(box(kPaper), 3);
  CHECK(rig.frames(box(kRock), 20) == 0);
  CHECK(rig.events == 1);
  CHECK_ID(rig.current(), Id::Rock);
}

// --- Unknown classes --------------------------------------------------------

void test_unknown_classes_never_report_from_none() {
  Rig rig;
  const uint8_t unknown[] = {3, 4, 17, 254, 255};
  for (uint8_t cls : unknown) rig.frames(box(cls), 10);
  CHECK(rig.events == 0);
  CHECK_ID(rig.current(), Id::None);
}

void test_unknown_class_confirms_none() {
  Rig rig;
  rig.frames(box(kScissors), 5);
  CHECK(rig.frames(box(3), 4) == 0);
  CHECK_ID(rig.current(), Id::Scissors);
  CHECK(rig.frame(box(3)));
  CHECK_ID(rig.last.gesture, Id::None);
  CHECK_ID(rig.current(), Id::None);
}

void test_unknown_class_breaks_streak() {
  Rig rig;
  rig.frames(box(kRock), 4);
  rig.frame(box(7));  // a real detection, unlike a missed frame
  CHECK(rig.frames(box(kRock), 4) == 0);
  CHECK(rig.frame(box(kRock)));
}

// --- millis() wraparound ----------------------------------------------------

void test_confirm_across_wraparound() {
  Rig rig(UINT32_MAX - 2 * kFrameMs);
  CHECK(rig.frames(box(kRock), 4) == 0);
  CHECK(rig.frame(box(kRock)));
  CHECK(rig.last_frame_ms() < 1000);  // the clock really wrapped
}

void test_timeout_across_wraparound() {
  Rig rig(UINT32_MAX - 200);
  rig.frames(box(kPaper), 5);
  const uint32_t seen = rig.last_frame_ms();
  const uint32_t after_wrap = seen + 100;
  CHECK(after_wrap < seen);
  CHECK(!rig.frame_at(no_box(), after_wrap));
  CHECK(!rig.frame_at(no_box(), seen + 500));
  CHECK_ID(rig.current(), Id::Paper);
  CHECK(rig.frame_at(no_box(), seen + 501));
  CHECK_ID(rig.last.gesture, Id::None);
  CHECK(rig.frames(no_box(), 100) == 0);
}

void test_steady_stream_across_wraparound() {
  Rig rig(UINT32_MAX - 1000);
  rig.frames(box(kRock), 5);
  for (int rep = 0; rep < 30; ++rep) {
    rig.frames(box(kRock), 2);
    rig.frame(no_box());
  }
  CHECK(rig.now() < 5000);
  CHECK(rig.events == 1);
  CHECK_ID(rig.current(), Id::Rock);
}

struct TestCase {
  const char* name;
  void (*fn)();
};

}  // namespace

int main() {
  const TestCase tests[] = {
      {"starts as none", test_starts_as_none},
      {"five matching frames confirm once", test_five_matching_frames_confirm_once},
      {"model classes map to gestures", test_model_classes_map_to_gestures},
      {"flicker never confirms", test_flicker_never_confirms},
      {"runs of four never confirm", test_runs_of_four_never_confirm},
      {"flicker keeps confirmed gesture", test_flicker_keeps_confirmed_gesture},
      {"low scores never confirm", test_low_scores_never_confirm},
      {"threshold score confirms", test_threshold_score_confirms},
      {"low-score frames act like missing frames", test_low_score_frames_act_like_missing_frames},
      {"low scores alone time out", test_low_scores_alone_time_out},
      {"single missed frame keeps streak", test_single_missed_frame_keeps_streak},
      {"single missed frames keep confirmed gesture", test_single_missed_frames_keep_confirmed_gesture},
      {"dropout up to timeout keeps streak", test_dropout_up_to_timeout_keeps_streak},
      {"long gap breaks partial streak", test_long_gap_breaks_partial_streak},
      {"gap without any frames breaks partial streak", test_gap_without_any_frames_breaks_partial_streak},
      {"timeout reports none once", test_timeout_reports_none_once},
      {"switching gestures", test_switching_gestures},
      {"returning to same gesture is not a change", test_returning_to_same_gesture_is_not_a_change},
      {"unknown classes never report from none", test_unknown_classes_never_report_from_none},
      {"unknown class confirms none", test_unknown_class_confirms_none},
      {"unknown class breaks streak", test_unknown_class_breaks_streak},
      {"confirm across millis() wraparound", test_confirm_across_wraparound},
      {"timeout across millis() wraparound", test_timeout_across_wraparound},
      {"steady stream across millis() wraparound", test_steady_stream_across_wraparound},
  };

  int failed = 0;
  for (const TestCase& t : tests) {
    const int before = g_failures;
    g_detail.clear();
    t.fn();
    const bool ok = g_failures == before;
    if (!ok) ++failed;
    std::printf("%s  %s\n%s", ok ? "PASS" : "FAIL", t.name, g_detail.c_str());
  }

  const int total = static_cast<int>(sizeof tests / sizeof tests[0]);
  std::printf("\n%d of %d tests passed, %d checks\n", total - failed, total, g_checks);
  return failed == 0 ? 0 : 1;
}
