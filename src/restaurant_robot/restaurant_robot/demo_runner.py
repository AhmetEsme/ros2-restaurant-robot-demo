import rclpy
from rclpy.node import Node
from restaurant_robot_interfaces.srv import OrderCommand
from std_msgs.msg import String


class DemoRunner(Node):
    def __init__(self):
        super().__init__('demo_runner')
        self.tables = [1, 2, 3, 4, 5]
        self.current_index = 0
        self._pending_timer = None
        self.client_ = self.create_client(OrderCommand, 'order_command')
        self.delivery_sub_ = self.create_subscription(
            String, 'delivery_status', self.on_delivery, 10)
        while not self.client_.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for order_command service...')
        self.get_logger().info('Demo Runner started — visiting tables 1, 2, 3, 4, 5\nデモ開始 — テーブル1, 2, 3, 4, 5 を順番に訪問')
        self.send_next_order()

    def send_next_order(self):
        if self.current_index >= len(self.tables):
            self.get_logger().info('Demo complete! / デモ完了！')
            return
        table = self.tables[self.current_index]
        req = OrderCommand.Request()
        req.command = 'add_order'
        req.table_number = table
        self.get_logger().info(f'>>> Table {table} / テーブル {table} に注文送信')
        future = self.client_.call_async(req)
        future.add_done_callback(lambda f: self.get_logger().info(f'Accepted: {f.result().message}'))

    def on_delivery(self, msg):
        self.get_logger().info(f'Delivered: {msg.data}')
        self.current_index += 1
        if self.current_index < len(self.tables):
            self._pending_timer = self.create_timer(3.0, self._on_timer)
        else:
            self.get_logger().info('All 3 tables done! / 全テーブル配達完了！')

    def _on_timer(self):
        if self._pending_timer:
            self._pending_timer.cancel()
            self._pending_timer = None
        self.send_next_order()


def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(DemoRunner())
