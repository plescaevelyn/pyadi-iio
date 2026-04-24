# Copyright (C) 2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""
ROS2 Servo Feedback Node - Hello World with ADALM-LSMSPG

This node reads ADC values from the AD5592r to simulate position and
current feedback from a servo motor. In a real robotic arm, these would
come from encoders and current sensors.

Channels used:
  - voltage1_adc: Simulates position feedback (like an encoder)
  - voltage2_adc: Simulates current draw (like a current sense resistor)
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Float32

import adi


class ServoFeedback(Node):
    """Reads ADC feedback and publishes sensor data."""

    def __init__(self):
        super().__init__("servo_feedback")

        # Declare parameters
        self.declare_parameter("uri", "ip:analog.local")
        self.declare_parameter("sample_rate_hz", 10.0)

        uri = self.get_parameter("uri").get_parameter_value().string_value
        sample_rate = (
            self.get_parameter("sample_rate_hz").get_parameter_value().double_value
        )

        # Connect to AD5592r
        self.get_logger().info(f"Connecting to AD5592r at {uri}")
        try:
            self.ad5592r = adi.ad5592r(uri=uri)
            self.position_adc = self.ad5592r.voltage1_adc
            self.current_adc = self.ad5592r.voltage2_adc
            self.mV_per_lsb = self.position_adc.scale
            self.get_logger().info("AD5592r ADC feedback connected!")
        except Exception as e:
            self.get_logger().error(f"Failed to connect to AD5592r: {e}")
            raise

        # Publishers
        self.joint_pub = self.create_publisher(JointState, "servo/joint_state", 10)
        self.current_pub = self.create_publisher(Float32, "servo/current_ma", 10)

        # Subscriber to position commands (for comparison)
        self.cmd_sub = self.create_subscription(
            Float32, "servo/position_cmd", self.cmd_callback, 10
        )
        self.last_cmd = 0.0

        # Timer for ADC sampling
        period = 1.0 / sample_rate
        self.timer = self.create_timer(period, self.timer_callback)

        self.get_logger().info(f"Servo Feedback started at {sample_rate} Hz")

    def voltage_to_angle(self, voltage_mv: float) -> float:
        """Convert voltage (0-2500 mV) back to angle (0-180 deg)."""
        return (voltage_mv / 2500.0) * 180.0

    def voltage_to_current(self, voltage_mv: float, r_sense: float = 47.0) -> float:
        """Convert sense voltage to current in mA."""
        return voltage_mv / r_sense

    def cmd_callback(self, msg: Float32):
        """Store latest commanded position."""
        self.last_cmd = msg.data

    def timer_callback(self):
        """Read ADC values and publish feedback."""
        # Read position feedback (voltage1)
        pos_voltage_mv = self.position_adc.raw * self.mV_per_lsb
        measured_angle = self.voltage_to_angle(pos_voltage_mv)

        # Read current feedback (voltage2)
        cur_voltage_mv = self.current_adc.raw * self.mV_per_lsb
        measured_current = self.voltage_to_current(cur_voltage_mv)

        # Publish JointState message
        joint_msg = JointState()
        joint_msg.header.stamp = self.get_clock().now().to_msg()
        joint_msg.name = ["servo_joint"]
        joint_msg.position = [measured_angle * 3.14159 / 180.0]  # radians
        joint_msg.effort = [measured_current]  # mA as proxy for effort
        self.joint_pub.publish(joint_msg)

        # Publish current separately
        current_msg = Float32()
        current_msg.data = measured_current
        self.current_pub.publish(current_msg)

        # Calculate tracking error
        error = self.last_cmd - measured_angle

        self.get_logger().info(
            f"Pos: {measured_angle:.1f} deg (cmd: {self.last_cmd:.1f}, err: {error:.1f}) | "
            f"Current: {measured_current:.2f} mA"
        )


def main(args=None):
    rclpy.init(args=args)
    node = ServoFeedback()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
