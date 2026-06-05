import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point


class RobotController(Node):
    def __init__(self):
        super().__init__('robot_controller')
        self.subscription_ = self.create_subscription(
            Point,
            'goal_position',
            self.listener_callback,
            10  # QoS queue size
        )
        self.get_logger().info('Subscriber started')

    def listener_callback(self, msg):
        self.get_logger().info(f'Received goal: x={msg.x}, y={msg.y}')


def main(args=None):
    rclpy.init(args=args)
    node = RobotController()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()