# ADALM-LSMSPG ROS2 Servo Demo

A minimal ROS2 example showing how to integrate ADI hardware with robotics applications.
Uses the AD5592r DAC/ADC on the ADALM-LSMSPG to drive a servo motor and read sensor feedback.

## What This Demo Does

This demo implements the basic control loop pattern used in robotics:

1. **servo_commander** generates a smooth sweeping motion (0-180 degrees) and outputs
   the corresponding voltage to DAC channel 0 — as if commanding a servo motor position
2. **servo_feedback** reads ADC channels to measure position and current, then publishes
   standard ROS2 `JointState` messages that any robotics tool can consume

Think of it as the "Hello World" for connecting real analog hardware to the ROS2 ecosystem.

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

Kuiper Linux 2 is based on Debian Trixie. ROS2 Jazzy (LTS) must be built from source
since official ROS2 packages are only available for Ubuntu.

### Build ROS2 Jazzy from Source

This process takes 2-3 hours on a Raspberry Pi 5.

```bash
# 1. Set locale
sudo apt update && sudo apt install -y locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

# 2. Install build dependencies
sudo apt install -y \
    python3-pip \
    python3-rosdep \
    python3-colcon-common-extensions \
    python3-vcstool \
    python3-sipbuild \
    sip-tools \
    git \
    curl

# 3. Install X11/graphics development libraries (required for rviz)
sudo apt install -y \
    libxrandr-dev \
    libfreetype-dev \
    libxt-dev \
    libxaw7-dev

# 4. Add swap space (Pi 5 needs extra memory for compilation)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 5. Initialize rosdep
sudo rosdep init
rosdep update

# 6. Create workspace and fetch ROS2 Jazzy sources
mkdir -p ~/ros2_jazzy/src && cd ~/ros2_jazzy
curl -sSL https://raw.githubusercontent.com/ros2/ros2/jazzy/ros2.repos | vcs import src

# 7. Install ROS2 dependencies (skip packages unavailable on Debian Trixie)
rosdep install --from-paths src --ignore-src -y \
    --rosdistro jazzy \
    --skip-keys "rti-connext-dds-6.0.1 urdfdom_headers python3-sip-dev"

# 8. Build ROS2 (use --parallel-workers 1 to avoid out-of-memory errors)
colcon build --symlink-install --parallel-workers 1

# 9. Source ROS2 setup (add to ~/.bashrc for persistence)
echo "source ~/ros2_jazzy/install/setup.bash" >> ~/.bashrc
source ~/ros2_jazzy/install/setup.bash
```

**Note:** If a package fails to build due to missing dependencies, install them and re-run
`colcon build` - it will continue from where it left off.

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
ros2 run adalm_lsmspg_servo_demo servo_commander --ros-args -p uri:="'local:'"
```

### Terminal 2: Start the Feedback Reader
```bash
source ~/ros2_ws/install/setup.bash
ros2 run adalm_lsmspg_servo_demo servo_feedback --ros-args -p uri:="'local:'"
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
    --ros-args -p uri:="'local:'" -p sweep_rate_hz:=0.5 -p max_angle:=90.0
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
ros2 run adalm_lsmspg_servo_demo servo_commander --ros-args -p uri:="'local:'"

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

**"Failed to parse global arguments" or "Couldn't parse parameter override rule":**
- URIs containing colons (like `local:` or `ip:host`) need extra quoting for ROS2's YAML parser
- Use single quotes inside double quotes: `-p uri:="'local:'"`
- Or use a params file instead of command-line parameters
