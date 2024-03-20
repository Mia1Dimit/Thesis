import csv
import matplotlib.pyplot as plt
import numpy as np

file_path = "fatigue_data_3new.csv"
with open(file_path, 'r') as file:
    reader = csv.reader(file)
    next(reader)  # Skip header row
    data = [list(map(float, row)) for row in reader]

# Transpose the data for easier plotting
data_transposed = list(map(list, zip(*data)))

# Extract individual measures
rms_values = data_transposed[0]
iemg_values = data_transposed[1]
mnf_values = data_transposed[2]
mpf_values = data_transposed[3]

# Create separate subplots
fig, axs = plt.subplots(4, 1, figsize=(10, 16))

# Plot RMS values
axs[0].plot(rms_values, label='RMS', color='blue')
axs[0].set_ylabel('RMS Values')
axs[0].set_title('RMS Values')

# Plot IEMG values
axs[1].plot(iemg_values, label='IEMG', color='orange')
axs[1].set_ylabel('IEMG Values')
axs[1].set_title('IEMG Values')

# Plot MNF and MPF values together
axs[2].plot(mnf_values, label='MNF', color='green')
axs[2].plot(mpf_values, label='MPF', color='red')
axs[2].set_ylabel('MNF/MPF Values')
axs[2].set_xlabel('Sample Index')
axs[2].set_title('MNF and MPF Values')
axs[2].legend()

output_csv_path = "algoB_data_3new.csv"
with open(output_csv_path, 'r') as file:
    reader = csv.reader(file)
    next(reader)  # Skip header row
    data = [list(map(float, row)) for row in reader]

fatigue_values = data_transposed[3]

# Plot Fatigue values
axs[3].plot(fatigue_values, label='Fatigue', color='purple')
axs[3].set_ylabel('Fatigue Values')
axs[3].set_xlabel('Sample Index')
axs[3].set_title('Fatigue Values')
axs[3].legend()

# Adjust layout for better spacing
plt.tight_layout()

# Show the subplots
plt.show()

