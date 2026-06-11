# ROS2 RESTAURANT DELIVERY ROBOT — COMPLETE NOTES

---

## GENERAL RULES (ALWAYS APPLY)

**Terminal rule:**
- External terminal (Ctrl+Alt+T): **ONLY for GUI programs** — turtlesim, rqt, rviz, Gazebo
- VS Code integrated terminal: **everything else** — ros2 run, colcon build, source, git, service call, topic echo

**Why?** VS Code terminal conflicts with snap libraries → `symbol lookup error: GLIBC_PRIVATE` error. GUI programs like turtlesim must only run in an external terminal.

**Each terminal is independent.** `source install/setup.bash` must be run in the same terminal where `ros2 run` will be executed. Different terminal → `Package not found` error.

**When to build:**
- `.py`, `.srv`, `.msg`, `package.xml`, `setup.py` changed → **always build**
- Only `params.yaml` changed → no build needed, just restart launch

**Build command:**
```bash
colcon build
source install/setup.bash
```

**Alias:** `restaurant` runs `cd ~/projects/restaurant_robot_ws && source install/setup.bash`. Use:
```bash
restaurant && ros2 launch restaurant_robot restaurant.launch.py
```

---

## VS CODE SHORTCUTS

- **Ctrl+F** → search for a value in a file
- **Ctrl+H** → Find & Replace — find and change a value
- **Insert key** → toggle between OVR/INS mode
  - **INS mode** (normal): typed character is inserted at cursor position
  - **OVR mode**: typed character overwrites the character under cursor — caution!
  - If `OVR` appears in the bottom-right status bar → press Insert to switch back

---

## PROJECT ARCHITECTURE

**Workspace:** `~/projects/restaurant_robot_ws`
**GitHub:** `https://github.com/AhmetEsme/ros2-restaurant-robot-demo`

**2 packages:**
- `restaurant_robot` → ament_python (contains nodes)
- `restaurant_robot_interfaces` → ament_cmake (contains custom msg/srv)

**⚠️ CRITICAL:** Two separate `package.xml` files exist. `rosidl` interface dependency lines go **ONLY** into `restaurant_robot_interfaces` (ament_cmake) `package.xml`. They must **NOT** go into `restaurant_robot`'s `package.xml`.

**4 Nodes:**
- `order_manager` → service server (`/order_command`), publishes Point to (`/goal_position`)
- `robot_controller` → subscribes `/goal_position`, drives turtle, publishes `/delivery_status`
- `table_status_publisher` → publishes `/table_status` (TableStatus.msg)
- `monitor` → subscribes `/delivery_status`, logs reports

**Custom Interfaces:**
- `OrderCommand.srv` → `string command`, `int32 table_number` / `bool success`, `string message`
- `TableStatus.msg` → `int32 table_number`, `string status`

