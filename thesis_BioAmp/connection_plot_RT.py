import asyncio
from bleak import BleakClient
import struct
import matplotlib.pyplot as plt

device_address = 'f4:12:fa:63:47:29'
filtered_characteristic_uuid = "a3b1a544-8794-11ee-b9d1-0242ac120002"

class RealTimePlotter:
    def __init__(self, window_size=1500):
        self.received_data = bytearray()
        self.amplitudes = []
        self.envelope_values = []  
        self.sample_count = 0
        self.window_size = window_size
        
        plt.ion()  # Turn on interactive mode
        self.fig, self.ax = plt.subplots()
        self.line, = self.ax.plot([], [], 'b-', label='EMG Data')
        self.envelope_line, = self.ax.plot([], [], 'r-', label='Envelope')  
        self.ax.set_xlabel('Number of Samples')
        self.ax.set_ylabel('EMG Amplitude')
        self.ax.set_title('Real-time EMG Data')
        self.ax.set_ylim(-200.0, 200.0)
        self.ax.set_xlim(0, self.window_size)
        self.ax.legend()

        self.buffer_size = 208
        self.circular_buffer = [0] * self.buffer_size
        self.sum_buffer = 0
        self.data_index = 0

    def set_data_and_plot(self):
        start_index = max(0, self.sample_count - self.window_size)
        end_index = min(self.sample_count, start_index + self.window_size)
        self.line.set_data(range(0, end_index), self.amplitudes[0:end_index])
        self.envelope_line.set_data(range(0, end_index), self.envelope_values[0:end_index])
        self.ax.set_xlim(start_index, end_index)
        plt.pause(0.01)

    def update_received_data(self, data):
        self.received_data.extend(data)
        while len(self.received_data) >= 208:
            packet = self.received_data[:208]
            self.received_data = self.received_data[208:]
            floats = [struct.unpack('f', packet[i:i+4])[0] for i in range(0, 208, 4)]
            self.amplitudes.extend(floats)
            self.sample_count = len(self.amplitudes)
            for val in floats:                
                self.envelope_values.append(self.calculate_envelope(abs(val)))

 
    def calculate_envelope(self, abs_emg):
        self.sum_buffer -= self.circular_buffer[self.data_index]
        self.sum_buffer += abs_emg
        self.circular_buffer[self.data_index] = abs_emg
        self.data_index = (self.data_index + 1) % self.buffer_size

        return (self.sum_buffer / self.buffer_size) * 2

async def notification_handler_wrapper(sender, data, plotter):
    await notification_handler(sender, data, plotter)

async def notification_handler(sender, data, plotter):
    plotter.update_received_data(data)

async def plot_handler(plotter):
    while True:
        plotter.set_data_and_plot()
        await asyncio.sleep(0.1)

async def main():    
    plotter = RealTimePlotter()

    client = BleakClient(device_address)

    await client.connect()
    if client.is_connected:
        print(f"Connected to device with MAC address: {client.address}")
         
        # Enable notifications for the filtered characteristic
        await client.start_notify(filtered_characteristic_uuid, 
                                  lambda sender, data: asyncio.ensure_future(notification_handler_wrapper(sender, data, plotter)))

        # Concurrently run notification handling and plotting
        await asyncio.gather(plot_handler(plotter), asyncio.sleep(0))

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('\n\n *** Interrupted.\n')
