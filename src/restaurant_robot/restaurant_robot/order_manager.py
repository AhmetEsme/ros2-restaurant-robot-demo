import rclpy
from rclpy.node import Node
from restaurant_robot_interfaces.srv import OrderCommand
from geometry_msgs.msg import Point


class OrderManager(Node):
    def __init__(self):
        super().__init__('order_manager')
        self.server_ = self.create_service(
            OrderCommand,
            'order_command',
            self.callback_service
        )
        self.goal_pub_ = self.create_publisher(Point, '/goal_position', 10)
        self.get_logger().info('Service server started')

    def callback_service(self, request, response):
        if request.command == 'add_order':
            point = Point()
            point.x = float(request.table_number)
            point.y = float(request.table_number)
            self.goal_pub_.publish(point)
            response.success = True
            response.message = f'Order sent to table {request.table_number}'
        else:
            response.success = False
            response.message = 'Unknown command'
        self.get_logger().info(response.message)
        return response
        


def main(args=None):
    rclpy.init(args=args)
    node = OrderManager()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()