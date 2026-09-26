"""One launch file for the whole v1 stack.

Phase 3 covers the serial transport and turtlesim. Phase 4 adds the hand,
shown in RViz2 with ros2_control mock hardware; the same model moves to
Gazebo (use_gazebo:=true) and TurtleBot3 joins it later in phase 4. The
micro-ROS agent (transport:=microros) is added in phase 5.
"""
from launch import LaunchDescription
from launch.actions import (
    AppendEnvironmentVariable,
    DeclareLaunchArgument,
    IncludeLaunchDescription,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    AndSubstitution,
    Command,
    EnvironmentVariable,
    EqualsSubstitution,
    FindExecutable,
    LaunchConfiguration,
    NotSubstitution,
    PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    transport = LaunchConfiguration('transport')
    port = LaunchConfiguration('port')
    robot = LaunchConfiguration('robot')
    use_gazebo = LaunchConfiguration('use_gazebo')
    is_hand = EqualsSubstitution(robot, 'hand')
    # The hand runs one of two backends: ros2_control mock hardware in RViz
    # (stage A), or gz_ros2_control inside Gazebo (stage B). robot_state_publisher
    # and the controller spawners are shared; only the controller-manager host,
    # the visualizer, and the Gazebo-only nodes differ.
    hand_rviz = AndSubstitution(is_hand, NotSubstitution(use_gazebo))
    hand_gazebo = AndSubstitution(is_hand, use_gazebo)
    # In Gazebo everything runs on the simulation clock. RViz is the viewer in
    # both stages: Gazebo Harmonic's own GUI renderer is unreliable on macOS
    # (OGRE/Metal in the conda build), so RViz shows the hand even in stage B,
    # driven by the same controllers.
    use_sim_time = ParameterValue(use_gazebo, value_type=bool)

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
    # use_gazebo flows into xacro so the URDF picks gz_ros2_control vs mock
    # hardware and includes the Gazebo plugin block only when true.
    robot_description = ParameterValue(
        Command([
            FindExecutable(name='xacro'), ' ',
            PathJoinSubstitution([
                FindPackageShare('gesture_sim'), 'urdf', 'simple_hand.urdf.xacro',
            ]),
            ' use_gazebo:=', use_gazebo,
        ]),
        value_type=str,
    )

    # Shared by both hand stages.
    robot_state_publisher = Node(
        package='robot_state_publisher', executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[{'robot_description': robot_description,
                     'use_sim_time': use_sim_time}],
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

    # Stage A only (RViz + mock hardware): a standalone controller manager, since
    # nothing else hosts one. In Gazebo the gz_ros2_control plugin is the manager.
    controller_manager = Node(
        package='controller_manager', executable='ros2_control_node',
        parameters=[
            {'robot_description': robot_description},
            PathJoinSubstitution([
                FindPackageShare('gesture_sim'), 'config', 'hand_controllers.yaml',
            ]),
        ],
        condition=IfCondition(hand_rviz),
    )

    rviz = Node(
        package='rviz2', executable='rviz2', name='rviz2',
        arguments=['-d', PathJoinSubstitution([
            FindPackageShare('gesture_sim'), 'rviz', 'hand.rviz',
        ])],
        parameters=[{'use_sim_time': use_sim_time}],
        condition=IfCondition(is_hand),
    )

    # RoboStack ships the gz_ros2_control system plugin in the conda env's lib
    # dir, but does not put that dir on Gazebo's system-plugin search path, so
    # the server fails to load it and the controller manager never starts. Add
    # it here (portable via CONDA_PREFIX rather than a hardcoded path).
    gz_plugin_path = AppendEnvironmentVariable(
        'GZ_SIM_SYSTEM_PLUGIN_PATH',
        PathJoinSubstitution([EnvironmentVariable('CONDA_PREFIX'), 'lib']),
        condition=IfCondition(hand_gazebo),
    )

    # Stage B only (Gazebo): headless server (GUI is opened separately with
    # `gz sim -g`), then spawn the hand from the robot_description topic. The
    # gz_ros2_control plugin in the URDF brings up the controller manager, which
    # the shared spawners above then populate.
    gz_server = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('ros_gz_sim'), 'launch', 'gz_sim.launch.py',
            ]),
        ]),
        launch_arguments={
            'gz_args': ['-s -r ', PathJoinSubstitution([
                FindPackageShare('gesture_sim'), 'worlds', 'hand_world.sdf',
            ])],
        }.items(),
        condition=IfCondition(hand_gazebo),
    )

    spawn_hand = Node(
        package='ros_gz_sim', executable='create',
        arguments=['-topic', 'robot_description', '-name', 'hand'],
        condition=IfCondition(hand_gazebo),
    )

    # Bridge Gazebo's simulation clock to ROS /clock. Without it, every node
    # running use_sim_time (the controller manager and its controllers) sits
    # waiting for time and the trajectory controller never advances a pose.
    clock_bridge = Node(
        package='ros_gz_bridge', executable='parameter_bridge',
        name='clock_bridge',
        arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
        condition=IfCondition(hand_gazebo),
    )

    return LaunchDescription(args + [
        gz_plugin_path,
        bridge, turtlesim, behavior,
        robot_state_publisher,
        joint_state_broadcaster_spawner, hand_controller_spawner,
        controller_manager, rviz,
        gz_server, spawn_hand, clock_bridge,
    ])
