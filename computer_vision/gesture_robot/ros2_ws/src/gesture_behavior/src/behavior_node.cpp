#include <chrono>
#include <cstdint>
#include <map>
#include <memory>
#include <string>

#include "geometry_msgs/msg/twist.hpp"
#include "gesture_msgs/msg/gesture.hpp"
#include "rclcpp/rclcpp.hpp"

using namespace std::chrono_literals;
using gesture_msgs::msg::Gesture;

// Subscribes to /gesture/event, holds the active gesture, and drives a robot:
//  - a 10 Hz timer publishes the active gesture's velocity on cmd_vel_topic,
//  - a 5 Hz watchdog drops the active gesture to NONE (stop) when messages stop.
// The velocity mapping and topic come from a per-robot YAML, so the same code
// drives turtlesim and, later, TurtleBot3.
class GestureBehavior : public rclcpp::Node {
 public:
  GestureBehavior() : Node("gesture_behavior") {
    cmd_vel_topic_ =
        declare_parameter<std::string>("cmd_vel_topic", "/turtle1/cmd_vel");
    watchdog_timeout_s_ = declare_parameter<double>("watchdog_timeout_s", 2.0);
    vel_[Gesture::PAPER] = load_velocity("paper");
    vel_[Gesture::ROCK] = load_velocity("rock");
    vel_[Gesture::SCISSORS] = load_velocity("scissors");

    cmd_pub_ = create_publisher<geometry_msgs::msg::Twist>(cmd_vel_topic_, 10);

    rclcpp::QoS qos(10);
    qos.reliable();
    sub_ = create_subscription<Gesture>(
        "/gesture/event", qos,
        std::bind(&GestureBehavior::on_gesture, this, std::placeholders::_1));

    last_msg_time_ = now();
    watchdog_timer_ =
        create_wall_timer(200ms, std::bind(&GestureBehavior::on_watchdog, this));
    velocity_timer_ =
        create_wall_timer(100ms, std::bind(&GestureBehavior::on_velocity, this));

    RCLCPP_INFO(get_logger(), "gesture_behavior up: cmd_vel_topic=%s watchdog=%.1fs",
                cmd_vel_topic_.c_str(), watchdog_timeout_s_);
  }

 private:
  struct Velocity {
    double linear = 0.0;
    double angular = 0.0;
  };

  Velocity load_velocity(const std::string& name) {
    Velocity v;
    v.linear = declare_parameter<double>("velocities." + name + ".linear", 0.0);
    v.angular = declare_parameter<double>("velocities." + name + ".angular", 0.0);
    return v;
  }

  void on_gesture(const Gesture::SharedPtr msg) {
    last_msg_time_ = now();  // any message, including a heartbeat, feeds the watchdog
    if (msg->gesture != active_gesture_) {
      active_gesture_ = msg->gesture;
      RCLCPP_INFO(get_logger(), "gesture -> %u", active_gesture_);
    }
  }

  void on_watchdog() {
    const double since = (now() - last_msg_time_).seconds();
    if (since > watchdog_timeout_s_ && active_gesture_ != Gesture::NONE) {
      RCLCPP_WARN(get_logger(),
                  "watchdog: no gesture for %.1fs, stopping robot", since);
      active_gesture_ = Gesture::NONE;
    }
  }

  void on_velocity() {
    geometry_msgs::msg::Twist twist;  // zero-initialized: NONE and unknown stop
    auto it = vel_.find(active_gesture_);
    if (it != vel_.end()) {
      twist.linear.x = it->second.linear;
      twist.angular.z = it->second.angular;
    }
    cmd_pub_->publish(twist);
  }

  std::string cmd_vel_topic_;
  double watchdog_timeout_s_;
  std::map<uint8_t, Velocity> vel_;
  uint8_t active_gesture_ = Gesture::NONE;
  rclcpp::Time last_msg_time_;
  rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr cmd_pub_;
  rclcpp::Subscription<Gesture>::SharedPtr sub_;
  rclcpp::TimerBase::SharedPtr watchdog_timer_;
  rclcpp::TimerBase::SharedPtr velocity_timer_;
};

int main(int argc, char** argv) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<GestureBehavior>());
  rclcpp::shutdown();
  return 0;
}
