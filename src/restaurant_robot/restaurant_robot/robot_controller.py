import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point
from geometry_msgs.msg import Twist
from turtlesim.msg import Pose
from std_msgs.msg import String

class RobotController(Node):
    def __init__(self):
        super().__init__('robot_controller')
        self.subscription_ = self.create_subscription(
            Point,
            'goal_position',
            self.listener_callback,
            10  # QoS queue size
        )
        self.cmd_pub_ = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)
        self.delivery_pub_ = self.create_publisher(String, 'delivery_status', 10)
        self.pose_sub_ = self.create_subscription(Pose, '/turtle1/pose', self.pose_callback, 10)
        self.goal_ = None
        self.get_logger().info('Subscriber started')

    def listener_callback(self, msg):
        self.goal_ = msg
        self.get_logger().info(f'Received goal: x={msg.x}, y={msg.y}')
        
    def pose_callback(self, pose):
        if self.goal_ is None:
            return

        import math
        dx = self.goal_.x - pose.x
        dy = self.goal_.y - pose.y
        distance = math.sqrt(dx*dx + dy*dy)

        cmd = Twist()
        if distance > 0.1:
            angle_to_goal = math.atan2(dy, dx)
            cmd.linear.x = 1.5 * distance
            cmd.angular.z = 6.0 * (angle_to_goal - pose.theta)
        else:
            msg = String()
            msg.data = f'Delivered to table at ({self.goal_.x}, {self.goal_.y})'
            self.delivery_pub_.publish(msg)
            self.get_logger().info(msg.data)
            self.goal_ = None
        self.cmd_pub_.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = RobotController()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()