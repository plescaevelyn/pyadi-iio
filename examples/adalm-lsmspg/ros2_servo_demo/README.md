# ADALM-LSMSPG ROS2 Servo Demo

A "Hello, World!" style ROS2 example demonstrating IIO + ADI hardware integration.
This package simulates servo motor control for a robotic arm using the AD5592r
DAC/ADC channels on the ADALM-LSMSPG evaluation board.

## What This Demo Does

- **servo_commander**: Generates sinusoidal position commands (like moving a robotic
  arm joint), outputs corresponding voltages via DAC channel 0
- **servo_feedback**: Reads ADC channels to simulate position encoder and current
  sensor feedback, publishes ROS2 JointState messages

This demonstrates the fundamental pattern for robotics: command output + sensor feedback.

## Hardware Setup

Ensure your ADALM-LSMSPG is connected to the Raspberry Pi 5 via the 40-pin ribbon cable
and the overlay is enabled in `/boot/config.txt`:

```
dtoverlay=rpi-adalm-lsmspg
```

Verify IIO connectivity:
```bash
iio_info -u local:
```

## ROS2 Installation on Raspberry Pi 5 (Kuiper Linux 2)

Kuiper Linux 2 is based on Debian Bookworm. ROS2 Jazzy (LTS) is the recommended version.

### Option 1: Install from ROS2 Debian Packages (Recommended)

```bash
# 1. Set locale
sudo apt update && sudo apt install -y locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

# 2. Add ROS2 apt repository
sudo apt install -y software-properties-common curl
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu jammy main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

# 3. Install ROS2 Jazzy (base is sufficient, desktop adds visualization tools)
sudo apt update
sudo apt install -y ros-jazzy-ros-base python3-colcon-common-extensions

# 4. Source ROS2 setup (add to ~/.bashrc for persistence)
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
source /opt/ros/jazzy/setup.bash
```

### Option 2: Build from Source (if packages unavailable)

```bash
# Install build dependencies
sudo apt install -y python3-rosdep python3-colcon-common-extensions python3-vcstool

# Create workspace and fetch sources
mkdir -p ~/ros2_jazzy/src && cd ~/ros2_jazzy
vcs import src < https://raw.githubusercontent.com/ros2/ros2/jazzy/ros2.repos

# Install dependencies and build (takes 1-2 hours on Pi 5)
sudo rosdep init && rosdep update
rosdep install --from-paths src --ignore-src -y
colcon build --symlink-install
```

### Install pyadi-iio

```bash
pip3 install pyadi-iio
# Or from your local clone:
cd /path/to/pyadi-iio
pip3 install -e .
```

## Building This Package

```bash
# Create a ROS2 workspace
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src

# Copy or symlink this package
cp -r /path/to/pyadi-iio/examples/adalm-lsmspg/ros2_servo_demo .
# Or: ln -s /path/to/pyadi-iio/examples/adalm-lsmspg/ros2_servo_demo .

# Build
cd ~/ros2_ws
colcon build --packages-select adalm_lsmspg_servo_demo

# Source the workspace
source install/setup.bash
```

## Running the Demo

### Terminal 1: Start the Servo Commander
```bash
source ~/ros2_ws/install/setup.bash
ros2 run adalm_lsmspg_servo_demo servo_commander --ros-args -p uri:="local:"
```

### Terminal 2: Start the Feedback Reader
```bash
source ~/ros2_ws/install/setup.bash
ros2 run adalm_lsmspg_servo_demo servo_feedback --ros-args -p uri:="local:"
```

### Terminal 3: Monitor Topics
```bash
# List active topics
ros2 topic list

# Echo position commands
ros2 topic echo /servo/position_cmd

# Echo joint state feedback
ros2 topic echo /servo/joint_state
```

## Parameters

### servo_commander
| Parameter | Default | Description |
|-----------|---------|-------------|
| uri | ip:analog.local | IIO context URI |
| sweep_rate_hz | 1.0 | Frequency of position sweep |
| min_angle | 0.0 | Minimum servo angle (degrees) |
| max_angle | 180.0 | Maximum servo angle (degrees) |

### servo_feedback
| Parameter | Default | Description |
|-----------|---------|-------------|
| uri | ip:analog.local | IIO context URI |
| sample_rate_hz | 10.0 | ADC sampling rate |

Example with custom parameters:
```bash
ros2 run adalm_lsmspg_servo_demo servo_commander \
    --ros-args -p uri:="local:" -p sweep_rate_hz:=0.5 -p max_angle:=90.0
```

## ROS2 Topics

| Topic | Type | Description |
|-------|------|-------------|
| /servo/position_cmd | std_msgs/Float32 | Commanded position (degrees) |
| /servo/joint_state | sensor_msgs/JointState | Position (rad) and effort (mA) |
| /servo/current_ma | std_msgs/Float32 | Motor current draw (mA) |

## Running on Remote Pi (from your PC)

If you want to visualize on your PC while running on the Pi:

```bash
# On Pi (set ROS_DOMAIN_ID to match)
export ROS_DOMAIN_ID=42
ros2 run adalm_lsmspg_servo_demo servo_commander --ros-args -p uri:="local:"

# On your PC (same domain ID)
export ROS_DOMAIN_ID=42
ros2 topic echo /servo/joint_state
```

## Troubleshooting

**"Permission denied" when accessing IIO devices locally:**
```bash
sudo usermod -aG dialout $USER
# Log out and back in, or:
sudo chmod 666 /dev/iio*
```

**"Cannot connect to AD5592r":**
- Verify the overlay is loaded: `dmesg | grep ad559`
- Check IIO devices exist: `ls /sys/bus/iio/devices/`
- Test with: `iio_info -u local:`

**ROS2 nodes can't find each other:**
- Ensure both use the same `ROS_DOMAIN_ID`
- Check firewall isn't blocking UDP multicast
