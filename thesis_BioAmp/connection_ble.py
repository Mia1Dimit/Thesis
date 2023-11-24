import asyncio
from bleak import BleakClient
import struct
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


device_address = 'F4:12:FA:63:47:29'
raw_characteristic_uuid = "b817f6da-8796-11ee-b9d1-0242ac120002"
filtered_characteristic_uuid = "a3b1a544-8794-11ee-b9d1-0242ac120002"
# Define a dictionary mapping handles or UUIDs to names
characteristic_names = {
    "b817f6da-8796-11ee-b9d1-0242ac120002": "EMG_Raw_Characteristic",
    "a3b1a544-8794-11ee-b9d1-0242ac120002": "EMG_Filtered_Characteristic"
}

# Extract UUIDs from characteristic_names
characteristic_uuids = list(characteristic_names.keys())

# Define lists to store received packets
raw_packets = []
filtered_packets = []

PACKET_SIZE = 52
NUM_PACKETS = 30
FLOATS_PER_PACKET = 52


def process_packets(raw_data, filtered_data):
    for i in range(NUM_PACKETS):
        raw_packet = raw_data[i]
        filtered_packet = filtered_data[i]

        raw_values = struct.unpack('<' + 'f' * FLOATS_PER_PACKET, raw_packet)
        filtered_values = struct.unpack('<' + 'f' * FLOATS_PER_PACKET, filtered_packet)


async def notification_handler(sender, data):
    handle = sender.uuid if sender.uuid in characteristic_uuids else sender

    # Check if the handle or UUID is in the dictionary
    characteristic_name = characteristic_names.get(str(handle), "Unknown")

    # Unpack bytearray into a float
    float_value = struct.unpack('<' + 'f' * (len(data) // 4), data)
    # Format float value to have two decimal places using f-string
    print(f"Received notification from {characteristic_name} (Handle: {handle}): Value: {float_value}")

    if characteristic_name == "EMG_Raw_Characteristic":
        raw_packets.append(data)
    elif characteristic_name == "EMG_Filtered_Characteristic":
        filtered_packets.append(data)

    if len(raw_packets) == NUM_PACKETS and len(filtered_packets) == NUM_PACKETS:
        process_packets(raw_packets, filtered_packets)

async def main():
    async with BleakClient(device_address) as client:
        try:
            if BleakClient.is_connected:
                print(f"Connected to device with MAC address: {device_address}")

                # Enable notifications for the raw characteristic
                await client.start_notify(raw_characteristic_uuid, notification_handler)
                
                # Enable notifications for the filtered characteristic
                await client.start_notify(filtered_characteristic_uuid, notification_handler)

                # Keep the connection open
                while True:
                    await asyncio.sleep(1)  # Or perform other tasks while listening for notifications

        except Exception as e:
            print(f"Error: {e}")


# Run the coroutine to connect and listen for notifications
asyncio.run(main())
