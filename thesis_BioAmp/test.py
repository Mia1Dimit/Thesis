import matplotlib.pyplot as plt
import numpy as np

def plot_signal_time_frequency(file_path):
    values = []
    with open(file_path, 'r') as file:
        lines = file.readlines()
        for line in lines:
            floats = line.strip().split(', ')
            values.extend([float(val) for val in floats])

    # Calculate the time domain plot (Number of Samples vs Received Float Values)
    num_samples = len(values)
    x_axis_time = np.arange(num_samples)

    plt.figure(figsize=(10, 6))

    plt.subplot(2, 1, 1)  # Top subplot for time domain
    plt.plot(x_axis_time, values, marker='o', linestyle='-')
    plt.xlabel('Number of Samples')
    plt.ylabel('Received Float Values')
    plt.title('Received Signal in Time Domain')
    plt.grid(True)

    # Calculate the frequency domain plot using FFT
    sampling_rate = 500  # Sample rate in Hz (500 samples per second)
    freq_domain = np.fft.fft(values)
    freq_domain = np.abs(freq_domain)[:num_samples//2]  # Only positive frequencies
    frequencies = np.fft.fftfreq(num_samples, d=1/sampling_rate)[:num_samples//2]

    plt.subplot(2, 1, 2)  # Bottom subplot for frequency domain
    plt.plot(frequencies, freq_domain)
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Amplitude')
    plt.title('Signal in Frequency Domain')
    plt.grid(True)

    plt.tight_layout()
    plt.show()

file_path = "received_floats.txt"  # Replace with the path to your file
plot_signal_time_frequency(file_path)
