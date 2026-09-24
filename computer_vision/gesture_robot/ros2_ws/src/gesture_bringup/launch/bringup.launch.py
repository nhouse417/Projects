"""One launch file for the whole v1 stack.

Phase 3 covers the serial transport and turtlesim. The micro-ROS agent
(transport:=microros) is added in phase 5, and turtlebot3/hand plus Gazebo in
phase 4; the arguments are declared now so the command line stays stable.
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import (
    EqualsSubstitution,
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    transport = LaunchConfiguration('transport')
    port = LaunchConfiguration('port')
    robot = LaunchConfiguration('robot')

    args = [
        DeclareLaunchArgument('transport', default_value='serial',
                              description='serial or microros'),
        DeclareLaunchArgument('port', default_value='/dev/cu.usbmodem101',
                              description='USB serial port of the camera (v1)'),
        DeclareLaunchArgument('robot', default_value='turtlesim',
                              description='turtlesim, turtlebot3, or hand'),
        DeclareLaunchArgument('use_gazebo', default_value='false'),
    ]

    # v1 serial bridge: publishes /gesture/event from the camera over USB.
    bridge = Node(
        package='gesture_bridge', executable='serial_bridge',
        name='gesture_bridge',
        parameters=[{'port': port}],
        condition=IfCondition(EqualsSubstitution(transport, 'serial')),
    )

    turtlesim = Node(
        package='turtlesim', executable='turtlesim_node', name='turtlesim',
        condition=IfCondition(EqualsSubstitution(robot, 'turtlesim')),
    )

    # Always starts, loading the YAML that matches `robot`.
    behavior = Node(
        package='gesture_behavior', executable='gesture_behavior_node',
        name='gesture_behavior',
        parameters=[PathJoinSubstitution([
            FindPackageShare('gesture_behavior'), 'config', [robot, '.yaml'],
        ])],
    )

    return LaunchDescription(args + [bridge, turtlesim, behavior])
