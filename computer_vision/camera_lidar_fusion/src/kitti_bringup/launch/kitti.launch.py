"""Play a KITTI bag and show it in RViz2 (image, cloud, TF, GT boxes).

    pixi run ws ros2 launch kitti_bringup kitti.launch.py bag:=bags/kitti_0000
    pixi run ws ros2 launch kitti_bringup kitti.launch.py bag:="/Volumes/Extreme SSD/bags/kitti_0000"

Node launch files include this one for playback and visualization.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    bag = LaunchConfiguration("bag")
    delay = LaunchConfiguration("delay")
    rviz = LaunchConfiguration("rviz")
    rviz_config = PathJoinSubstitution([FindPackageShare("kitti_bringup"), "rviz", "kitti.rviz"])

    return LaunchDescription([
        DeclareLaunchArgument("bag", description="bag folder, e.g. bags/kitti_0000"),
        DeclareLaunchArgument("delay", default_value="2.0",
                              description="seconds to wait before playback, so subscribers are up"),
        DeclareLaunchArgument("rviz", default_value="true", description="start RViz2"),
        ExecuteProcess(cmd=["ros2", "bag", "play", bag, "--delay", delay], output="screen"),
        Node(package="rviz2", executable="rviz2", arguments=["-d", rviz_config],
             condition=IfCondition(rviz)),
    ])
