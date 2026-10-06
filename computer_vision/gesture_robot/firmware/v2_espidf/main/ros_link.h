#pragma once

#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"

// micro-ROS side (migration step M5). ros_task manages the agent connection,
// publishes confirmed gesture events from the queue immediately, and sends a
// 1 Hz heartbeat with the current state. `arg` is a QueueHandle_t carrying
// gesture::Event values produced by vision_task.
void ros_task(void *arg);
