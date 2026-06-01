# Design — Restaurant Delivery Robot

## Nodes (4)
- order_manager: command queue + service server (the coordinator)
- robot_controller: drives the turtle to a goal position
- table_status_publisher: broadcasts each table's status
- monitor: console output + delivery report

## Interfaces

### Custom (restaurant_robot_interfaces)
- OrderCommand.srv
  - request: string command, int32 table_number
  - response: bool success, string message
- TableStatus.msg
  - int32 table_number, string status  # EMPTY / WAITING / DELIVERED

### Standard (reused, not custom)
- geometry_msgs/Point  -> goal position
- std_msgs/String      -> delivery status text

## Topics & Services
| Connection | Name | Type |
|---|---|---|
| Operator -> order_manager | /order_command | OrderCommand.srv (service) |
| table_status_publisher -> order_manager | /table_status | TableStatus.msg (topic) |
| order_manager -> robot_controller | /goal_position | geometry_msgs/Point (topic) |
| robot_controller -> monitor | /delivery_status | std_msgs/String (topic) |
