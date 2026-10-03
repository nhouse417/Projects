#pragma once

// AT client for the Grove Vision AI V2 over UART1 (migration step M4).
//
// vision_task starts continuous inference, frames each reply (\r ... \n), parses
// the boxes with cJSON, and logs the best one so it can be compared against v1
// for the same hand. The shared debouncer, the event queue, and micro-ROS
// publishing are wired in on top of this in M5.
void vision_task(void *arg);
