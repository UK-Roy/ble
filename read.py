# import asyncio
# from bleak import BleakClient

# # DEVICE_ADDRESS = "46:22:24:DE:0A:5C" # Replace with your BP2 device MAC address
# DEVICE_ADDRESS = "D4:E4:7F:25:20:0D" # Replace with your BP2 device MAC address
# CHARACTERISTIC_UUID = "00002a29-0000-1000-8000-00805f9b34fb"  # UUID of the characteristic that holds the sensor data


# async def read_sensor_data(device_address, characteristic_uuid):
#     async with BleakClient(device_address) as client:
#         print(f"Connected to {device_address}")

#         if client.is_connected:
#             print("Connection successful!")

#             # Read the data from the characteristic
#             sensor_data = await client.read_gatt_char(characteristic_uuid)
#             print(f"Sensor Data: {sensor_data}")
            
#             # Process the sensor data as needed
#             # For example, unpacking the data (assuming it's in a specific binary format)
#             # You can use struct.unpack or decode the data as required by your BP device
#             # Example (if it's binary data):
#             # systolic, diastolic = struct.unpack('<HH', sensor_data)
#             # print(f"Systolic: {systolic}, Diastolic: {diastolic}")
            
#         else:
#             print(f"Failed to connect to {device_address}")

# async def notification_handler(sender, data):
#     print(f"Notification from {sender}: {data}")
#     # Process the received data here (e.g., unpack the data for systolic/diastolic)

# async def subscribe_to_notifications(device_address, characteristic_uuid):
#     async with BleakClient(device_address) as client:
#         print(f"Connected to {device_address}")

#         if client.is_connected:
#             print("Connection successful!")

#             # Subscribe to the characteristic for real-time updates
#             await client.start_notify(characteristic_uuid, notification_handler)
#             print(f"Subscribed to notifications from {characteristic_uuid}")
            
#             # Keep the connection open and listening for updates
#             await asyncio.sleep(60)  # Listen for 60 seconds (or until you stop it)

#         else:
#             print(f"Failed to connect to {device_address}")

# # Run the function to subscribe
# # asyncio.run(subscribe_to_notifications(DEVICE_ADDRESS, CHARACTERISTIC_UUID))


# # Run the function
# asyncio.run(read_sensor_data(DEVICE_ADDRESS, CHARACTERISTIC_UUID))

import asyncio
from bleak import BleakClient

DEVICE_ADDRESS = "D4:E4:7F:25:20:0D"  # Replace with your O2Ring device MAC address
NOTIFY_CHARACTERISTIC_UUID = "0734594a-a8e7-4b1a-a6b1-cd5243059a57"  # Characteristic UUID for notifications

async def notification_handler(sender, data):
    """Callback to handle notifications."""
    print(f"Notification from {sender}: {data}")
    
    # Process the received data (for example, unpack the sensor values)
    # Assuming data is raw sensor data (bytearray) that you need to decode
    if data:
        o2 = int(data[0])  # Example: SpO2 value
        hr = int(data[1])  # Example: Heart rate value
        print(f"Received data - SpO2: {o2}% | Heart Rate: {hr} bpm")
    else:
        print("Received empty data, no update from device.")

async def subscribe_to_notifications(device_address):
    async with BleakClient(device_address) as client:
        if client.is_connected:
            print(f"Connected to {device_address}")
            
            # Subscribe to the characteristic for notifications
            await client.start_notify(NOTIFY_CHARACTERISTIC_UUID, notification_handler)
            print(f"Subscribed to notifications from {NOTIFY_CHARACTERISTIC_UUID}")
            
            # Keep the connection open and wait for notifications
            await asyncio.sleep(60)  # Adjust time as necessary to keep listening for updates

# Run the function to subscribe to notifications
asyncio.run(subscribe_to_notifications(DEVICE_ADDRESS))
