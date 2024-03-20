import asyncio
from bleak import BleakClient
import struct
import matplotlib.pyplot as plt
import numpy as np

device_address = 'f4:12:fa:63:47:29'
filtered_characteristic_uuid = "a3b1a544-8794-11ee-b9d1-0242ac120002"

class RealTimePlotter:
    def __init__(self, window_size=1000):
        self.received_data = bytearray()
        self.amplitudes = []
        self.envelope_values = []  
        self.rms_values = []
        self.iemg_values = []
        self.fft_values = []
        self.mnf_values = []
        self.mpf_values = []
        self.sample_count = 0
        self.window_size = window_size
        self.start_index = 0
        self.end_index = 1000

        # First figure for EMG signal and its envelope
        plt.ion()
        self.fig_emg, ( self.ax_emg, self.ax_fft, self.ax_rms, self.ax_iemg, self.ax_mnf) = plt.subplots(5)
        self.line_emg, = self.ax_emg.plot([], [], 'b-', label='EMG Data')
        self.envelope_line_emg, = self.ax_emg.plot([], [], 'r-', label='Envelope')
        self.line_fft, = self.ax_fft.plot([], [], 'b-', label='FFT')
        self.line_rms, = self.ax_rms.plot([], [], 'g-', label='RMS')
        self.line_iemg, = self.ax_iemg.plot([], [], 'm-', label='IEMG')
        self.line_mnf, = self.ax_mnf.plot([], [], 'r-', label='MNF')
        self.line_mpf, = self.ax_mnf.plot([], [], 'g-', label='MPF')

        # Set labels and legends
        self.ax_emg.set_xlabel('Number of Samples')
        self.ax_emg.set_ylabel('EMG Amplitude')
        #self.ax_emg.set_title('Real-time EMG Data')
        self.ax_emg.set_ylim(-75.0, 75.0)
        #self.ax_emg.set_xlim(0, self.window_size)
        self.ax_emg.legend()

        self.ax_fft.set_xlabel('Frequency (Hz)')
        self.ax_fft.set_ylabel('Power')
        #self.ax_fft.set_title('FFT EMG')
        self.ax_fft.set_ylim(-2000.0, 2000.0)
        #self.ax_fft.set_xlim(0, self.window_size)
        self.ax_fft.legend()

        self.ax_rms.set_xlabel('Number of Samples')
        self.ax_rms.set_ylabel('RMS Value')
        #self.ax_rms.set_title('RMS')
        self.ax_rms.set_ylim(-100.0, 100.0)
        self.ax_rms.legend()

        self.ax_iemg.set_xlabel('Number of Samples')
        self.ax_iemg.set_ylabel('IEMG Value')
        #self.ax_iemg.set_title('IEMG')
        self.ax_iemg.set_ylim(-800.0, 800.0)
        self.ax_iemg.legend()

        # Set labels and legends for the frequency plot
        self.ax_mnf.set_xlabel('Number of Samples')
        self.ax_mnf.set_ylabel('Frequency (Hz)')
        #self.ax_mnf.set_title('MNF/MPF')
        self.ax_mnf.set_ylim(-500.0, 750.0)  
        self.ax_mnf.legend()

        self.buffer_size = 208
        self.circular_buffer = [0] * self.buffer_size
        self.sum_buffer = 0
        self.data_index = 0

    # Modify the set_data_and_plot method
    def set_data_and_plot(self):
        #start_index = max(0, self.sample_count - self.window_size)
        #end_index = min(self.sample_count, start_index + self.window_size)

        # Update EMG signal and envelope plot
        self.line_emg.set_data(range(0, len(self.amplitudes)), self.amplitudes[0:len(self.amplitudes)])        
        self.envelope_line_emg.set_data(range(0, len(self.envelope_values)), self.envelope_values[0:len(self.envelope_values)])
        self.ax_emg.set_xlim(0, self.sample_count)
        

        if(len(self.fft_values)>=1000):
            fft_freq = np.fft.fftfreq(1000, d=1/500)
            print("frequencies: ", len(fft_freq))
            print("magnitudes: ", self.fft_values[-1000:])
            self.line_fft.set_data(fft_freq , self.fft_values[-1000:])
            self.ax_fft.set_xlim(0, len(fft_freq)/2)

        # Update RMS, IEMG plots
        self.line_rms.set_data(range(0, len(self.rms_values)), self.rms_values[0:len(self.rms_values)])
        self.ax_rms.set_xlim(0, len(self.rms_values))

        self.line_iemg.set_data(range(0, len(self.iemg_values)), self.iemg_values[0:len(self.iemg_values)])
        self.ax_iemg.set_xlim(0, len(self.iemg_values))

        print("Length of mnf_values:", self.mnf_values[0:len(self.mnf_values)])
        print("Length of mpf_values:", self.mpf_values[0:len(self.mpf_values)])
        self.line_mnf.set_data(range(0, len(self.mnf_values)), self.mnf_values[0:len(self.mnf_values)])
        self.line_mpf.set_data(range(0, len(self.mpf_values)), self.mpf_values[0:len(self.mpf_values)])
        self.ax_mnf.set_xlim(0, len(self.mnf_values))

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

            print("Length of amplitudes:", len(self.amplitudes))
            print("Length of envelope_values:", len(self.envelope_values))

        step = 100
        if (len(self.amplitudes) >= 1000 + self.start_index):                
            epoch_data = self.amplitudes[self.start_index:self.end_index]
            self.rms_values.append(self.calculate_rms(epoch_data))
            self.iemg_values.append(self.calculate_iemg(epoch_data))

            fft_result = np.fft.fft(epoch_data)
            freq_values = np.fft.fftfreq(len(epoch_data), d=1/500) 
            self.fft_values.extend(np.abs(fft_result))
            self.mnf_values.append(self.calculate_mnf(freq_values, fft_result))
            self.mpf_values.append(self.calculate_mpf(freq_values, fft_result))
            self.start_index +=step
            self.end_index = self.window_size + self.start_index
        

    def calculate_envelope(self, abs_emg_value):
        self.sum_buffer -= self.circular_buffer[self.data_index]
        self.sum_buffer += abs_emg_value
        self.circular_buffer[self.data_index] = abs_emg_value
        self.data_index = (self.data_index + 1) % self.buffer_size
        return (self.sum_buffer / self.buffer_size) * 2        

    def calculate_rms(self,rms_val):
        return np.sqrt(np.mean(np.square(rms_val)))         

    def calculate_iemg(self,iemg_values):
        return np.sum(np.abs(iemg_values)) 
    
    def calculate_mnf(self, freq_values, fft_result):
        mnf = np.sum(freq_values * np.abs(fft_result)**2) / np.sum(np.abs(fft_result)**2)
        return mnf

    def calculate_mpf(self, freq_values, fft_result):
        power_spectrum = np.abs(fft_result)**2
        total_power = np.sum(power_spectrum)
        cumulative_power = np.cumsum(power_spectrum)
        mpf_index = np.argmax(cumulative_power >= 0.5 * total_power)
        mpf = freq_values[mpf_index]
        return mpf

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
