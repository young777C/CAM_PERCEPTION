"""示例：启动相机感知桥接节点。

覆盖参数请用 launch 参数语法，例如：
  ros2 launch cam_perception_bridge perception.launch.py \\
    cam_perception_root:=/path/to/CAM_PERCEPTION source:=live
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    root = LaunchConfiguration("cam_perception_root")
    source = LaunchConfiguration("source")
    task = LaunchConfiguration("task")
    topic = LaunchConfiguration("publish_topic")

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "cam_perception_root",
                default_value="",
                description="CAM_PERCEPTION 仓库根目录；空则使用 CAM_PERCEPTION_ROOT 或节点内推断",
            ),
            DeclareLaunchArgument("source", default_value="replay"),
            DeclareLaunchArgument("task", default_value="traffic_sign"),
            DeclareLaunchArgument(
                "publish_topic", default_value="/camera_perception/detections"
            ),
            Node(
                package="cam_perception_bridge",
                executable="cam_perception_node",
                name="cam_perception_bridge",
                output="screen",
                parameters=[
                    {
                        "cam_perception_root": root,
                        "source": source,
                        "task": task,
                        "publish_topic": topic,
                    }
                ],
            ),
        ]
    )
