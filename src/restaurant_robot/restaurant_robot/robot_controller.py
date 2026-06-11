import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point, Twist
from turtlesim.msg import Pose
from std_msgs.msg import String


class RobotController(Node):
    def __init__(self):
        super().__init__('robot_controller')

        self.goal = None
        self.arrived = False

        self.distance_tolerance = 0.15
        self.angle_tolerance = 0.25

        self.max_linear_speed = 1.15
        self.max_angular_speed = 2.0

        self.linear_gain = 0.92
        self.angular_gain = 3.0

        self.goal_sub = self.create_subscription(
            Point,
            'goal_position',
            self.goal_callback,
            10
        )

        self.pose_sub = self.create_subscription(
            Pose,
            '/turtle1/pose',
            self.pose_callback,
            10
        )

        self.cmd_pub = self.create_publisher(
            Twist,
            '/turtle1/cmd_vel',
            10
        )

        self.delivery_pub = self.create_publisher(
            String,
            'delivery_status',
            10
        )

        self.get_logger().info('Professional robot controller started')

    def goal_callback(self, msg):
        self.goal = msg
        self.arrived = False
        self.get_logger().info(
            f'New goal received: x={msg.x:.2f}, y={msg.y:.2f}'
        )

    def normalize_angle(self, angle):
        return math.atan2(math.sin(angle), math.cos(angle))

    def clamp(self, value, min_value, max_value):
        return max(min(value, max_value), min_value)

    def stop_robot(self):
        cmd = Twist()
        self.cmd_pub.publish(cmd)

    def pose_callback(self, pose):
        if self.goal is None:
            self.stop_robot()
            return

        dx = self.goal.x - pose.x
        dy = self.goal.y - pose.y
        distance = math.sqrt(dx * dx + dy * dy)

        if distance <= self.distance_tolerance:
            if not self.arrived:
                self.arrived = True
                self.stop_robot()

                msg = String()
                msg.data = f'Delivered to table at ({self.goal.x}, {self.goal.y})'
                self.delivery_pub.publish(msg)
                self.get_logger().info(msg.data)

                self.goal = None
            return

        angle_to_goal = math.atan2(dy, dx)
        angle_error = self.normalize_angle(angle_to_goal - pose.theta)

        cmd = Twist()

        angular_speed = self.angular_gain * angle_error
        cmd.angular.z = self.clamp(
            angular_speed,
            -self.max_angular_speed,
            self.max_angular_speed
        )

        if abs(angle_error) > self.angle_tolerance:
            cmd.linear.x = 0.0
        else:
            linear_speed = self.linear_gain * distance
            cmd.linear.x = self.clamp(
                linear_speed,
                0.0,
                self.max_linear_speed
            )

        self.cmd_pub.publish(cmd)


def main(args=None):
    rclpy.init(args=args)

    node = RobotController()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.stop_robot()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()