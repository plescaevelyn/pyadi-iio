# Copyright (C) 2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import time
import sys
import adi
import matplotlib.pyplot as plt
import numpy as np

my_uri = sys.argv[1] if len(sys.argv) >= 2 else "local:"
print("uri: " + str(my_uri))


ada4355_dev = adi.ada4355(uri=my_uri)

ada4355_dev.rx_buffer_size = 8096
ada4355_dev.rx_enabled_channels = [0]
print("RX rx_enabled_channels: " + str(ada4355_dev.rx_enabled_channels))

print("Writing 0x00 to 0x0D to select user input test mode")
ada4355_dev.ada4355_register_write(0x0D,0x00)
print("0x0D test mode is: ", ada4355_dev.ada4355_register_read(0x0D))

# rx data

data = ada4355_dev.rx()

# plot setup

fig, (ch1) = plt.subplots(1, 1)

fig.suptitle("ADA4355 Data")
ch1.plot(data)
ch1.set_ylabel("Channel 1 amplitude")
ch1.set_xlabel("Samples")

plt.show()

ada4355_dev.rx_destroy_buffer()