**ROS2 Data Types:**
- `geometry_msgs/Point` → x, y, z (target position)
- `geometry_msgs/Twist` → linear.x, angular.z (velocity command)
- `turtlesim/Pose` → x, y, theta (turtle's current position)
- `std_msgs/String` → data (delivery status)

**Point / Pose / Twist difference:**
- Point: position only (x, y, z)
- Pose: position + orientation (x, y, theta)
- Twist: velocity (linear + angular)

---

## STAGE 1 — WORKSPACE AND PACKAGE CREATION

**Create workspace:**
```bash
mkdir -p ~/projects/restaurant_robot_ws/src
cd ~/projects/restaurant_robot_ws
```

**Node package (ament_python):**
```bash
cd src
ros2 pkg create --build-type ament_python restaurant_robot
```

**Interface package (ament_cmake):**
```bash
ros2 pkg create --build-type ament_cmake restaurant_robot_interfaces
```

**Inner/outer package structure:**
```
restaurant_robot/          ← outer package (setup.py, package.xml)
  restaurant_robot/        ← inner package (node .py files go here)
    __init__.py
    robot_controller.py
    ...
```

**First build:**
```bash
cd ~/projects/restaurant_robot_ws
colcon build
source install/setup.bash
```

**Package check:**
```bash
ros2 pkg list | grep restaurant
```

---

## STAGE 1 — FULL FILE CONTENTS

### restaurant_robot/package.xml (ament_python)

```xml
<?xml version="1.0"?>
<package format="3">
  <name>restaurant_robot</name>
  <version>0.0.1</version>
  <description>Restaurant delivery robot nodes</description>
  <maintainer email="ahmet@example.com">ahmet</maintainer>
  <license>MIT</license>

  <depend>rclpy</depend>
  <depend>geometry_msgs</depend>
  <depend>turtlesim</depend>
  <depend>std_msgs</depend>
  <depend>restaurant_robot_interfaces</depend>

  <buildtool_depend>ament_python</buildtool_depend>

  <export>
    <build_type>ament_python</build_type>
  </export>
</package>
```

### restaurant_robot_interfaces/package.xml (ament_cmake)

```xml
<?xml version="1.0"?>
<package format="3">
  <name>restaurant_robot_interfaces</name>
  <version>0.0.1</version>
  <description>Custom interfaces for restaurant robot</description>
  <maintainer email="ahmet@example.com">ahmet</maintainer>
  <license>MIT</license>

  <buildtool_depend>ament_cmake</buildtool_depend>

  <build_depend>rosidl_default_generators</build_depend>
  <exec_depend>rosidl_default_runtime</exec_depend>
  <member_of_group>rosidl_interface_packages</member_of_group>

  <export>
    <build_type>ament_cmake</build_type>
  </export>
</package>
```

### restaurant_robot/setup.py (full)

```python
import os
from setuptools import find_packages, setup

package_name = 'restaurant_robot'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'config'), ['config/params.yaml']),
        (os.path.join('share', package_name, 'launch'), ['launch/restaurant.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    entry_points={
        'console_scripts': [
            'robot_controller = restaurant_robot.robot_controller:main',
            'order_manager = restaurant_robot.order_manager:main',
            'table_status_publisher = restaurant_robot.table_status_publisher:main',
            'monitor = restaurant_robot.monitor:main',
            'demo = restaurant_robot.demo_runner:main',
        ],
    },
)
```

### restaurant_robot_interfaces/CMakeLists.txt (full)

```cmake
cmake_minimum_required(VERSION 3.8)
project(restaurant_robot_interfaces)

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/TableStatus.msg"
  "srv/OrderCommand.srv"
)

ament_package()
```

---

## STAGE 2 — WRITING NODES (OOP STRUCTURE)

**Node writing order:** first publisher/subscriber nodes, then service server/client.

**Basic node template:**
```python
import rclpy
from rclpy.node import Node

class MyNode(Node):
    def __init__(self):
        super().__init__('node_name')
        # define publishers, subscribers, services here

def main(args=None):
    rclpy.init(args=args)
    node = MyNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

**⚠️ CRITICAL:** `self.cmd_pub_.publish(cmd)` must be **outside** the `if/else` block. If left inside, it only publishes in the `else` block.

**Source required after every build:**
```bash
source install/setup.bash
```

---

## STAGE 2 — FULL NODE FILES

### robot_controller.py

```python
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
        self.max_linear_speed = 1.0
        self.max_angular_speed = 2.0
        self.linear_gain = 0.8
        self.angular_gain = 3.0
        self.goal_sub = self.create_subscription(Point, 'goal_position', self.goal_callback, 10)
        self.pose_sub = self.create_subscription(Pose, '/turtle1/pose', self.pose_callback, 10)
        self.cmd_pub = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)
        self.delivery_pub = self.create_publisher(String, 'delivery_status', 10)

    def goal_callback(self, msg):
        self.goal = msg
        self.arrived = False

    def normalize_angle(self, angle):
        return math.atan2(math.sin(angle), math.cos(angle))

    def clamp(self, value, min_value, max_value):
        return max(min(value, max_value), min_value)

    def stop_robot(self):
        self.cmd_pub.publish(Twist())

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
        cmd.angular.z = self.clamp(
            self.angular_gain * angle_error,
            -self.max_angular_speed, self.max_angular_speed)
        if abs(angle_error) > self.angle_tolerance:
            cmd.linear.x = 0.0
        else:
            cmd.linear.x = self.clamp(
                self.linear_gain * distance, 0.0, self.max_linear_speed)
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
```

### order_manager.py

```python
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point
from restaurant_robot_interfaces.srv import OrderCommand


