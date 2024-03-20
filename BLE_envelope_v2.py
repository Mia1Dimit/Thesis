import asyncio
from bleak import BleakClient
import struct
import matplotlib.pyplot as plt
import numpy as np

device_address = 'f4:12:fa:63:47:29'
filtered_characteristic_uuid = "a3b1a544-8794-11ee-b9d1-0242ac120002"

class RealTimePlotter:
    def __init__(self, window_size=1500):
        self.received_data = bytearray()
        self.amplitudes = []
        self.envelope_values = []  
        self.rms_values = []
        self.iemg_values = []
        self.sample_count = 0
        self.window_size = window_size

        # First figure for EMG signal and its envelope
        plt.ion()
        self.fig_emg, ( self.ax_emg, self.ax_env, self.ax_rms, self.ax_iemg) = plt.subplots(4)
        self.line_emg, = self.ax_emg.plot([], [], 'b-', label='EMG Data')
        self.envelope_line_emg, = self.ax_env.plot([], [], 'r-', label='Envelope')
        self.line_rms, = self.ax_rms.plot([], [], 'g-', label='RMS')
        self.line_iemg, = self.ax_iemg.plot([], [], 'm-', label='IEMG')

        # Set labels and legends
        self.ax_emg.set_xlabel('Number of Samples')
        self.ax_emg.set_ylabel('EMG Amplitude')
        #self.ax_emg.set_title('Real-time EMG Data')
        self.ax_emg.set_ylim(-1000.0, 1000.0)
        self.ax_emg.set_xlim(0, self.window_size)
        self.ax_emg.legend()

        self.ax_env.set_xlabel('Number of Samples')
        self.ax_env.set_ylabel('EMG Envelope')
        #self.ax_env.set_title('Envelope EMG')
        self.ax_env.set_ylim(-500.0, 500.0)
        self.ax_env.set_xlim(0, self.window_size)
        self.ax_env.legend()

        self.ax_rms.set_xlabel('Number of Samples')
        self.ax_rms.set_ylabel('RMS Value')
        #self.ax_rms.set_title('RMS')
        self.ax_rms.set_ylim(-1000.0, 1000.0)
        self.ax_rms.legend()

        self.ax_iemg.set_xlabel('Number of Samples')
        self.ax_iemg.set_ylabel('IEMG Value')
        #self.ax_iemg.set_title('IEMG')
        self.ax_iemg.set_ylim(-1000.0, 1000.0)
        self.ax_iemg.legend()

        self.buffer_size = 208
        self.circular_buffer = [0] * self.buffer_size
        self.sum_buffer = 0
        self.data_index = 0

    # Modify the set_data_and_plot method
    def set_data_and_plot(self):
        print("Length of amplitudes:", len(self.amplitudes))
        print("Length of envelope values:", len(self.envelope_values))
        print("Length of rms_values:", len(self.rms_values))
        print("Length of iemg_values:", len(self.iemg_values))
        start_index = max(0, self.sample_count - self.window_size)
        end_index = min(self.sample_count, start_index + self.window_size)

        # Update EMG signal and envelope plot
        self.line_emg.set_data(range(0, end_index), self.amplitudes[0:end_index])
        self.envelope_line_emg.set_data(range(0, end_index), self.envelope_values[0:end_index])
        self.ax_emg.set_xlim(start_index, end_index)

        # Update RMS, IEMG, and MeanAbsVal plots
        self.line_rms.set_data(range(0, len(self.rms_values)), self.rms_values[0:len(self.rms_values)])
        self.ax_rms.set_xlim(0, len(self.rms_values))
        self.line_iemg.set_data(range(0, len(self.iemg_values)), self.iemg_values[0:len(self.iemg_values)])
        self.ax_iemg.set_xlim(0, len(self.iemg_values))

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

            step = 100
            for i in range(0, len(self.amplitudes) - 1000 + 1, step):
                epoch_data = self.amplitudes[i:i+1000]
                self.rms_values.append(self.calculate_rms(epoch_data))
                self.iemg_values.append(self.calculate_iemg(epoch_data))

    # Modify calculate_envelope to accept an array
    def calculate_envelope(self, abs_emg_value):
        self.sum_buffer -= self.circular_buffer[self.data_index]
        self.sum_buffer += abs_emg_value
        self.circular_buffer[self.data_index] = abs_emg_value
        self.data_index = (self.data_index + 1) % self.buffer_size
        return (self.sum_buffer / self.buffer_size) * 2
        

    def calculate_rms(self,rms_val):
        return np.sqrt(np.mean(np.square(rms_val)))         

    def calculate_iemg(self,iemg_values):
        calculated_value = np.sum(np.abs(iemg_values))
        #print(f"Calculated IEMG: {calculated_value}")
        return calculated_value 


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
        await client.start_notify(filtered_characteristic_uuid, lambda sender, data: asyncio.ensure_future(notification_handler_wrapper(sender, data, plotter)))

        # Concurrently run notification handling, plotting, and calculations
        await asyncio.gather(plot_handler(plotter), asyncio.sleep(0))

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('\n\n *** Interrupted.\n')
