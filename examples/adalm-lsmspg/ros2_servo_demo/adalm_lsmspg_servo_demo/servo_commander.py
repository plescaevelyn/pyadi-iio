# Copyright (C) 2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""
ROS2 Servo Commander Node - Hello World with ADALM-LSMSPG

This node demonstrates using the AD5592r DAC to simulate servo position
commands. It publishes position commands and uses the DAC to output
corresponding voltage levels - like commanding a servo motor in a robotic arm.

The AD5592r DAC channel outputs a voltage proportional to the commanded
position (0-180 degrees mapped to 0-2.5V).
"""

import math

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32

import adi


class ServoCommander(Node):
    """Publishes servo position commands and drives DAC output."""

    def __init__(self):
        super().__init__("servo_commander")

        # Declare parameters
        self.declare_parameter("uri", "ip:analog.local")
        self.declare_parameter("sweep_rate_hz", 1.0)
        self.declare_parameter("min_angle", 0.0)
        self.declare_parameter("max_angle", 180.0)

        uri = self.get_parameter("uri").get_parameter_value().string_value
        self.sweep_rate = (
            self.get_parameter("sweep_rate_hz").get_parameter_value().double_value
        )
        self.min_angle = (
            self.get_parameter("min_angle").get_parameter_value().double_value
        )
        self.max_angle = (
            self.get_parameter("max_angle").get_parameter_value().double_value
        )

        # Connect to AD5592r
        self.get_logger().info(f"Connecting to AD5592r at {uri}")
        try:
            self.ad5592r = adi.ad5592r(uri=uri)
            self.dac_out = self.ad5592r.voltage0_dac
            self.mV_per_lsb = self.dac_out.scale
            self.get_logger().info("AD5592r connected successfully!")
        except Exception as e:
            self.get_logger().error(f"Failed to connect to AD5592r: {e}")
            raise

        # Publisher for commanded position
        self.position_pub = self.create_publisher(Float32, "servo/position_cmd", 10)

        # Timer for periodic updates (10 Hz control loop)
        self.timer = self.create_timer(0.1, self.timer_callback)

        # State for sweep pattern
        self.time_elapsed = 0.0
        self.get_logger().info(
            f"Servo Commander started - sweeping {self.min_angle} to {self.max_angle} degrees"
        )

    def angle_to_voltage_mv(self, angle_deg: float) -> float:
        """Convert angle (0-180 deg) to voltage (0-2500 mV)."""
        normalized = (angle_deg - self.min_angle) / (self.max_angle - self.min_angle)
        return normalized * 2500.0

    def timer_callback(self):
        """Generate sinusoidal sweep pattern and output to DAC."""
        self.time_elapsed += 0.1

        # Generate smooth sinusoidal sweep between min and max angles
        angle = (self.min_angle + self.max_angle) / 2.0 + (
            (self.max_angle - self.min_angle)
            / 2.0
            * math.sin(2 * math.pi * self.sweep_rate * self.time_elapsed)
        )

        # Convert to voltage and write to DAC
        voltage_mv = self.angle_to_voltage_mv(angle)
        self.dac_out.raw = int(voltage_mv / self.mV_per_lsb)

        # Publish position command
        msg = Float32()
        msg.data = float(angle)
        self.position_pub.publish(msg)

        self.get_logger().debug(
            f"Position: {angle:.1f} deg -> DAC: {voltage_mv:.0f} mV"
        )

    def destroy_node(self):
        """Cleanup: set DAC to safe zero position."""
        if hasattr(self, "dac_out"):
            self.dac_out.raw = 0
            self.get_logger().info("DAC set to zero - cleanup complete")
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = ServoCommander()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
