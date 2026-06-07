import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class Monitor(Node):
    def __init__(self):
        super().__init__('monitor')
        self.subscription_ = self.create_subscription(
            String,
            'delivery_status',
            self.listener_callback,
            10  # QoS queue size
        )
        self.get_logger().info('Monitor started')

    def listener_callback(self, msg):
        self.get_logger().info(f'Received: {msg.data}')


def main(args=None):
    rclpy.init(args=args)
    node = Monitor()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()