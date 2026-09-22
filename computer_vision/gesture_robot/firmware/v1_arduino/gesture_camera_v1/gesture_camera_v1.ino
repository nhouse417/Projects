#include <HardwareSerial.h>
#include <Seeed_Arduino_SSCMA.h>
#include "gesture_debouncer.h"

// Boxes come back in the 240x240 preview frame, not the model's 192x192 input.
constexpr float kImgW = 240.0f;
constexpr float kImgH = 240.0f;
constexpr uint32_t kHeartbeatMs = 1000;

// 1 also prints every raw box, to confirm the score scale and the class order.
#define LOG_RAW_BOXES 0

HardwareSerial atSerial(0);  // UART to the Vision AI V2 through the XIAO header
SSCMA AI;
gesture::Debouncer deb(gesture::Config{});
gesture::Event last{gesture::Id::None, 0.0f, 0.0f, 0.0f};
uint32_t lastSentMs = 0;

void emit(const gesture::Event& e) {
  Serial.printf("{\"g\":%u,\"c\":%.2f,\"x\":%.3f,\"y\":%.3f,\"t\":%lu}\n",
                static_cast<unsigned>(e.gesture), e.confidence,
                e.cx, e.cy, static_cast<unsigned long>(millis()));
  lastSentMs = millis();
}

void setup() {
  Serial.begin(115200);
  if (!AI.begin(&atSerial)) Serial.println("SSCMA begin failed");
}

void loop() {
  // The library builds AT+INVOKE=<times>,<!filter>,<filter>, so filter=true
  // sends AT+INVOKE=1,0,1: every frame, no image.
  if (AI.invoke(1, true, false) != 0) return;  // 0 means success

  gesture::Detection det{false, 0, 0.0f, 0.0f, 0.0f};
  for (auto& b : AI.boxes()) {                    // keep the highest-scoring box
#if LOG_RAW_BOXES
    Serial.printf("raw x=%u y=%u w=%u h=%u score=%u target=%u\n", b.x, b.y, b.w,
                  b.h, b.score, b.target);
#endif
    float s = b.score / 100.0f;
    if (!det.valid || s > det.score) {
      // x, y are already the box center.
      det = {true, static_cast<uint8_t>(b.target), s, b.x / kImgW, b.y / kImgH};
    }
  }

  gesture::Event ev;
  if (deb.update(det, millis(), ev)) {
    last = ev;
    emit(last);
  } else if (millis() - lastSentMs >= kHeartbeatMs) {
    emit(last);                                   // heartbeat with current state
  }
}
