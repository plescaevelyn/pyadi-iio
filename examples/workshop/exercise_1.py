import adi
import tkinter as tk
from tkinter import messagebox
from tkinter import *
import time
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import customtkinter as ctk


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

channel_config = ["voltage_out", "voltage_out", "voltage_in", "voltage_out"]

# Possible values: 0, 1
channel_enable = [1, 1, 1, 1]

# Possible values: "ad74413r", "max14906"
channel_device = ["ad74413r", "ad74413r", "ad74413r", "ad74413r"]

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
# Rev ID should be 0x8
print("AD74413R rev ID:", ad74413r.reg_read(0x46))

# Channels which may be used to sample data from the AD74413R
print("AD74413R input (ADC) channels:", ad74413r._rx_channel_names)

# Channels which may be used to set DAC values
print("AD74413R output (DAC) channels:", ad74413r._tx_channel_names)

print("ADT75 temperature reading:", adt75() * 62.5)

data = []

num_readings = 20
for _ in range(num_readings):
    try:
        current = ad74413r.channel["current3"].raw * ad74413r.channel["current3"].scale
        data.append(current)
        time.sleep(0.1)
    except Exception as e:
        print(f"Error reading value {e}")

voltage_dac_scale = ad74413r.channel["voltage0"].scale
voltage_dac_offset = ad74413r.channel["voltage0"].offset

def check_led_status():
    # Check if the LED is on (raw value of 8000)
    return ad74413r.channel["voltage3"].raw == 8000

# Function to turn on the fan
def turn_on_fan():
    ad74413r.channel["voltage0"].raw = 8000 
    ad74413r.channel["voltage1"].raw = 8000
    fan_button_on.configure(state="disabled")  

def turn_off_fan():
    # Your code to turn off the fan goes here
    pass
    
    
# Function to turn on/off the LED
def toggle_led():
    if not check_led_status():
        ad74413r.channel["voltage3"].raw = 8000
        messagebox.showinfo("Status:", "LED is turned ON. ")
        turn_on_fan()
    else:
        ad74413r.channel["voltage3"].raw = 0
        messagebox.showinfo("Status", "LED is turned OFF.")
        turn_off_fan()


# Set appearance mode for the UI
ctk.set_appearance_mode("dark") 
ctk.set_default_color_theme("green")  

# Create the main application window
app = ctk.CTk()
app.geometry("1000x600")
app.title("Industrial Control Application")

# Left Sidebar Frame
sidebar_frame = ctk.CTkFrame(app, width=200, corner_radius=10)
sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nswe")
sidebar_frame.grid_rowconfigure(4, weight=1)

# Sidebar Buttons
fan_button_on = ctk.CTkButton(sidebar_frame, text="Turn Fan ON", command=turn_on_fan)
fan_button_on.grid(row=0, column=0, padx=20, pady=10)

fan_button_off = ctk.CTkButton(sidebar_frame, text="Turn Fan OFF", command=turn_off_fan)
fan_button_off.grid(row=1, column=0, padx=20, pady=10)


# Main Content Frame
main_frame = ctk.CTkFrame(app, corner_radius=10)
main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
main_frame.grid_rowconfigure(0, weight=1)
main_frame.grid_columnconfigure(0, weight=1)

    
# Matplotlib Plot Integration
def plot_values(data):
    fig, ax = plt.subplots(figsize=(8, 4))
    plt.plot(data, marker='o', linestyle="-")
    plt.title("AD74413R current0 reading")
    plt.xlabel("Reading number")
    plt.ylabel("Current [mA]")
    plt.grid(True)
    # plt.show()
    return fig


fig = plot_values(data)

# Embed the plot in the Tkinter frame
canvas = FigureCanvasTkAgg(fig, master=main_frame)  # Create the canvas
canvas.get_tk_widget().grid(row=0, column=0, padx=20, pady=20, sticky="nsew")  # Place the canvas in the frame
canvas.draw()


# Segmented Button in Main Frame

# Right Widgets Frame
widgets_frame = ctk.CTkFrame(app, corner_radius=10)
widgets_frame.grid(row=0, column=2, padx=20, pady=20, sticky="nsew")
widgets_frame.grid_rowconfigure(0, weight=1)
widgets_frame.grid_columnconfigure(0, weight=1)

# Checkboxes and Switches
scrollable_frame = ctk.CTkScrollableFrame(widgets_frame, width=200)
scrollable_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

switch_1 = ctk.CTkSwitch(scrollable_frame, text="Turn LED and Fan ON/OFF", command=toggle_led)
switch_1.grid(row=0, column=0, pady=5)

checkbox_1 = ctk.CTkCheckBox(scrollable_frame, text="Read Current0 data", command=plot_values(data))
checkbox_1.grid(row=3, column=0, pady=5)

# Run the application
app.mainloop()