class OrderManager(Node):
    def __init__(self):
        super().__init__('order_manager')
        self.declare_parameter('table_x_coords', [2.0, 8.0, 8.0, 2.0, 5.5])
        self.declare_parameter('table_y_coords', [2.0, 2.0, 8.0, 8.0, 5.5])
        self.x_coords = self.get_parameter('table_x_coords').value
        self.y_coords = self.get_parameter('table_y_coords').value
        self.srv = self.create_service(OrderCommand, '/order_command', self.order_callback)
        self.goal_pub = self.create_publisher(Point, 'goal_position', 10)

    def order_callback(self, request, response):
        table = request.table_number
        if request.command == 'add_order' and 1 <= table <= len(self.x_coords):
            goal = Point()
            goal.x = self.x_coords[table - 1]
            goal.y = self.y_coords[table - 1]
            self.goal_pub.publish(goal)
            response.success = True
            response.message = f'Order sent to table {table}'
        else:
            response.success = False
            response.message = 'Invalid command or table number'
        return response


def main(args=None):
    rclpy.init(args=args)
    node = OrderManager()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
```

### table_status_publisher.py

```python
import rclpy
from rclpy.node import Node
from restaurant_robot_interfaces.msg import TableStatus


class TableStatusPublisher(Node):
    def __init__(self):
        super().__init__('table_status_publisher')
        self.pub = self.create_publisher(TableStatus, 'table_status', 10)
        self.timer = self.create_timer(1.0, self.timer_callback)

    def timer_callback(self):
        msg = TableStatus()
        msg.table_number = 1
        msg.status = 'EMPTY'
        self.pub.publish(msg)
        self.get_logger().info(f'Table {msg.table_number}: {msg.status}')


def main(args=None):
    rclpy.init(args=args)
    node = TableStatusPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
```

### monitor.py

```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class Monitor(Node):
    def __init__(self):
        super().__init__('monitor')
        self.sub = self.create_subscription(
            String, 'delivery_status', self.callback, 10)

    def callback(self, msg):
        self.get_logger().info(f'Delivery report: {msg.data}')


def main(args=None):
    rclpy.init(args=args)
    node = Monitor()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
```

### demo_runner.py

```python
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
        self.send_next_order()

    def send_next_order(self):
        if self.current_index >= len(self.tables):
            self.get_logger().info('All 5 tables done!')
            return
        table = self.tables[self.current_index]
        req = OrderCommand.Request()
        req.command = 'add_order'
        req.table_number = table
        future = self.client_.call_async(req)
        future.add_done_callback(
            lambda f: self.get_logger().info(f'Accepted: {f.result().message}'))

    def on_delivery(self, msg):
        self.current_index += 1
        if self.current_index < len(self.tables):
            self._pending_timer = self.create_timer(2.0, self._on_timer)
        else:
            self.get_logger().info('All 5 tables done!')

    def _on_timer(self):
        if self._pending_timer:
            self._pending_timer.cancel()
            self._pending_timer = None
        self.send_next_order()


def main(args=None):
    rclpy.init(args=args)
    node = DemoRunner()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
```

---

## STAGE 3 — TOPIC (PUBLISHER / SUBSCRIBER)

**Publisher:**
```python
self.pub = self.create_publisher(MsgType, 'topic_name', 10)
msg = MsgType()
msg.data = '...'
self.pub.publish(msg)
```

**Subscriber:**
```python
self.sub = self.create_subscription(MsgType, 'topic_name', self.callback, 10)

