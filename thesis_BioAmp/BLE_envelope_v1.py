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
        self.meanAbs_values = []
        self.sample_count = 0
        self.window_size = window_size

        # First figure for EMG signal and its envelope
        plt.ion()
        self.fig_emg, ( self.ax_emg, self.ax_rms, self.ax_iemg, self.ax_mean_abs_val) = plt.subplots(4)
        self.line_emg, = self.ax_emg.plot([], [], 'b-', label='EMG Data')
        self.envelope_line_emg, = self.ax_emg.plot([], [], 'r-', label='Envelope')
        self.line_rms, = self.ax_rms.plot([], [], 'g-', label='RMS')
        self.line_iemg, = self.ax_iemg.plot([], [], 'm-', label='IEMG')
        self.line_mean_abs_val, = self.ax_mean_abs_val.plot([], [], 'c-', label='Mean Abs Val')

        # Set labels and legends
        self.ax_emg.set_xlabel('Number of Samples')
        self.ax_emg.set_ylabel('EMG Amplitude')
        #self.ax_emg.set_title('Real-time EMG Data')
        self.ax_emg.set_ylim(-200.0, 200.0)
        self.ax_emg.set_xlim(0, self.window_size)
        self.ax_emg.legend()

        self.ax_rms.set_xlabel('Number of Samples')
        self.ax_rms.set_ylabel('RMS Value')
        #self.ax_rms.set_title('RMS')
        self.ax_rms.set_ylim(-100.0, 100.0)
        self.ax_rms.legend()

        self.ax_iemg.set_xlabel('Number of Samples')
        self.ax_iemg.set_ylabel('IEMG Value')
        #self.ax_iemg.set_title('IEMG')
        self.ax_iemg.set_ylim(-100.0, 100.0)
        self.ax_iemg.legend()

        self.ax_mean_abs_val.set_xlabel('Number of Samples')
        self.ax_mean_abs_val.set_ylabel('Mean Abs Val Value')
        #self.ax_mean_abs_val.set_title('Mean Abs Val')
        self.ax_mean_abs_val.set_ylim(-100.0, 100.0)
        self.ax_mean_abs_val.legend()        

        self.buffer_size = 208
        self.circular_buffer = [0] * self.buffer_size
        self.sum_buffer = 0
        self.data_index = 0

    # Modify the set_data_and_plot method
    def set_data_and_plot(self):
        start_index = max(0, self.sample_count - self.window_size)
        end_index = min(self.sample_count, start_index + self.window_size)

        # Update EMG signal and envelope plot
        self.line_emg.set_data(range(0, end_index), self.amplitudes[0:end_index])
        self.envelope_line_emg.set_data(range(0, end_index), self.envelope_values[0:end_index])
        self.ax_emg.set_xlim(start_index, end_index)

        # Update RMS, IEMG, and MeanAbsVal plots
        self.line_rms.set_data(range(0, end_index), self.rms_values[0:end_index])
        self.ax_rms.set_xlim(start_index, end_index)
        self.line_iemg.set_data(range(0, end_index), self.iemg_values[0:end_index])
        self.ax_iemg.set_xlim(start_index, end_index)
        self.line_mean_abs_val.set_data(range(0, end_index), self.meanAbs_values[0:end_index])
        self.ax_mean_abs_val.set_xlim(start_index, end_index)

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
                self.rms_values.append(self.calculate_rms(val))
                self.iemg_values.append(self.calculate_iemg(val))
                self.meanAbs_values.append(self.calculate_mean_abs_val(val))

    def calculate_envelope(self, abs_emg):
        self.sum_buffer -= self.circular_buffer[self.data_index]
        self.sum_buffer += abs_emg
        self.circular_buffer[self.data_index] = abs_emg
        self.data_index = (self.data_index + 1) % self.buffer_size        
        return (self.sum_buffer / self.buffer_size) * 2

    def calculate_rms(self,rms_val):
        rms_value = np.sqrt(np.mean(np.square(rms_val)))
        return rms_value

    def calculate_mean_abs_val(self,iemg_val):
        return np.mean(np.abs(iemg_val))

    def calculate_iemg(self,mean_abs__val):
        cumulative_sum = np.cumsum(np.abs(mean_abs__val))
        return cumulative_sum[-1]  # return the sum of the windowed values


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
