#include "ros_link.h"

#include <cstdio>

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "esp_timer.h"
#include "esp_system.h"  // esp_restart

#include <rcl/rcl.h>
#include <rcl/error_handling.h>
#include <rclc/rclc.h>
#include <rclc/executor.h>
#include <rmw_microros/rmw_microros.h>
#include <rosidl_runtime_c/string_functions.h>
#include <gesture_msgs/msg/gesture.h>

#include "gesture_debouncer.h"

namespace {

// micro-ROS entities, (re)created on connect and torn down on disconnect so the
// device survives the agent restarting or Wi-Fi dropping.
rcl_allocator_t g_allocator;
rclc_support_t g_support;
rcl_node_t g_node;
rcl_publisher_t g_pub;
rcl_timer_t g_timer;
rclc_executor_t g_executor;
gesture_msgs__msg__Gesture g_msg;  // holds the current state between publishes
QueueHandle_t g_queue = nullptr;
unsigned g_publish_failures = 0;

// Consecutive failed publishes that mean the link is dead. At the 1 Hz heartbeat
// this is ~5 s; the behavior node's 2 s watchdog has already stopped the robot.
constexpr unsigned kMaxPublishFailures = 5;

int64_t millis() { return esp_timer_get_time() / 1000; }

// Stamp with synced agent time and publish the current message. Used both for an
// immediate publish on a confirmed change and for the 1 Hz heartbeat.
void publish_current() {
  const int64_t ns = rmw_uros_epoch_nanos();  // valid after rmw_uros_sync_session
  g_msg.header.stamp.sec = static_cast<int32_t>(ns / 1000000000LL);
  g_msg.header.stamp.nanosec = static_cast<uint32_t>(ns % 1000000000LL);
  // Reliable QoS with a 1-deep stream: once the agent stops ACKing (gone or
  // restarted with a new session), the stream stays full and publishes fail.
  // Consecutive failures are how we detect a dead link; a success clears them.
  if (rcl_publish(&g_pub, &g_msg, nullptr) == RCL_RET_OK) {
    g_publish_failures = 0;
  } else {
    ++g_publish_failures;
  }
}

void set_msg_from_event(const gesture::Event &ev) {
  g_msg.gesture = static_cast<uint8_t>(ev.gesture);
  g_msg.confidence = ev.confidence;
  g_msg.bbox_cx = ev.cx;
  g_msg.bbox_cy = ev.cy;
}

// 1 Hz heartbeat: republish the current state so silence is meaningful to the
// behavior node's watchdog, and a late subscriber learns the state within 1 s.
void heartbeat_cb(rcl_timer_t *timer, int64_t) {
  if (timer != nullptr) publish_current();
}

#define RET_ON_FAIL(fn)                                                        \
  do {                                                                         \
    if ((fn) != RCL_RET_OK) return false;                                      \
  } while (0)

bool create_entities() {
  g_allocator = rcl_get_default_allocator();

  rcl_init_options_t init_options = rcl_get_zero_initialized_init_options();
  RET_ON_FAIL(rcl_init_options_init(&init_options, g_allocator));
  rmw_init_options_t *rmw_options =
      rcl_init_options_get_rmw_init_options(&init_options);
  RET_ON_FAIL(rmw_uros_options_set_udp_address(
      CONFIG_MICRO_ROS_AGENT_IP, CONFIG_MICRO_ROS_AGENT_PORT, rmw_options));

  RET_ON_FAIL(rclc_support_init_with_options(&g_support, 0, nullptr,
                                             &init_options, &g_allocator));
  RET_ON_FAIL(rclc_node_init_default(&g_node, "gesture_camera", "", &g_support));
  // Reliable QoS, matching the v1 bridge. Don't make one side best-effort.
  RET_ON_FAIL(rclc_publisher_init_default(
      &g_pub, &g_node,
      ROSIDL_GET_MSG_TYPE_SUPPORT(gesture_msgs, msg, Gesture), "gesture/event"));
  RET_ON_FAIL(rclc_timer_init_default2(&g_timer, &g_support, RCL_MS_TO_NS(1000),
                                       heartbeat_cb, true));
  g_executor = rclc_executor_get_zero_initialized_executor();
  RET_ON_FAIL(
      rclc_executor_init(&g_executor, &g_support.context, 1, &g_allocator));
  RET_ON_FAIL(rclc_executor_add_timer(&g_executor, &g_timer));

  // Sync device time to the agent so header.stamp is real wall-clock time.
  if (rmw_uros_sync_session(1000) != RMW_RET_OK) {
    printf("ros_link: time sync failed; stamps may be off until reconnect\n");
  }
  return true;
}

}  // namespace

void ros_task(void *arg) {
  g_queue = static_cast<QueueHandle_t>(arg);

  // Allocate the header's frame_id once, and start in the rest state (NONE) so
  // the first heartbeats report "no gesture" until one is confirmed.
  gesture_msgs__msg__Gesture__init(&g_msg);
  rosidl_runtime_c__String__assign(&g_msg.header.frame_id, "gesture_camera");
  g_msg.gesture = static_cast<uint8_t>(gesture::Id::None);

  // Options carrying the agent address, used to ping before a session exists
  // (the plain rmw_uros_ping_agent() has no address pre-session on this
  // component). ping_agent_options opens and closes its own transport per call.
  rcl_init_options_t ping_opts = rcl_get_zero_initialized_init_options();
  if (rcl_init_options_init(&ping_opts, rcl_get_default_allocator()) !=
      RCL_RET_OK) {
    printf("ros_link: failed to init ping options; rebooting\n");
    esp_restart();
  }
  rmw_init_options_t *ping_rmw =
      rcl_init_options_get_rmw_init_options(&ping_opts);
  (void)rmw_uros_options_set_udp_address(CONFIG_MICRO_ROS_AGENT_IP,
                                         CONFIG_MICRO_ROS_AGENT_PORT, ping_rmw);

  // Wait for the agent, probing twice a second.
  int64_t last_ping = 0;
  while (true) {
    if (millis() - last_ping > 500) {
      last_ping = millis();
      if (rmw_uros_ping_agent_options(100, 1, ping_rmw) == RMW_RET_OK) break;
    }
    vTaskDelay(pdMS_TO_TICKS(100));
  }

  if (!create_entities()) {
    printf("ros_link: entity creation failed; rebooting\n");
    esp_restart();
  }
  printf("ros_link: agent connected\n");
  g_publish_failures = 0;

  // Publish confirmed changes and the heartbeat. On a lost link, reboot rather
  // than tearing the session down in place: tearing down a micro-ROS session
  // whose agent has vanished is unreliable on this component, whereas a fresh
  // boot reconnects cleanly (as a power-cycle already demonstrated). esp_restart
  // re-runs app_main -> Wi-Fi -> this task, which waits for the agent again.
  for (;;) {
    gesture::Event ev;
    while (xQueueReceive(g_queue, &ev, 0) == pdTRUE) {
      set_msg_from_event(ev);
      publish_current();
    }
    // Runs the heartbeat timer and paces the loop. With reliable QoS and a
    // 1-deep stream, sustained publish failures mean the agent is gone.
    rclc_executor_spin_some(&g_executor, RCL_MS_TO_NS(50));
    if (g_publish_failures >= kMaxPublishFailures) {
      printf("ros_link: agent lost; rebooting to reconnect\n");
      esp_restart();
    }
  }
}
