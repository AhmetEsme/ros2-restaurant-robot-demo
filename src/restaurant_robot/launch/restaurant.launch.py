from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    params_file = os.path.join(
    get_package_share_directory('restaurant_robot'),
    'config',
    'params.yaml'
)
    return LaunchDescription([
    Node(package='turtlesim', executable='turtlesim_node'),
    Node(package='restaurant_robot', executable='robot_controller'),
    Node(package='restaurant_robot', executable='table_status_publisher'),
    Node(package='restaurant_robot', executable='order_manager', parameters=[params_file]),
    Node(package='restaurant_robot', executable='monitor'),
])