// Gesture firmware v2 — migration step M4.
//
// Runs the AT client only: vision_task reads the Grove Vision AI V2 over UART1,
// frames and parses each reply, and logs the best box so it can be compared
// against v1 for the same hand. No Wi-Fi or micro-ROS yet — M3's publisher and
// this camera path are joined by the shared debouncer and an event queue in M5.
//
// Gate: on `idf.py monitor`, the parsed boxes match what v1 reports for the same
// hand in the same lighting.

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "at_client.h"

extern "C" void app_main(void) {
  // cJSON parses onto the heap, but printf with floats and the reply buffer want
  // some stack; 8 KB is comfortable.
  xTaskCreate(vision_task, "vision_task", 8192, nullptr, 5, nullptr);
}