def callback(self, msg):
    # use msg
```

**Periodic publish with timer:**
```python
self.timer = self.create_timer(1.0, self.timer_callback)

def timer_callback(self):
    self.pub.publish(msg)
```

**CLI commands:**
```bash
ros2 topic list
ros2 topic echo /delivery_status
ros2 topic info /goal_position
```

---

## STAGE 4 — SERVICE (SERVER / CLIENT)

**Service server:**
```python
from restaurant_robot_interfaces.srv import OrderCommand

self.srv = self.create_service(OrderCommand, '/order_command', self.callback)

def callback(self, request, response):
    response.success = True
    response.message = 'OK'
    return response
```

**Service client:**
```python
self.client = self.create_client(OrderCommand, '/order_command')
while not self.client.wait_for_service(timeout_sec=1.0):
    self.get_logger().info('Waiting...')

req = OrderCommand.Request()
req.command = 'add_order'
req.table_number = 1
future = self.client.call_async(req)
```

**CLI test:**
```bash
ros2 service call /order_command restaurant_robot_interfaces/srv/OrderCommand \
  "{command: 'add_order', table_number: 1}"
```

---

## STAGE 5 — CUSTOM INTERFACE (MSG / SRV)

**TableStatus.msg:**
```
int32 table_number
string status
```

**OrderCommand.srv:**
```
string command
int32 table_number
---
bool success
string message
```

**Add to CMakeLists.txt:**
```cmake
find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/TableStatus.msg"
  "srv/OrderCommand.srv"
)
```

**Add to package.xml (interface package ONLY):**
```xml
<build_depend>rosidl_default_generators</build_depend>
<exec_depend>rosidl_default_runtime</exec_depend>
<member_of_group>rosidl_interface_packages</member_of_group>
```

**⚠️ WARNING:** These lines must **NOT** go into `restaurant_robot`'s `package.xml`. Only into `restaurant_robot_interfaces` package.xml.

---

## STAGE 6 — PARAMS.YAML AND LAUNCH FILE

**params.yaml** (under `config/` folder):
```yaml
order_manager:
  ros__parameters:
    table_x_coords: [2.0, 8.0, 8.0, 2.0, 5.5]
    table_y_coords: [2.0, 2.0, 8.0, 8.0, 5.5]
```

**Reading parameters in node:**
```python
self.declare_parameter('table_x_coords', [2.0, 5.0, 8.0])
x_coords = self.get_parameter('table_x_coords').value
```

**restaurant.launch.py:**
```python
from launch import LaunchDescription
from launch_ros.actions import Node
import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    params_file = os.path.join(
        get_package_share_directory('restaurant_robot'),
        'config', 'params.yaml'
    )
    return LaunchDescription([
        Node(package='turtlesim', executable='turtlesim_node', name='turtlesim'),
        Node(package='restaurant_robot', executable='order_manager',
             parameters=[params_file]),
        Node(package='restaurant_robot', executable='robot_controller'),
        Node(package='restaurant_robot', executable='table_status_publisher'),
        Node(package='restaurant_robot', executable='monitor'),
    ])
