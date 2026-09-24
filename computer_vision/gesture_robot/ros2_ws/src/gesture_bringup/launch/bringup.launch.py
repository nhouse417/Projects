"""One launch file for the whole v1 stack.

Phase 3 covers the serial transport and turtlesim. Phase 4 adds the hand,
shown in RViz2 with ros2_control mock hardware; the same model moves to
Gazebo (use_gazebo:=true) and TurtleBot3 joins it later in phase 4. The
micro-ROS agent (transport:=microros) is added in phase 5.
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import (
    Command,
    EqualsSubstitution,
    FindExecutable,
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    transport = LaunchConfiguration('transport')
    port = LaunchConfiguration('port')
    robot = LaunchConfiguration('robot')
    is_hand = EqualsSubstitution(robot, 'hand')

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

    # Hand stage A (robot:=hand, no Gazebo yet): robot_state_publisher plus a
    # standalone controller_manager using ros2_control mock hardware, so the
    # gesture_behavior JointTrajectory output has something to drive. Once
    # Gazebo joins in phase 4, these get wrapped in "unless use_gazebo",
    # since Gazebo hosts the controller manager itself through a plugin.
    robot_description = ParameterValue(
        Command([
            FindExecutable(name='xacro'), ' ',
            PathJoinSubstitution([
                FindPackageShare('gesture_sim'), 'urdf', 'simple_hand.urdf.xacro',
            ]),
        ]),
        value_type=str,
    )

    robot_state_publisher = Node(
        package='robot_state_publisher', executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[{'robot_description': robot_description}],
        condition=IfCondition(is_hand),
    )

    controller_manager = Node(
        package='controller_manager', executable='ros2_control_node',
        parameters=[
            {'robot_description': robot_description},
            PathJoinSubstitution([
                FindPackageShare('gesture_sim'), 'config', 'hand_controllers.yaml',
            ]),
        ],
        condition=IfCondition(is_hand),
    )

    joint_state_broadcaster_spawner = Node(
        package='controller_manager', executable='spawner',
        arguments=['joint_state_broadcaster'],
        condition=IfCondition(is_hand),
    )

    hand_controller_spawner = Node(
        package='controller_manager', executable='spawner',
        arguments=['hand_controller'],
        condition=IfCondition(is_hand),
    )

    rviz = Node(
        package='rviz2', executable='rviz2', name='rviz2',
        arguments=['-d', PathJoinSubstitution([
            FindPackageShare('gesture_sim'), 'rviz', 'hand.rviz',
        ])],
        condition=IfCondition(is_hand),
    )

    return LaunchDescription(args + [
        bridge, turtlesim, behavior,
        robot_state_publisher, controller_manager,
        joint_state_broadcaster_spawner, hand_controller_spawner, rviz,
    ])
