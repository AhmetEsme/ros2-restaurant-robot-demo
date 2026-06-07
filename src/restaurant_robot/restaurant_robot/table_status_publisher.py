import rclpy
from rclpy.node import Node
from restaurant_robot_interfaces.msg import TableStatus


class TableStatusPublisher(Node):
    def __init__(self):
        super().__init__('table_status_publisher')
        self.publisher_ = self.create_publisher(
            TableStatus,
            'table_status',
            10  # QoS queue size
        )
        self.timer_ = self.create_timer(1.0, self.timer_callback)
        self.get_logger().info('Publisher started')

    def timer_callback(self):
        msg = TableStatus()
        msg.table_number = 1
        msg.status = 'EMPTY'
        self.publisher_.publish(msg)
        self.get_logger().info(f'Table {msg.table_number}: {msg.status}')


def main(args=None):
    rclpy.init(args=args)
    node = TableStatusPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()