```

**data_files in setup.py:**
```python
(os.path.join('share', package_name, 'config'), ['config/params.yaml']),
(os.path.join('share', package_name, 'launch'), ['launch/restaurant.launch.py']),
```

**Only params.yaml changed** → no build needed, just restart launch.

---

## STAGE 7 — DEMO RUNNER AND DOCUMENTATION

**Turtlesim reset:**
```bash
ros2 service call /reset std_srvs/srv/Empty
```

**rqt_graph (external terminal):**
```bash
ros2 run rqt_graph rqt_graph
```

**GIF recording (Peek):**
1. Start launch in external terminal
2. VS Code terminal — reset: `ros2 service call /reset std_srvs/srv/Empty`
3. Peek → align over TurtleSim window → Record as GIF
4. VS Code terminal: `ros2 run restaurant_robot demo`
5. When "All 5 tables done!" appears → Peek → Stop
6. `mv ~/Videos/Peek*.gif ~/projects/restaurant_robot_ws/docs/demo.gif`

**If docs folder missing:**
```bash
mkdir -p ~/projects/restaurant_robot_ws/docs
```

**Git commit:**
```bash
git add -A
git commit -m "commit message"
git push origin main
```

**When to commit:** After each stage is complete. Don't commit small experimental changes.

---

## ROBOT CONTROLLER — CRITICAL NOTES

**Angle normalization is required.** Without it, turtle zigzags and exits the screen:
```python
def normalize_angle(self, angle):
    return math.atan2(math.sin(angle), math.cos(angle))
```

**Turn first, then move forward:**
```python
if abs(angle_error) > self.angle_tolerance:
    cmd.linear.x = 0.0  # stop while turning
else:
    cmd.linear.x = self.linear_gain * distance
```

**Speed clamping:**
```python
def clamp(self, value, min_value, max_value):
    return max(min(value, max_value), min_value)
```

**Tunable parameters:**
```python
self.distance_tolerance = 0.15
self.angle_tolerance = 0.25
self.max_linear_speed = 1.0
self.max_angular_speed = 2.0
self.linear_gain = 0.8
self.angular_gain = 3.0
```

---

## RQT_GRAPH ARCHITECTURE EXPLANATION

Shapes in rqt_graph:
- **Oval/ellipse** → Node (e.g. `/order_manager`, `/robot_controller`, `/turtlesim`)
- **Rectangle** → Topic (e.g. `/goal_position`, `/turtle1/cmd_vel`)
- **Arrow direction** → from Publisher to Subscriber

`/order_manager` → (`/goal_position` topic) → `/robot_controller` → (`/turtle1/cmd_vel` topic) → `/turtlesim`

`/robot_controller` also subscribes to `/turtle1/pose` (comes from turtlesim).

`/delivery_status` topic is published by `/robot_controller`, subscribed by `/monitor`.

---

## OTHER CRITICAL NOTES

**VS Code GUI warning:** Never run turtlesim, rqt, rviz from VS Code terminal → `GLIBC_PRIVATE` error. Always use external terminal (Ctrl+Alt+T). Never use "Run Python File" from VS Code — nodes must be run with `ros2 run`.

**Node naming rule:** Keep executable name in `setup.py` and `super().__init__('...')` the same.
```python
# setup.py
'order_manager = restaurant_robot.order_manager:main'

# inside order_manager.py
super().__init__('order_manager')  # same name
```

- `ros2 run restaurant_robot order_manager` → uses executable name (from setup.py)
- `ros2 node list` → shows node name (from super().__init__)

**Creating architecture.png:**
```bash
python3 .../architecture.py
sudo apt install fonts-ipaexfont  # if Japanese font needed
```

**Snippet usage:** File → Preferences → Configure Snippets → Python → type `ros2pub` and press Tab.

**If docs folder missing:**
```bash
mkdir -p ~/projects/restaurant_robot_ws/docs
```

---

## COMMON ERRORS

| Error | Cause | Fix |
|-------|-------|-----|
| `Package not found` | source run in different terminal | Run `source install/setup.bash` in same terminal |
| `GLIBC_PRIVATE` | turtlesim run in VS Code terminal | Move to external terminal |
| Turtle zigzags | Angle not normalized | Use `normalize_angle()` |
| Turtle exits screen | Speed too high | Lower `linear_gain`, add clamp |
| `params.yaml` shows M | VS Code sync delay | Verify with `cat`, ignore M |
| Demo shows old table count | Old binary running | Ctrl+C → restart launch |

---

*ROS2 Jazzy — Ubuntu 24.04 — June 2026*
