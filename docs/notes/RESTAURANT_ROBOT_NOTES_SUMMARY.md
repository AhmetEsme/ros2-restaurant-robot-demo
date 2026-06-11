# ROS2 RESTAURANT DELIVERY ROBOT — NOTES SUMMARY

---

## GENERAL RULES (ALWAYS APPLY)

**Terminal rule:**
- External terminal (Ctrl+Alt+T): **ONLY for GUI programs** — turtlesim, rqt, rviz, Gazebo
- VS Code integrated terminal: **everything else** — ros2 run, colcon build, source, git, service call, topic echo

**Why?** VS Code terminal conflicts with snap libraries → `symbol lookup error: GLIBC_PRIVATE` error.

**Each terminal is independent.** `source install/setup.bash` must be run in the same terminal where `ros2 run` will be executed. Different terminal → `Package not found` error.

**When to build:**
- `.py`, `.srv`, `.msg`, `package.xml`, `setup.py` changed → **always build**
- Only `params.yaml` changed → no build needed, just restart launch

**Build command:**
```bash
colcon build
source install/setup.bash
```

**Alias:**
```bash
restaurant && ros2 launch restaurant_robot restaurant.launch.py
```

---

## VS CODE SHORTCUTS

- **Ctrl+F** → search for a value in a file
- **Ctrl+H** → Find & Replace — find and change a value
- **Insert key** → toggle between OVR/INS mode
  - **INS mode** (normal): typed character inserted at cursor
  - **OVR mode**: typed character overwrites character under cursor — caution!
  - If `OVR` shows in bottom-right → press Insert to switch back

---

## PROJECT ARCHITECTURE

**Workspace:** `~/projects/restaurant_robot_ws`
**GitHub:** `https://github.com/AhmetEsme/ros2-restaurant-robot-demo`

**2 packages:**
- `restaurant_robot` → ament_python (contains nodes)
- `restaurant_robot_interfaces` → ament_cmake (contains custom msg/srv)

**⚠️ CRITICAL:** Two separate `package.xml` files. `rosidl` dependency lines go **ONLY** into `restaurant_robot_interfaces` package.xml. Must **NOT** go into `restaurant_robot` package.xml.

**4 Nodes:**
- `order_manager` → service server (`/order_command`), publishes Point (`/goal_position`)
- `robot_controller` → subscribes `/goal_position`, drives turtle, publishes `/delivery_status`
- `table_status_publisher` → publishes `/table_status`
- `monitor` → subscribes `/delivery_status`, logs reports

**ROS2 Data Types:**
- `geometry_msgs/Point` → x, y, z (target position)
- `geometry_msgs/Twist` → linear.x, angular.z (velocity command)
- `turtlesim/Pose` → x, y, theta (current turtle position)
- `std_msgs/String` → data (delivery status)

**Point / Pose / Twist:**
- Point: position only (x, y, z)
- Pose: position + orientation (x, y, theta)
- Twist: velocity (linear + angular)

---

## STAGE 1 — WORKSPACE AND PACKAGE CREATION

```bash
mkdir -p ~/projects/restaurant_robot_ws/src
cd ~/projects/restaurant_robot_ws/src
ros2 pkg create --build-type ament_python restaurant_robot
ros2 pkg create --build-type ament_cmake restaurant_robot_interfaces
cd ..
colcon build
source install/setup.bash
ros2 pkg list | grep restaurant
```

**Inner/outer package structure:**
```
restaurant_robot/          ← outer package (setup.py, package.xml)
  restaurant_robot/        ← inner package (node .py files go here)
    __init__.py
    robot_controller.py
```

---

## STAGE 2 — WRITING NODES (OOP STRUCTURE)

**Node writing order:** publisher/subscriber nodes first, then service server/client.

**Basic node template:**
```python
import rclpy
from rclpy.node import Node

class MyNode(Node):
    def __init__(self):
        super().__init__('node_name')

def main(args=None):
    rclpy.init(args=args)
    node = MyNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
```

**setup.py entry points:**
```python
entry_points={
    'console_scripts': [
        'robot_controller = restaurant_robot.robot_controller:main',
        'order_manager = restaurant_robot.order_manager:main',
        'table_status_publisher = restaurant_robot.table_status_publisher:main',
        'monitor = restaurant_robot.monitor:main',
        'demo = restaurant_robot.demo_runner:main',
    ],
},
```

