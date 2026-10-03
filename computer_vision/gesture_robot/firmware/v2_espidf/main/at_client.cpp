#include "at_client.h"

#include <cstdio>
#include <cstring>
#include <string>

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/uart.h"
#include "esp_timer.h"
#include "cJSON.h"

// Set to 1 to dump every raw JSON reply to the console, to eyeball the wire
// format first; set back to 0 to log the parsed best box, which is what the M4
// gate compares against v1. (Same idea as v1's LOG_RAW_BOXES.)
#define LOG_RAW_REPLIES 0

namespace {

// UART1 to the Vision AI V2 through the XIAO header. The console stays on USB
// (native USB-CDC), so UART1 on these pins never conflicts with it. Same
// physical link and baud as v1, so boxes should match.
constexpr uart_port_t kUart = UART_NUM_1;
constexpr int kTxPin = 21;    // XIAO D6
constexpr int kRxPin = 20;    // XIAO D7
constexpr int kBaud = 921600; // SSCMA default
constexpr int kRxRingBytes = 4096;
constexpr size_t kMaxReply = 4096;

// Boxes report the center in the 240x240 preview frame, not the model's 192x192
// input (confirmed on hardware for v1).
constexpr double kImgW = 240.0;
constexpr double kImgH = 240.0;

// Continuous inference: N_TIMES=-1 (until stopped), DIFFERED=0 (reply every
// frame, so the debouncer sees consecutive frames), RESULT_ONLY=1 (no base64
// image, to keep the link light). This is the raw command v1 builds via the
// library as AT+INVOKE=1,0,1 per frame.
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

// If no bytes arrive for 2 s the camera has usually stopped streaming (it
// happens after a reflash or a USB reconnect). Break and re-arm inference.
void rearm_if_stalled() {
  const int64_t now = esp_timer_get_time();
  if (now - g_last_rx_us < 2000000) return;  // 2 s
  uart_write_bytes(kUart, kBreak, sizeof(kBreak) - 1);
  vTaskDelay(pdMS_TO_TICKS(50));
  start_inference();
  g_last_rx_us = now;  // don't re-break every 50 ms while it recovers
}

void handle_reply(const std::string &line) {
#if LOG_RAW_REPLIES
  printf("%s\n", line.c_str());
#else
  cJSON *root = cJSON_Parse(line.c_str());
  if (root == nullptr) return;

  // Keep only inference events (type 1, name "INVOKE"); the command echo and
  // other replies are ignored.
  const cJSON *type = cJSON_GetObjectItemCaseSensitive(root, "type");
  const cJSON *name = cJSON_GetObjectItemCaseSensitive(root, "name");
  if (!cJSON_IsNumber(type) || type->valueint != 1 || !cJSON_IsString(name) ||
      strcmp(name->valuestring, "INVOKE") != 0) {
    cJSON_Delete(root);
    return;
  }

  const cJSON *data = cJSON_GetObjectItemCaseSensitive(root, "data");
  const cJSON *boxes =
      data ? cJSON_GetObjectItemCaseSensitive(data, "boxes") : nullptr;
  if (!cJSON_IsArray(boxes)) {
    cJSON_Delete(root);
    return;
  }

  // Each box is [x, y, w, h, score, target]: center in the 240x240 frame, score
  // 0-100, target the class index. Keep the highest-scoring one, as v1 does.
  bool have = false;
  int bx = 0, by = 0, bw = 0, bh = 0, bscore = -1, btarget = 0;
  const cJSON *box = nullptr;
  cJSON_ArrayForEach(box, boxes) {
    if (!cJSON_IsArray(box) || cJSON_GetArraySize(box) < 6) continue;
    const int score = static_cast<int>(cJSON_GetArrayItem(box, 4)->valuedouble);
    if (have && score <= bscore) continue;
    have = true;
    bx = static_cast<int>(cJSON_GetArrayItem(box, 0)->valuedouble);
    by = static_cast<int>(cJSON_GetArrayItem(box, 1)->valuedouble);
    bw = static_cast<int>(cJSON_GetArrayItem(box, 2)->valuedouble);
    bh = static_cast<int>(cJSON_GetArrayItem(box, 3)->valuedouble);
    bscore = score;
    btarget = static_cast<int>(cJSON_GetArrayItem(box, 5)->valuedouble);
  }

  if (have) {
    // Left block matches v1's raw-box log; the parenthesised block is what the
    // debouncer will consume in M5 (normalized center, score 0-1).
    printf("box x=%d y=%d w=%d h=%d score=%d target=%d  (cx=%.3f cy=%.3f s=%.2f)\n",
           bx, by, bw, bh, bscore, btarget, bx / kImgW, by / kImgH,
           bscore / 100.0);
  } else {
    printf("no box\n");
  }
  cJSON_Delete(root);
#endif
}

}  // namespace

void vision_task(void *) {
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
    handle_reply(line);  // end of a reply
    line.clear();
  }
}
