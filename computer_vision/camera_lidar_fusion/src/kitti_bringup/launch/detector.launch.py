"""
Starts the detector node which publishes annotations from a kitti bag
to RViz2.

    pixi run ws ros2 launch kitti_bringup detector.launch.py bag:=bags/kitti_0000
    pixi run ws ros2 launch kitti_bringup detector.launch.py bag:=bags/kitti_0016 use_coreml:=true

"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    """
    Bag playback and RViz2 from kitti.launch.py, plus the detector node.
    """
    bag = LaunchConfiguration("bag")
    use_coreml = LaunchConfiguration("use_coreml")
    kitti_launch = PathJoinSubstitution(
        [FindPackageShare("kitti_bringup"), "launch", "kitti.launch.py"])
    detector_rviz = PathJoinSubstitution(
        [FindPackageShare("kitti_bringup"), "rviz", "detector.rviz"])

    return LaunchDescription([
        DeclareLaunchArgument("bag", description="bag folder, e.g. bags/kitti_0000"),
        DeclareLaunchArgument("use_coreml", default_value="false",
                              description="run inference through Core ML (macOS only)"),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(kitti_launch),
            launch_arguments={"bag": bag, "rviz_config": detector_rviz}.items()),
        Node(package="detector_cpp", executable="detector_node", output="screen",
             parameters=[{"use_coreml": ParameterValue(use_coreml, value_type=bool)}])
    ])