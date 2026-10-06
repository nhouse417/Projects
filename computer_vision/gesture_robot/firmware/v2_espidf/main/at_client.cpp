#include "at_client.h"

#include <cstdio>
#include <cstring>
#include <string>

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "driver/uart.h"
#include "esp_timer.h"
#include "cJSON.h"

#include "gesture_debouncer.h"

// Set to 1 to dump every raw JSON reply to the console instead of running the
// debouncer, to eyeball the wire format. Default 0: parse, debounce, and queue.
#define LOG_RAW_REPLIES 0

namespace {

// UART1 to the Vision AI V2 through the XIAO header. The console stays on USB
// (native USB-CDC), so UART1 on these pins never conflicts with it. Same
// physical link and baud as v1.
constexpr uart_port_t kUart = UART_NUM_1;
constexpr int kTxPin = 21;    // XIAO D6
constexpr int kRxPin = 20;    // XIAO D7
constexpr int kBaud = 921600; // SSCMA default
constexpr int kRxRingBytes = 4096;
constexpr size_t kMaxReply = 4096;

// Boxes report the center in the 240x240 preview frame (confirmed on hardware).
constexpr double kImgW = 240.0;
constexpr double kImgH = 240.0;

// Continuous inference: N_TIMES=-1, DIFFERED=0 (reply every frame, so the
// debouncer sees consecutive frames), RESULT_ONLY=1 (no base64 image).
constexpr char kInvoke[] = "AT+INVOKE=-1,0,1\r";
constexpr char kBreak[] = "AT+BREAK\r";

int64_t g_last_rx_us = 0;

void uart_init() {
  uart_config_t cfg = {};
  cfg.baud_rate = kBaud;
  cfg.data_bits = UART_DATA_8_BITS;
  cfg.parity = UART_PARITY_DISABLE;
  cfg.stop_bits = UART_STOP_BITS_1;
  cfg.flow_ctrl = UART_HW_FLOWCTRL_DISABLE;
  cfg.source_clk = UART_SCLK_DEFAULT;
  ESP_ERROR_CHECK(uart_driver_install(kUart, kRxRingBytes, 0, 0, nullptr, 0));
  ESP_ERROR_CHECK(uart_param_config(kUart, &cfg));
  ESP_ERROR_CHECK(uart_set_pin(kUart, kTxPin, kRxPin, UART_PIN_NO_CHANGE,
                               UART_PIN_NO_CHANGE));
}

void start_inference() { uart_write_bytes(kUart, kInvoke, sizeof(kInvoke) - 1); }

// If no bytes arrive for 2 s the camera has usually stopped streaming (after a
// reflash or USB reconnect). Break and re-arm inference.
void rearm_if_stalled() {
  const int64_t now = esp_timer_get_time();
  if (now - g_last_rx_us < 2000000) return;  // 2 s
  uart_write_bytes(kUart, kBreak, sizeof(kBreak) - 1);
  vTaskDelay(pdMS_TO_TICKS(50));
  start_inference();
  g_last_rx_us = now;  // don't re-break every 50 ms while it recovers
}

// Parse one reply. Returns true if it was an inference event (type 1, name
// "INVOKE") -- i.e. one frame the debouncer should count -- and fills `det` with
// the highest-scoring box (det.valid is false when the frame had no box). Other
// replies (the command echo, etc.) return false and are not counted as frames.
bool parse_event(const std::string &line, gesture::Detection &det) {
  det = {false, 0, 0.0f, 0.0f, 0.0f};

  cJSON *root = cJSON_Parse(line.c_str());
  if (root == nullptr) return false;

  const cJSON *type = cJSON_GetObjectItemCaseSensitive(root, "type");
  const cJSON *name = cJSON_GetObjectItemCaseSensitive(root, "name");
  if (!cJSON_IsNumber(type) || type->valueint != 1 || !cJSON_IsString(name) ||
      strcmp(name->valuestring, "INVOKE") != 0) {
    cJSON_Delete(root);
    return false;
  }

  const cJSON *data = cJSON_GetObjectItemCaseSensitive(root, "data");
  const cJSON *boxes =
      data ? cJSON_GetObjectItemCaseSensitive(data, "boxes") : nullptr;
  if (cJSON_IsArray(boxes)) {
    // Each box is [x, y, w, h, score, target]; keep the highest-scoring one.
    int best_score = -1;
    const cJSON *box = nullptr;
    cJSON_ArrayForEach(box, boxes) {
      if (!cJSON_IsArray(box) || cJSON_GetArraySize(box) < 6) continue;
      const int score =
          static_cast<int>(cJSON_GetArrayItem(box, 4)->valuedouble);
      if (score <= best_score) continue;
      best_score = score;
      det.valid = true;
      det.model_class =
          static_cast<uint8_t>(cJSON_GetArrayItem(box, 5)->valuedouble);
      det.score = static_cast<float>(score) / 100.0f;
      det.cx = static_cast<float>(cJSON_GetArrayItem(box, 0)->valuedouble / kImgW);
      det.cy = static_cast<float>(cJSON_GetArrayItem(box, 1)->valuedouble / kImgH);
    }
  }

  cJSON_Delete(root);
  return true;  // it was an inference frame, box or not
}

}  // namespace

void vision_task(void *arg) {
  QueueHandle_t queue = static_cast<QueueHandle_t>(arg);
  gesture::Debouncer deb{gesture::Config{}};

  uart_init();
  g_last_rx_us = esp_timer_get_time();
  start_inference();

  std::string line;
  uint8_t byte = 0;
  for (;;) {
    if (uart_read_bytes(kUart, &byte, 1, pdMS_TO_TICKS(50)) != 1) {
      rearm_if_stalled();
      continue;
    }
    g_last_rx_us = esp_timer_get_time();
    if (byte == '\r') {  // start of a reply
      line.clear();
      continue;
    }
    if (byte != '\n') {  // body byte
      if (line.size() < kMaxReply) line.push_back(static_cast<char>(byte));
      continue;
    }

    // End of a reply.
#if LOG_RAW_REPLIES
    printf("%s\n", line.c_str());
#else
    gesture::Detection det;
    if (parse_event(line, det)) {
      const uint32_t now_ms = static_cast<uint32_t>(esp_timer_get_time() / 1000);
      gesture::Event ev;
      if (deb.update(det, now_ms, ev)) {
        // Confirmed change: hand it to ros_task to publish. Drop if the queue is
        // full (only happens while the agent is gone; the heartbeat catches up).
        printf("gesture -> %u (conf %.2f)\n", static_cast<unsigned>(ev.gesture),
               ev.confidence);
        xQueueSend(queue, &ev, 0);
      }
    }
#endif
    line.clear();
  }
}
