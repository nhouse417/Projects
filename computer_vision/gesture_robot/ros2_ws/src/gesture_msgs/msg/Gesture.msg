uint8 PAPER=0
uint8 ROCK=1
uint8 SCISSORS=2
uint8 NONE=255

std_msgs/Header header
uint8 gesture        # one of the constants above
float32 confidence   # 0.0 to 1.0
float32 bbox_cx      # normalized box center, 0.0 to 1.0
float32 bbox_cy
