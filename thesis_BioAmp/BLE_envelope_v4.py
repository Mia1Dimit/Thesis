import asyncio
from bleak import BleakClient
import struct
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import butter, filtfilt
import keyboard

device_address = 'f4:12:fa:63:47:29'
filtered_characteristic_uuid = "a3b1a544-8794-11ee-b9d1-0242ac120002"
sampling_freq = 800

class CtrlAPressed(Exception):
    pass

class RealTimePlotter:
    def __init__(self, window_size=1000):
        self.received_data = bytearray()
        self.amplitudes = []
        self.envelope_values = []  
        self.rms_values = []
        self.iemg_values = []
        self.mnf_values = []
        self.mpf_values = []
        self.fatigue_A_values = []
        self.fatigue_B_values = []
        self.sample_count = 0
        self.window_size = window_size
        self.start_index = 0
        self.end_index = 800
        self.baseline_initialized = False
        self.iemg_initial = None
        self.fatigue_start_index = 0
        self.packet_index = 0


        # First figure for EMG signal and its envelope
        plt.ion()
        self.fig_emg, ( self.ax_emg, self.ax_rms, self.ax_iemg, self.ax_mnf) = plt.subplots(4)
        self.line_emg, = self.ax_emg.plot([], [], 'b-', label='EMG Data')
        self.envelope_line_emg, = self.ax_emg.plot([], [], 'r-', label='Envelope')
        self.line_rms, = self.ax_rms.plot([], [], 'g-', label='RMS')
        self.line_iemg, = self.ax_iemg.plot([], [], 'm-', label='IEMG')
        self.line_mnf, = self.ax_mnf.plot([], [], 'r-', label='MNF')
        self.line_mpf, = self.ax_mnf.plot([], [], 'g-', label='MPF')

        # Set labels and legends
        self.ax_emg.set_xlabel('Time (sec)')
        self.ax_emg.set_ylabel('EMG Amplitude')
        #self.ax_emg.set_title('Real-time EMG Data')
        self.ax_emg.set_ylim(-75.0, 75.0)
        #self.ax_emg.set_xlim(0, self.window_size)
        self.ax_emg.legend()

        self.ax_rms.set_xlabel('Time (sec)')
        self.ax_rms.set_ylabel('RMS Value')
        #self.ax_rms.set_title('RMS')
        self.ax_rms.set_ylim(0.0, 100.0)
        self.ax_rms.legend()

        self.ax_iemg.set_xlabel('Time (sec)')
        self.ax_iemg.set_ylabel('IEMG Value')
        #self.ax_iemg.set_title('IEMG')
        self.ax_iemg.set_ylim(0.0, 15000.0)
        self.ax_iemg.legend()

        # Set labels and legends for the frequency plot
        self.ax_mnf.set_xlabel('Time (sec)')
        self.ax_mnf.set_ylabel('Frequency (Hz)')
        #self.ax_mnf.set_title('MNF/MPF')
        self.ax_mnf.set_ylim(0.0, 200.0)
        self.ax_mnf.legend()

        self.buffer_size = 208
        self.circular_buffer = [0] * self.buffer_size
        self.sum_buffer = 0
        self.data_index = 0

        # Add a new figure for plotting fatigue values
        self.fig_fatigue, (self.ax_fatigue_A, self.ax_fatigue_B) = plt.subplots(2)
        self.line_fatigue_A, = self.ax_fatigue_A.plot([], [], 'b-', label='Fatigue A')
        self.line_fatigue_B, = self.ax_fatigue_B.plot([], [], 'r-', label='Fatigue B')

        # Set labels and legends for fatigue plots
        self.ax_fatigue_A.set_xlabel('Time (sec)')
        self.ax_fatigue_A.set_ylabel('Fatigue A Level')
        self.ax_fatigue_A.set_ylim(-500.0, 500.0)
        self.ax_fatigue_A.legend()

        self.ax_fatigue_B.set_xlabel('Time (sec)')
        self.ax_fatigue_B.set_ylabel('Fatigue B Level')
        self.ax_fatigue_B.set_ylim(-500.0, 500.0)
        self.ax_fatigue_B.legend()

    def raise_ctrl_a_exception(self):
        if keyboard.is_pressed('ctrl+a'):
            raise CtrlAPressed
        
    def set_data_and_plot(self):

        try:
            self.raise_ctrl_a_exception()
            # Update EMG signal and envelope plot
            self.line_emg.set_data(range(0, len(self.amplitudes)), self.amplitudes[0:len(self.amplitudes)])        
            self.envelope_line_emg.set_data(range(0, len(self.envelope_values)), self.envelope_values[0:len(self.envelope_values)])
            self.ax_emg.set_xlim(0, self.sample_count)

            # Update RMS, IEMG plots
            self.line_rms.set_data(range(0, len(self.rms_values)), self.rms_values[0:len(self.rms_values)])
            self.ax_rms.set_xlim(0, len(self.rms_values))

            self.line_iemg.set_data(range(0, len(self.iemg_values)), self.iemg_values[0:len(self.iemg_values)])
            self.ax_iemg.set_xlim(0, len(self.iemg_values))

            #print("Length of mnf_values:", self.mnf_values[0:len(self.mnf_values)])
            #print("Length of mpf_values:", self.mpf_values[0:len(self.mpf_values)])
            self.line_mnf.set_data(range(0, len(self.mnf_values)), self.mnf_values[0:len(self.mnf_values)])
            self.line_mpf.set_data(range(0, len(self.mpf_values)), self.mpf_values[0:len(self.mpf_values)])
            self.ax_mnf.set_xlim(0, len(self.mnf_values))

            # Update fatigue plots
            self.line_fatigue_A.set_data(range(0, len(self.fatigue_A_values)), self.fatigue_A_values[0:len(self.fatigue_A_values)])
            self.line_fatigue_B.set_data(range(0, len(self.fatigue_B_values)), self.fatigue_B_values[0:len(self.fatigue_B_values)])
            
            # Set xlim for fatigue plots
            self.ax_fatigue_A.set_xlim(0, len(self.fatigue_A_values))
            self.ax_fatigue_B.set_xlim(0, len(self.fatigue_B_values))

            plt.pause(0.01)
        except CtrlAPressed:
            print("Ctrl+A pressed. Disconnecting device and plotting final data.")
            raise

    def plot_final_data(self):
        self.line_emg.set_data(range(0, len(self.amplitudes)), self.amplitudes[0:len(self.amplitudes)])        
        self.envelope_line_emg.set_data(range(0, len(self.envelope_values)), self.envelope_values[0:len(self.envelope_values)])
        self.ax_emg.set_xlim(0, self.sample_count)
        
        self.line_rms.set_data(range(0, len(self.rms_values)), self.rms_values[0:len(self.rms_values)])
        self.ax_rms.set_xlim(0, len(self.rms_values))

        self.line_iemg.set_data(range(0, len(self.iemg_values)), self.iemg_values[0:len(self.iemg_values)])
        self.ax_iemg.set_xlim(0, len(self.iemg_values))

        self.line_mnf.set_data(range(0, len(self.mnf_values)), self.mnf_values[0:len(self.mnf_values)])
        self.line_mpf.set_data(range(0, len(self.mpf_values)), self.mpf_values[0:len(self.mpf_values)])
        self.ax_mnf.set_xlim(0, len(self.mnf_values))

        self.line_fatigue_A.set_data(range(0, len(self.fatigue_A_values)), self.fatigue_A_values[0:len(self.fatigue_A_values)])
        self.line_fatigue_B.set_data(range(0, len(self.fatigue_B_values)), self.fatigue_B_values[0:len(self.fatigue_B_values)])
        self.ax_fatigue_A.set_xlim(0, len(self.fatigue_A_values))
        self.ax_fatigue_B.set_xlim(0, len(self.fatigue_B_values))

        data_to_save = np.vstack((self.rms_values, self.iemg_values, self.mnf_values, self.mpf_values)).T
        fatigue_data = np.vstack((self.fatigue_A_values)).T

        np.savetxt('non_output_data3.csv', data_to_save, delimiter=',', header="RMS, IEMG, MNF, MPF", comments='')
        np.savetxt('non_fatigue_data3.csv', fatigue_data, delimiter=',', header="Fatigue A", comments='')
        plt.show(block=False)

    def update_received_data(self, data):
        self.received_data.extend(data)

        while len(self.received_data) >= 244:
            packet = self.received_data[:244]
            self.packet_index += 1
            print("num of packets:", self.packet_index)
            self.received_data = self.received_data[244:]
            floats = [struct.unpack('f', packet[i:i+4])[0] for i in range(0, 244, 4)]
            self.amplitudes.extend(floats)
            self.sample_count = len(self.amplitudes)

            for val in floats:
                self.envelope_values.append(self.calculate_envelope(abs(val)))

            #print("Length of amplitudes:", len(self.amplitudes))
            #print("Length of envelope_values:", len(self.envelope_values))

        step = 400
        if (len(self.amplitudes) >= 800 + self.start_index):                
            epoch_data = self.amplitudes[self.start_index:self.end_index]
            self.rms_values.append(self.calculate_rms(epoch_data))
            self.iemg_values.append(self.calculate_iemg(epoch_data))

            fft_result = np.fft.fft(epoch_data)
            freq_values = np.fft.fftfreq(len(epoch_data), d=1/500) 
            positive_freq_mask = freq_values >= 0
            positive_freq_values = freq_values[positive_freq_mask]
            positive_fft_values = fft_result[positive_freq_mask]

            self.mnf_values.append(self.calculate_mnf(positive_freq_values, positive_fft_values))
            self.mpf_values.append(self.calculate_mpf(positive_freq_values, positive_fft_values))
            self.start_index +=step
            self.end_index += self.start_index
        
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

    def algorithm_A_fatigue(self):
        if len(self.mpf_values) >= 6 + self.fatigue_start_index:  
            if not self.baseline_initialized:
                self.baseline = np.mean(self.mpf_values[:3])
                print("Baseline value:", self.baseline)
                self.baseline_initialized = True

            self.fatigue_start_index += 3
            recent_mpf_values = self.mpf_values[-3:]
            average_mpf = np.mean(recent_mpf_values)

            if average_mpf >= self.baseline:
                self.baseline = average_mpf
            
            fatigue_level = ((self.baseline - average_mpf) / self.baseline) * 100
            self.fatigue_A_values.append(fatigue_level)
            print(f"Fatigue Level: {fatigue_level}")

    def algorithm_B_fatigue(self):
        if (len(self.iemg_values) >= 3 + self.fatigue_start_index):  
            iemg_current = np.mean(self.iemg_values[-3:])
            self.fatigue_start_index += 3

            if self.iemg_initial is None:
                self.iemg_initial = iemg_current
                print("Initial IEMG value:", self.iemg_initial)

            if iemg_current > self.iemg_initial:
                print("Algorithm B Triggered")
                # Step 1: Separate EMG signal based on the frequency of 80Hz
                lfc, hfc = self.butterworth_bandpass_filter(self.amplitudes)

                # Step 2: Calculate FFT of the Low Frequency Component (LFC) and High Frequency Component (HFC)
                fft_lfc = np.fft.fft(lfc)
                fft_hfc = np.fft.fft(hfc)

                # Step 3: Calculate Instantaneous Mean Amplitude of LFC and HFC
                ima_lfc = np.sum(np.abs(fft_lfc)) / len(fft_lfc)
                ima_hfc = np.sum(np.abs(fft_hfc)) / len(fft_hfc)

                # Step 4: Calculate Fatigue Index
                fatigue_index = ima_lfc - ima_hfc
                self.fatigue_B_values.append(fatigue_index)
                print(f"Fatigue Index: {fatigue_index}")
            else:
                self.fatigue_B_values.append(0)

    def butterworth_bandpass_filter(self, signal):
        def butter_bandpass(lowcut, highcut, fs, order=4):
            nyquist = 0.5 * fs
            low = lowcut / nyquist
            high = highcut / nyquist
            b, a = butter(order, [low, high], btype='band')
            return b, a

        # Filter 1: 25-79Hz
        lowcut1, highcut1 = 25.0, 79.0
        b1, a1 = butter_bandpass(lowcut1, highcut1, fs=800.0)
        lfc = filtfilt(b1, a1, signal)

        # Filter 2: 80-350Hz
        lowcut2, highcut2 = 80.0, 350.0
        b2, a2 = butter_bandpass(lowcut2, highcut2, fs=800.0)
        hfc = filtfilt(b2, a2, signal)

        return lfc, hfc


async def notification_handler_wrapper(sender, data, plotter):
    await notification_handler(sender, data, plotter)

async def notification_handler(sender, data, plotter):
    plotter.update_received_data(data)
    plotter.algorithm_A_fatigue()
    #plotter.algorithm_B_fatigue()

async def plot_handler(plotter):
    while True:
        plotter.set_data_and_plot()
        await asyncio.sleep(0.1)

async def main():
    plotter = RealTimePlotter()

    client = BleakClient(device_address)

    try:
        await client.connect()
        if client.is_connected:
            print(f"Connected to device with MAC address: {client.address}")

            # Enable notifications for the filtered characteristic
            await client.start_notify(filtered_characteristic_uuid, lambda sender, data: asyncio.ensure_future(notification_handler_wrapper(sender, data, plotter)))

            # Concurrently run notification handling, plotting, and calculations
            await asyncio.gather(plot_handler(plotter), asyncio.sleep(0))

    except CtrlAPressed:
        plotter.plot_final_data()
        await client.disconnect()
        while True:
            try:
                user_input = input("Press Enter to exit.")
                if user_input == "":
                    break
            except KeyboardInterrupt:
                pass
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        await client.disconnect()
           

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('\n\n *** Interrupted.\n')
