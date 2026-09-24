#include <chrono>
#include <cstdint>
#include <map>
#include <memory>
#include <string>
#include <vector>

#include "builtin_interfaces/msg/duration.hpp"
#include "geometry_msgs/msg/twist.hpp"
#include "gesture_msgs/msg/gesture.hpp"
#include "rclcpp/rclcpp.hpp"
#include "trajectory_msgs/msg/joint_trajectory.hpp"
#include "trajectory_msgs/msg/joint_trajectory_point.hpp"

using namespace std::chrono_literals;
using gesture_msgs::msg::Gesture;

// Subscribes to /gesture/event and drives either a mobile robot or the hand,
// selected by the `robot` parameter (turtlesim, turtlebot3, or hand):
//  - Twist mode (turtlesim/turtlebot3): a 10 Hz timer publishes the active
//    gesture's velocity on cmd_vel_topic, continuously, so NONE stops it.
//  - JointTrajectory mode (hand): publishes one point on gesture change;
//    NONE holds the last pose instead of moving to a neutral one, since a
//    static hand has no safety reason to react to a lost signal.
// A 5 Hz watchdog drops the active gesture to NONE when messages stop,
// regardless of mode. Mappings come from a per-robot YAML, so the same node
// binary drives every robot.
class GestureBehavior : public rclcpp::Node {
 public:
  GestureBehavior() : Node("gesture_behavior") {
    watchdog_timeout_s_ = declare_parameter<double>("watchdog_timeout_s", 2.0);
    is_hand_ = declare_parameter<std::string>("robot", "turtlesim") == "hand";

    if (is_hand_) {
      setup_hand();
    } else {
      setup_twist();
    }

    rclcpp::QoS qos(10);
    qos.reliable();
    sub_ = create_subscription<Gesture>(
        "/gesture/event", qos,
        std::bind(&GestureBehavior::on_gesture, this, std::placeholders::_1));

    last_msg_time_ = now();
    watchdog_timer_ =
        create_wall_timer(200ms, std::bind(&GestureBehavior::on_watchdog, this));

    RCLCPP_INFO(get_logger(), "gesture_behavior up: robot=%s watchdog=%.1fs",
                is_hand_ ? "hand" : "twist", watchdog_timeout_s_);
  }

 private:
  struct Velocity {
    double linear = 0.0;
    double angular = 0.0;
  };

  void setup_twist() {
    cmd_vel_topic_ =
        declare_parameter<std::string>("cmd_vel_topic", "/turtle1/cmd_vel");
    vel_[Gesture::PAPER] = load_velocity("paper");
    vel_[Gesture::ROCK] = load_velocity("rock");
    vel_[Gesture::SCISSORS] = load_velocity("scissors");
    cmd_pub_ = create_publisher<geometry_msgs::msg::Twist>(cmd_vel_topic_, 10);
    velocity_timer_ =
        create_wall_timer(100ms, std::bind(&GestureBehavior::on_velocity, this));
  }

  void setup_hand() {
    joint_trajectory_topic_ = declare_parameter<std::string>(
        "joint_trajectory_topic", "/hand_controller/joint_trajectory");
    move_time_s_ = declare_parameter<double>("move_time_s", 0.8);
    joint_names_ = declare_parameter<std::vector<std::string>>("joint_names", {});
    positions_[Gesture::PAPER] = load_positions("paper");
    positions_[Gesture::ROCK] = load_positions("rock");
    positions_[Gesture::SCISSORS] = load_positions("scissors");
    joint_pub_ = create_publisher<trajectory_msgs::msg::JointTrajectory>(
        joint_trajectory_topic_, 10);
  }

  Velocity load_velocity(const std::string& name) {
    Velocity v;
    v.linear = declare_parameter<double>("velocities." + name + ".linear", 0.0);
    v.angular = declare_parameter<double>("velocities." + name + ".angular", 0.0);
    return v;
  }

  std::vector<double> load_positions(const std::string& name) {
    return declare_parameter<std::vector<double>>("positions." + name,
                                                    std::vector<double>{});
  }

  void on_gesture(const Gesture::SharedPtr msg) {
    last_msg_time_ = now();  // any message, including a heartbeat, feeds the watchdog
    if (msg->gesture != active_gesture_) {
      active_gesture_ = msg->gesture;
      RCLCPP_INFO(get_logger(), "gesture -> %u", active_gesture_);
      if (is_hand_ && active_gesture_ != Gesture::NONE) {
        publish_joint_trajectory();
      }
    }
  }

  void on_watchdog() {
    const double since = (now() - last_msg_time_).seconds();
    if (since > watchdog_timeout_s_ && active_gesture_ != Gesture::NONE) {
      RCLCPP_WARN(get_logger(),
                  "watchdog: no gesture for %.1fs, stopping robot", since);
      active_gesture_ = Gesture::NONE;  // hand mode: holds the last published pose
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

  void publish_joint_trajectory() {
    auto it = positions_.find(active_gesture_);
    if (it == positions_.end()) return;

    trajectory_msgs::msg::JointTrajectory traj;
    traj.joint_names = joint_names_;
    trajectory_msgs::msg::JointTrajectoryPoint point;
    point.positions = it->second;
    point.time_from_start.sec = static_cast<int32_t>(move_time_s_);
    point.time_from_start.nanosec = static_cast<uint32_t>(
        (move_time_s_ - point.time_from_start.sec) * 1e9);
    traj.points.push_back(point);
    joint_pub_->publish(traj);
  }

  bool is_hand_ = false;
  double watchdog_timeout_s_;
  uint8_t active_gesture_ = Gesture::NONE;
  rclcpp::Time last_msg_time_;
  rclcpp::Subscription<Gesture>::SharedPtr sub_;
  rclcpp::TimerBase::SharedPtr watchdog_timer_;

  // Twist mode (turtlesim, turtlebot3)
  std::string cmd_vel_topic_;
  std::map<uint8_t, Velocity> vel_;
  rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr cmd_pub_;
  rclcpp::TimerBase::SharedPtr velocity_timer_;

  // JointTrajectory mode (hand)
  std::string joint_trajectory_topic_;
  double move_time_s_ = 0.8;
  std::vector<std::string> joint_names_;
  std::map<uint8_t, std::vector<double>> positions_;
  rclcpp::Publisher<trajectory_msgs::msg::JointTrajectory>::SharedPtr joint_pub_;
};

int main(int argc, char** argv) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<GestureBehavior>());
  rclcpp::shutdown();
  return 0;
}
