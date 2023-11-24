import asyncio
from bleak import BleakClient
import struct
import matplotlib.pyplot as plt

device_address = 'F4:12:FA:63:47:29'
raw_characteristic_uuid = "b817f6da-8796-11ee-b9d1-0242ac120002"
filtered_characteristic_uuid = "a3b1a544-8794-11ee-b9d1-0242ac120002"

# Define your notification_handler function
async def notification_handler(sender, data):
    global received_data
    received_data.extend(data)

def process_packets():
    global received_data
    while len(received_data) >= 208:  # Check if at least one full packet is received
        packet = received_data[:208]  # Extract one packet (208 bytes = 52 floats)
        received_data = received_data[208:]  # Remove processed packet from received_data
        floats = [struct.unpack('f', packet[i:i+4])[0] for i in range(0, 208, 4)]  # Translate bytearray to floats

        # Write the floats to a text file
        with open("received_floats.txt", "a") as file:
            file.write(', '.join(map(str, floats)) + '\n')

async def main():
    global received_data
    received_data = bytearray()

    async with BleakClient(device_address) as client:
        try:
            if client.is_connected:
                print(f"Connected to device with MAC address: {client.address}")

                # Enable notifications for the raw characteristic
                await client.start_notify(raw_characteristic_uuid, notification_handler)

                # Enable notifications for the filtered characteristic
                await client.start_notify(filtered_characteristic_uuid, notification_handler)

                # Keep the connection open
                while True:
                    await asyncio.sleep(1)  # Or perform other tasks while listening for notifications
                    process_packets()
        except Exception as e:
            print(f"Error: {e}")

asyncio.run(main())
