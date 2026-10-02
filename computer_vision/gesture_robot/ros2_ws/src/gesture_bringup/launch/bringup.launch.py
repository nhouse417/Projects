"""One launch file for the whole stack.

The transport (serial bridge in v1, micro-ROS agent in v2) is chosen with
`transport`, and the robot with `robot`. Phase 3 covers the serial transport and
turtlesim. Phase 4 adds the hand (in RViz2 with mock hardware, or in Gazebo with
gz_ros2_control via use_gazebo:=true) and TurtleBot3 (robot:=turtlebot3, always
in Gazebo). Gazebo's own GUI does not render on macOS, so RViz2 is the viewer for
both Gazebo robots. Phase 5 adds transport:=microros, which starts the micro-ROS
agent (the ESP32-C3 publishes /gesture/event itself over Wi-Fi) instead of the
serial bridge; everything downstream is identical to serial.
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
    OrSubstitution,
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
    is_tb3 = EqualsSubstitution(robot, 'turtlebot3')
    # The hand runs one of two backends: ros2_control mock hardware in RViz
    # (stage A), or gz_ros2_control inside Gazebo (stage B). robot_state_publisher
    # and the controller spawners are shared; only the controller-manager host,
    # the visualizer, and the Gazebo-only nodes differ.
    hand_rviz = AndSubstitution(is_hand, NotSubstitution(use_gazebo))
    hand_gazebo = AndSubstitution(is_hand, use_gazebo)
    # TurtleBot3 only runs in Gazebo, so it implies the sim without use_gazebo.
    gazebo_up = OrSubstitution(hand_gazebo, is_tb3)
    # In Gazebo everything runs on the simulation clock. RViz is the viewer for
    # every Gazebo robot: Gazebo Harmonic's own GUI renderer is unreliable on
    # macOS (OGRE/Metal in the conda build).
    use_sim_time = ParameterValue(OrSubstitution(use_gazebo, is_tb3),
                                  value_type=bool)

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

    # v2 micro-ROS agent: the ESP32-C3 publishes /gesture/event itself over
    # Wi-Fi (XRCE-DDS, UDP 8888), and the agent presents it as a normal ROS 2
    # node. Nothing downstream (behavior, sim) changes between transports.
    agent = Node(
        package='micro_ros_agent', executable='micro_ros_agent',
        name='micro_ros_agent',
        arguments=['udp4', '--port', '8888'],
        condition=IfCondition(EqualsSubstitution(transport, 'microros')),
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

    # Shared headless Gazebo server (its GUI is skipped; RViz is the viewer).
    gz_server = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('ros_gz_sim'), 'launch', 'gz_sim.launch.py',
            ]),
        ]),
        launch_arguments={
            'gz_args': ['-s -r ', PathJoinSubstitution([
                FindPackageShare('gesture_sim'), 'worlds', 'gesture_world.sdf',
            ])],
        }.items(),
        condition=IfCondition(gazebo_up),
    )

    # Hand in Gazebo: spawn from the robot_description topic. The gz_ros2_control
    # plugin in the URDF brings up the controller manager, which the shared
    # spawners above then populate.
    spawn_hand = Node(
        package='ros_gz_sim', executable='create',
        arguments=['-topic', 'robot_description', '-name', 'hand'],
        condition=IfCondition(hand_gazebo),
    )

    # Bridge Gazebo's simulation clock to ROS /clock. Without it, every node
    # running use_sim_time sits waiting for time.
    clock_bridge = Node(
        package='ros_gz_bridge', executable='parameter_bridge',
        name='clock_bridge',
        arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
        condition=IfCondition(gazebo_up),
    )

    # --- TurtleBot3 in Gazebo (robot:=turtlebot3) ---------------------------
    # The Burger's meshes are referenced as model://turtlebot3_common/..., so
    # Gazebo needs the package's models dir on its resource path to find them.
    tb3_resource_path = AppendEnvironmentVariable(
        'GZ_SIM_RESOURCE_PATH',
        PathJoinSubstitution([FindPackageShare('turtlebot3_gazebo'), 'models']),
        condition=IfCondition(is_tb3),
    )

    # Spawn the stock Burger. Its lidar is declared but never renders, because
    # gesture_world omits the sensors system plugin (avoids the macOS crash).
    spawn_burger = Node(
        package='ros_gz_sim', executable='create',
        arguments=[
            '-world', 'gesture_world', '-name', 'burger', '-z', '0.01',
            '-file', PathJoinSubstitution([
                FindPackageShare('turtlebot3_gazebo'),
                'models', 'turtlebot3_burger', 'model.sdf',
            ]),
        ],
        condition=IfCondition(is_tb3),
    )

    # Bridge the Burger's ROS<->gz topics: gesture_behavior's Twist on /cmd_vel
    # drives the DiffDrive plugin; odom, tf, and joint_states come back for RViz.
    tb3_bridge = Node(
        package='ros_gz_bridge', executable='parameter_bridge',
        name='turtlebot3_bridge',
        arguments=[
            '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            '/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
            '/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model',
        ],
        parameters=[{'use_sim_time': use_sim_time}],
        condition=IfCondition(is_tb3),
    )

    # robot_state_publisher + RViz so the Burger is visible (Gazebo GUI is dead
    # on macOS). The URDF ships with turtlebot3_gazebo as a plain file.
    tb3_description = ParameterValue(
        Command([
            'cat ', PathJoinSubstitution([
                FindPackageShare('turtlebot3_gazebo'),
                'urdf', 'turtlebot3_burger.urdf',
            ]),
        ]),
        value_type=str,
    )

    tb3_state_publisher = Node(
        package='robot_state_publisher', executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[{'robot_description': tb3_description,
                     'use_sim_time': use_sim_time}],
        condition=IfCondition(is_tb3),
    )

    tb3_rviz = Node(
        package='rviz2', executable='rviz2', name='rviz2',
        arguments=['-d', PathJoinSubstitution([
            FindPackageShare('gesture_sim'), 'rviz', 'turtlebot3.rviz',
        ])],
        parameters=[{'use_sim_time': use_sim_time}],
        condition=IfCondition(is_tb3),
    )

    return LaunchDescription(args + [
        gz_plugin_path,
        bridge, agent, turtlesim, behavior,
        robot_state_publisher,
        joint_state_broadcaster_spawner, hand_controller_spawner,
        controller_manager, rviz,
        gz_server, spawn_hand, clock_bridge,
        tb3_resource_path, spawn_burger, tb3_bridge,
        tb3_state_publisher, tb3_rviz,
    ])
