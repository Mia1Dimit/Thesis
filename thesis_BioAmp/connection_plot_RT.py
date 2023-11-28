import asyncio
from bleak import BleakClient
import struct
import matplotlib.pyplot as plt

device_address = 'f4:12:fa:63:47:29'
raw_characteristic_uuid = "b817f6da-8796-11ee-b9d1-0242ac120002"
filtered_characteristic_uuid = "a3b1a544-8794-11ee-b9d1-0242ac120002"

# Initialize variables for received data and plotting
received_data = bytearray()
amplitudes = []
sample_count = 0

# Plotting function
def plot_data():
    window_size = 3120
    start_index = max(0, sample_count - window_size)
    end_index = min(sample_count, start_index + window_size)
    plt.plot(range(start_index, end_index), amplitudes[start_index:end_index], 'b-')
    plt.xlabel('Number of Samples')
    plt.ylabel('EMG Amplitude')
    plt.title('Real-time EMG Data')
    plt.ylim(-200.0,200.0)  # Set fixed limits for y-axis
    plt.xlim(max(0, sample_count - window_size), sample_count)  # Fix x-axis range to 3120 values
    plt.show(block=False)
    plt.pause(0.01)

# Notification handler to receive data
async def notification_handler(sender, data):
    global received_data
    received_data.extend(data)

# Process received packets
async def process_packets():
    global received_data, amplitudes, sample_count
    while len(received_data) >= 208:  # Check if at least one full packet is received
        packet = received_data[:208]  # Extract one packet (208 bytes = 52 floats)
        received_data = received_data[208:]  # Remove processed packet from received_data
        floats = [struct.unpack('f', packet[i:i+4])[0] for i in range(0, 208, 4)]  # Translate bytearray to floats

        # Update data for plotting
        for f in floats:
            amplitudes.append(f)
            sample_count += 1

        # Plot the data
        plot_data()

async def main():
    global received_data

    plt.ion()  # Turn on interactive mode

    async with BleakClient(device_address) as client:
        try:
            if client.is_connected:
                print(f"Connected to device with MAC address: {client.address}")

                # Enable notifications for the raw characteristic
                await client.start_notify(raw_characteristic_uuid, notification_handler)

                # Enable notifications for the filtered characteristic
                await client.start_notify(filtered_characteristic_uuid, notification_handler)

                # Keep receiving data and plot periodically
                while True:
                    await asyncio.sleep(1)  # Wait for data without interfering with the reception                    
                    await process_packets()
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            plt.show()  # Display the plot window after disconnecting

# Run the main function
asyncio.run(main())
