// Gesture firmware v2 — migration step M5 (complete v2 firmware).
//
// Two FreeRTOS tasks keep camera parsing and networking apart, so a slow Wi-Fi
// moment never makes the device miss frames:
//   vision_task (at_client.cpp) reads the camera over UART1, runs the shared
//     debouncer, and queues a confirmed gesture event on each change.
//   ros_task (ros_link.cpp) manages the agent connection, publishes queued
//     events immediately over micro-ROS, sends a 1 Hz heartbeat, syncs time, and
//     reconnects if the agent or Wi-Fi drops.
//
// Gate: ros2 topic hz /gesture/event is ~1 Hz at rest, with extra messages on
// each gesture change; the v2 stack drives the robot via transport:=microros.

#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"

#include <uros_network_interfaces.h>

#include "at_client.h"
#include "ros_link.h"
#include "gesture_debouncer.h"

extern "C" void app_main(void) {
  // Confirmed gesture changes flow vision_task -> ros_task over this queue.
  static QueueHandle_t queue = xQueueCreate(10, sizeof(gesture::Event));

  // The camera path runs regardless of Wi-Fi, so start it first.
  xTaskCreate(vision_task, "vision_task", 8192, queue, 5, nullptr);

  // Bring up Wi-Fi (blocks until associated), then start the micro-ROS task.
  ESP_ERROR_CHECK(uros_network_interface_initialize());
  xTaskCreate(ros_task, "ros_task", CONFIG_MICRO_ROS_APP_STACK, queue,
              CONFIG_MICRO_ROS_APP_TASK_PRIO, nullptr);
}
