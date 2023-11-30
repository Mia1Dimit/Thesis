import asyncio
from bleak import BleakClient
import struct
import matplotlib.pyplot as plt

class RealTimePlotter:
    def __init__(self, window_size=3120):
        self.received_data = bytearray()
        self.amplitudes = []
        self.sample_count = 0
        self.window_size = window_size
        
        plt.ion()  # Turn on interactive mode
        self.fig, self.ax = plt.subplots()
        self.line, = self.ax.plot([], [], 'b-')
        self.ax.set_xlabel('Number of Samples')
        self.ax.set_ylabel('EMG Amplitude')
        self.ax.set_title('Real-time EMG Data')
        self.ax.set_ylim(-200.0, 200.0)
        self.ax.set_xlim(0, self.window_size)

    def set_data_and_plot(self):
        start_index = max(0, self.sample_count - self.window_size)
        end_index = min(self.sample_count, start_index + self.window_size)
        self.line.set_data(range(start_index, end_index), self.amplitudes[start_index:end_index])
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
            

async def notification_handler_wrapper(sender, data, plotter):
    await notification_handler(sender, data, plotter)

async def notification_handler(sender, data, plotter):
    plotter.update_received_data(data)

async def plot_handler(plotter):
    while True:
        plotter.set_data_and_plot()
        await asyncio.sleep(0.1)

async def main():
    device_address = 'f4:12:fa:63:47:29'
    filtered_characteristic_uuid = "a3b1a544-8794-11ee-b9d1-0242ac120002"
    
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
