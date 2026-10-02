// Gesture firmware v2 — migration step M3.
//
// Publishes a hard-coded gesture_msgs/Gesture on /gesture/event once per second
// over Wi-Fi (Micro-XRCE-DDS to the agent on the Mac). No camera, debouncer, or
// time sync yet: this step only proves that the custom message is built into
// micro-ROS and arrives downstream with the same fields v1 sends. The AT client
// (M4) and the debouncer, heartbeat, time sync, and reconnection (M5) come next.
//
// Gate: `ros2 topic echo /gesture/event` shows the fields below, at ~1 Hz.

#include <cstdio>
#include <unistd.h>

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_system.h"

#include <uros_network_interfaces.h>
#include <rcl/rcl.h>
#include <rcl/error_handling.h>
#include <rclc/rclc.h>
#include <rclc/executor.h>
#include <rmw_microros/rmw_microros.h>
#include <rosidl_runtime_c/string_functions.h>
#include <gesture_msgs/msg/gesture.h>

#define RCCHECK(fn)                                                            \
  {                                                                            \
    rcl_ret_t rc = (fn);                                                       \
    if (rc != RCL_RET_OK) {                                                    \
      printf("Failed status on line %d: %d. Aborting.\n", __LINE__, (int)rc);  \
      vTaskDelete(NULL);                                                       \
    }                                                                          \
  }
#define RCSOFTCHECK(fn)                                                        \
  {                                                                            \
    rcl_ret_t rc = (fn);                                                       \
    if (rc != RCL_RET_OK) {                                                    \
      printf("Failed status on line %d: %d. Continuing.\n", __LINE__, (int)rc);\
    }                                                                          \
  }

static rcl_publisher_t g_pub;
static gesture_msgs__msg__Gesture g_msg;

static void timer_callback(rcl_timer_t *timer, int64_t) {
  if (timer != NULL) {
    printf("publishing gesture=%u\n", g_msg.gesture);
    RCSOFTCHECK(rcl_publish(&g_pub, &g_msg, NULL));
  }
}

static void micro_ros_task(void *) {
  rcl_allocator_t allocator = rcl_get_default_allocator();
  rclc_support_t support;

  rcl_init_options_t init_options = rcl_get_zero_initialized_init_options();
  RCCHECK(rcl_init_options_init(&init_options, allocator));

  // Static agent address instead of discovery: the Mac's IP and port 8888 are
  // set in menuconfig under "micro-ROS Settings".
  rmw_init_options_t *rmw_options =
      rcl_init_options_get_rmw_init_options(&init_options);
  RCCHECK(rmw_uros_options_set_udp_address(CONFIG_MICRO_ROS_AGENT_IP,
                                           CONFIG_MICRO_ROS_AGENT_PORT,
                                           rmw_options));

  RCCHECK(rclc_support_init_with_options(&support, 0, NULL, &init_options,
                                         &allocator));

  rcl_node_t node;
  RCCHECK(rclc_node_init_default(&node, "gesture_camera", "", &support));

  // Reliable QoS, matching the v1 bridge. Don't make one side best-effort.
  RCCHECK(rclc_publisher_init_default(
      &g_pub, &node, ROSIDL_GET_MSG_TYPE_SUPPORT(gesture_msgs, msg, Gesture),
      "gesture/event"));

  // Allocate the header's frame_id string once, then fill the hard-coded fields.
  // These mirror v1's example line {"g":1,"c":0.87,"x":0.512,"y":0.430}: ROCK,
  // confidence 0.87, box centered just past the middle of the frame. The stamp
  // stays zero until time sync lands in M5.
  gesture_msgs__msg__Gesture__init(&g_msg);
  rosidl_runtime_c__String__assign(&g_msg.header.frame_id, "gesture_camera");
  g_msg.gesture = 1;  // ROCK
  g_msg.confidence = 0.87f;
  g_msg.bbox_cx = 0.512f;
  g_msg.bbox_cy = 0.430f;

  rcl_timer_t timer;
  RCCHECK(rclc_timer_init_default2(&timer, &support, RCL_MS_TO_NS(1000),
                                   timer_callback, true));

  rclc_executor_t executor;
  RCCHECK(rclc_executor_init(&executor, &support.context, 1, &allocator));
  RCCHECK(rclc_executor_add_timer(&executor, &timer));

  for (;;) {
    rclc_executor_spin_some(&executor, RCL_MS_TO_NS(100));
    usleep(10000);
  }

  RCCHECK(rcl_publisher_fini(&g_pub, &node));
  RCCHECK(rcl_node_fini(&node));
  vTaskDelete(NULL);
}

extern "C" void app_main(void) {
  ESP_ERROR_CHECK(uros_network_interface_initialize());

  // The ESP32-C3 is single-core, so this just shares the one core with the
  // Wi-Fi/lwIP tasks; the spin loop yields (usleep) so they aren't starved.
  xTaskCreate(micro_ros_task, "uros_task", CONFIG_MICRO_ROS_APP_STACK, NULL,
              CONFIG_MICRO_ROS_APP_TASK_PRIO, NULL);
}