**⚠️ CRITICAL:** `self.cmd_pub_.publish(cmd)` must be **outside** the `if/else` block.

---

## STAGE 3 — TOPIC (PUBLISHER / SUBSCRIBER)

```python
# Publisher
self.pub = self.create_publisher(MsgType, 'topic_name', 10)
self.pub.publish(msg)

# Subscriber
self.sub = self.create_subscription(MsgType, 'topic_name', self.callback, 10)

# Timer
self.timer = self.create_timer(1.0, self.timer_callback)
```

```bash
ros2 topic list
ros2 topic echo /delivery_status
ros2 topic info /goal_position
```

---

## STAGE 4 — SERVICE (SERVER / CLIENT)

```python
# Server
self.srv = self.create_service(OrderCommand, '/order_command', self.callback)

# Client
self.client = self.create_client(OrderCommand, '/order_command')
req = OrderCommand.Request()
future = self.client.call_async(req)
```

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

**CMakeLists.txt:**
```cmake
find_package(rosidl_default_generators REQUIRED)
rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/TableStatus.msg"
  "srv/OrderCommand.srv"
)
```

**package.xml (interface package ONLY):**
```xml
<build_depend>rosidl_default_generators</build_depend>
<exec_depend>rosidl_default_runtime</exec_depend>
<member_of_group>rosidl_interface_packages</member_of_group>
```

---

## STAGE 6 — PARAMS.YAML AND LAUNCH FILE

**params.yaml:**
```yaml
order_manager:
  ros__parameters:
    table_x_coords: [2.0, 8.0, 8.0, 2.0, 5.5]
    table_y_coords: [2.0, 2.0, 8.0, 8.0, 5.5]
```

Only `params.yaml` changed → no build, just restart launch.

**setup.py data_files:**
```python
(os.path.join('share', package_name, 'config'), ['config/params.yaml']),
(os.path.join('share', package_name, 'launch'), ['launch/restaurant.launch.py']),
```

---

## STAGE 7 — DEMO RUNNER AND DOCUMENTATION

**GIF recording (Peek):**
1. Start launch in external terminal
2. VS Code terminal: `ros2 service call /reset std_srvs/srv/Empty`
3. Peek → align over TurtleSim → Record as GIF
4. VS Code terminal: `ros2 run restaurant_robot demo`
5. "All 5 tables done!" → Peek → Stop
6. `mv ~/Videos/Peek*.gif ~/projects/restaurant_robot_ws/docs/demo.gif`

**Git commit:**
```bash
git add -A
git commit -m "commit message"
git push origin main
```

---

## ROBOT CONTROLLER — CRITICAL NOTES

**Angle normalization (required):**
```python
def normalize_angle(self, angle):
    return math.atan2(math.sin(angle), math.cos(angle))
```

**Turn first, then move forward:**
```python
if abs(angle_error) > self.angle_tolerance:
    cmd.linear.x = 0.0
else:
    cmd.linear.x = self.linear_gain * distance
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

## RQT_GRAPH ARCHITECTURE

- **Oval** → Node
- **Rectangle** → Topic
- **Arrow** → Publisher to Subscriber

```
/order_manager → (/goal_position) → /robot_controller → (/turtle1/cmd_vel) → /turtlesim
/robot_controller also subscribes /turtle1/pose
/delivery_status: robot_controller publishes, monitor subscribes
```

---

## OTHER CRITICAL NOTES

**VS Code GUI warning:** Never run turtlesim/rqt/rviz from VS Code terminal. Always use external terminal. Never use "Run Python File".

**Node naming:** Keep executable name in `setup.py` and `super().__init__()` the same.

**If docs folder missing:** `mkdir -p ~/projects/restaurant_robot_ws/docs`

---

## COMMON ERRORS

| Error | Cause | Fix |
|-------|-------|-----|
| `Package not found` | source in different terminal | Run source in same terminal |
| `GLIBC_PRIVATE` | turtlesim in VS Code | Move to external terminal |
| Turtle zigzags | Angle not normalized | Use `normalize_angle()` |
| Turtle exits screen | Speed too high | Lower `linear_gain`, add clamp |
| `params.yaml` shows M | VS Code sync delay | Verify with `cat`, ignore M |
| Demo shows old tables | Old binary running | Ctrl+C → restart launch |

---

*ROS2 Jazzy — Ubuntu 24.04 — June 2026*
