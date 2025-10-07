import time
import adi
import numpy as np
import matplotlib.pyplot as plt

AD74413R_DAC_MAX_CODE = 8192

dev_uri = "ip:192.168.97.40"

"""
	Possible values:
	- max14906 selected as device: input, output, high_z
	- ad74413r selected as device: high_z, voltage_out, current_out,
				       voltage_in, current_in_ext, current_in_loop,
				       resistance, digital_input, digital_input_loop,
				       current_in_ext_hart, current_in_loop_hart

"""
channel_config = ["output", "voltage_in", "voltage_in", "high_z"]

# Possible values: 0, 1
channel_enable = [1, 1, 1, 1]

# Possible values: "ad74413r", "max14906"
channel_device = ["max14906","ad74413r", "ad74413r", "ad74413r"]

swiot = adi.swiot(uri=dev_uri)
swiot.mode = "config"
swiot = adi.swiot(uri=dev_uri)

swiot.ch0_device = channel_device[0]
swiot.ch0_function = channel_config[0]
swiot.ch0_enable = channel_enable[0]
swiot.ch1_device = channel_device[1]
swiot.ch1_function = channel_config[1]
swiot.ch1_enable = channel_enable[1]
swiot.ch2_device = channel_device[2]
swiot.ch2_function = channel_config[2]
swiot.ch2_enable = channel_enable[2]
swiot.ch3_device = channel_device[3]
swiot.ch3_function = channel_config[3]
swiot.ch3_enable = channel_enable[3]
swiot.mode = "runtime"

ad74413r = adi.ad74413r(uri=dev_uri)
max14906 = adi.max14906(uri=dev_uri)
adt75 = adi.lm75(uri=dev_uri)
swiot = adi.swiot(uri=dev_uri)
swiot.mode = "runtime"


# Constants for PWM control
PWM_FREQUENCY = 250  # Frequency for fan control
PWM_PERIOD = 1.0  # Time period for one cycle (s)
DC_RPM = 4500  # Max number of RPM for the fan

# PID parameters for temperature control
Kp = 1.5
Ki = 1
Kd = 1
setpoint = 26.0  # Temperature setpoint in degrees Celsius

# Initialize PID control variables
integral = 0
previous_error = 0

time_data = []
temperature_data = []
pwm_data = []
pwm_signal_data = []
fan_rpm = []
data = []

# --- Helper Functions ---

# PID control function
def pid_control(current_temperature):
    """
    This function implements a PID control algorithm to regulate a system based on 
    a temperature input.
    
    :param current_temperature: The "current_temperature" parameter is the current temperature value
    that is used as input to the PID control algorithm. This parameter represents the actual temperature
    of the system that the PID controller is trying to control.
    """
    global integral, previous_error

    # Calculate error
    error = -(setpoint - current_temperature)
    print(f"Current error: {error}")

    # Proportional, Integral, and Derivative terms
    proportional = Kp * error
    integral += error * Ki
    derivative = Kd * (error - previous_error)
    previous_error = error

    # PID output for fan speed control
    pid_output = proportional + integral + derivative
    print(f"PID output: {pid_output}")

    # Convert PID output to PWM duty cycle (0-100%)
    pwm_duty_cycle = np.clip(pid_output, 0, 100)
    print(f"PWM duty cycle: {int(pwm_duty_cycle)}")

    return pwm_duty_cycle

# Function to simulate PWM using MAX14906 digital output
def set_pwm_duty_cycle(channel, duty_cycle):
    """
    This function sets the duty cycle for a specific PWM channel.
    
    :param channel: The "channel" parameter typically refers to the specific PWM channel or pin on a
    microcontroller  where you want to set the duty cycle.
    :param duty_cycle: The duty cycle parameter represents the percentage of time that the PWM signal is
    high (on) compared to the total period of the signal. It typically ranges from 0 (0% duty cycle,
    signal always low) to 100 (100% duty cycle, signal always high).
    """
    on_time = (duty_cycle / 100) * PWM_PERIOD
    off_time = PWM_PERIOD - on_time
    print(f"On-time: {on_time}, Off-time: {off_time}")

    if duty_cycle > 0:
        # Turn on the digital output for "on_time"
        max14906.channel["voltage0"].raw = 1
        data.extend([1] * int(duty_cycle))
        time.sleep(on_time)

        # Turn off the digital output for "off_time"
        max14906.channel["voltage0"].raw = 0
        data.extend([0] * (100 - int(duty_cycle)))
        time.sleep(off_time)
    else:
        # Duty cycle is 0%, fan should be off
        max14906.channel["voltage0"].raw = 0
        time.sleep(PWM_PERIOD)

# --- Main Execution Loop ---

try:
    # Verify device channels
    print("MAX14906 output/input channels:", max14906._tx_channel_names, max14906._rx_channel_names)
    print("AD74413R input (ADC) channels:", ad74413r._rx_channel_names)
    print(f"Initial ADT75 temperature reading: {adt75() * 62.5} °C")

    start_time = time.time()

    # Main loop for temperature control and fan speed adjustment
    while True:
        # Read the current temperature from ADT75 sensor
        current_temperature = adt75() * 62.5
        print(f"Current temperature: {current_temperature} °C")

        # Get the PID-adjusted PWM duty cycle based on the temperature
        pwm_output = pid_control(current_temperature)

        # Simulate PWM to control the fan using MAX14906
        set_pwm_duty_cycle(max14906.channel["voltage0"].raw, pwm_output)
        fan_speed = DC_RPM * pwm_output / 100
        fan_rpm.append(fan_speed)

        # Append data for plotting
        current_time = time.time() - start_time
        time_data.append(current_time)
        temperature_data.append(current_temperature)
        pwm_data.append(pwm_output)

        # Plot data every 10 iterations
        if len(time_data) % 6 == 0:
            plt.clf()

            # Plot Temperature vs. Time
            plt.subplot(3, 1, 1)
            plt.plot(time_data, temperature_data, label="Actual Temperature")
            plt.axhline(setpoint, color='r', linestyle='--', label="Setpoint")
            plt.xlabel("Time (s)")
            plt.ylabel("Temperature (°C)")
            plt.legend()
            plt.grid(True)

            # Plot Fan Speed vs. Time
            plt.subplot(3, 1, 2)
            plt.plot(time_data, fan_rpm, label="Fan Speed", color="b")
            plt.xlabel("Time (s)")
            plt.ylabel("Speed (RPM)")
            plt.grid(True)
            plt.legend()

            # Plot PWM Signal
            plt.subplot(3, 1, 3)
            plt.plot(data, label="PWM Signal", color='g')
            plt.xlabel("Time (s)")
            plt.ylabel("PWM Signal")
            plt.grid(True)
            plt.legend()

            # Adjust layout and update the plot
            plt.tight_layout()
            plt.subplots_adjust(hspace=0.2)
            plt.pause(0.01)

        
        time.sleep(0.2)

except KeyboardInterrupt:
    # Stop the fan when CTRL+C is pressed
    max14906.channel["voltage0"].raw = 0
    print("PWM simulation stopped and voltage set to 0.")
