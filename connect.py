# import asyncio
# from bleak import BleakScanner, BleakClient

# # Device name to look for (BP2 5768)
# DEVICE_NAME = "BP2 5768"

# async def connect_to_device(device):
#     try:
#         print("At the try block")
#         # Create a BleakClient instance using the device address (MAC)
#         async with BleakClient(device) as client:
#             print(f"Connected to {device.name} ({device.address})")
            
#             # Check if the device is connected
#             if client.is_connected:
#                 print(f"Successfully connected to {device.name}")
#                 # You can now interact with the device, for example, read/write characteristics

#                 # For testing, just print the services
#                 services = await client.get_services()
#                 for service in services:
#                     print(f"Service: {service.uuid}")
#                     for characteristic in service.characteristics:
#                         print(f"  Characteristic: {characteristic.uuid}")
#                 # Once done, the client will automatically disconnect when leaving the async context
#             else:
#                 print(f"Failed to connect to {device.name}")
#     except Exception as e:
#         print(f"Error connecting to {device.name}: {e}")

# async def scan_for_devices():
#     print("Scanning for BP devices...")

#     # Create a BleakScanner instance to scan for nearby devices
#     scanner = BleakScanner()
    
#     print(f"Start Scanning")
#     def on_detection(device, advertisement_data):
#         if device.name == DEVICE_NAME:  # Match BP2 5768 by name
#             print(f"Found BP2 device: {device.name} ({device.address})")
#             # Automatically connect to the found BP2 device
#             asyncio.create_task(connect_to_device(device))

#     # Register the detection callback function
#     scanner.register_detection_callback(on_detection)

#     # Start scanning for nearby devices
#     await scanner.start()

#     # Allow scanning for 10 seconds (adjust as needed)
#     await asyncio.sleep(10)

#     # Stop scanning after the timeout
#     await scanner.stop()
#     print("Scanning complete.")

# # Run the scanning function
# asyncio.run(scan_for_devices())


import asyncio
from bleak import BleakClient

DEVICE_ADDRESS = "46:22:24:DE:0A:5C" # Replace with your BP2 device MAC address
# DEVICE_ADDRESS = "D4:E4:7F:25:20:0D" # Replace with your BP2 device MAC address

async def connect_to_device(device_address):
    async with BleakClient(device_address) as client:
        print(f"Connected to {device_address}")

        # Check if connected
        if client.is_connected:
            print("Connection successful!")
            # Start reading data from the device (for example, reading services)
            services = await client.get_services()
            for service in services:
                print(f"Service UUID: {service.uuid}")
                for characteristic in service.characteristics:
                    print(f"  Characteristic UUID: {characteristic.uuid} Properties: {characteristic.properties}")
            
            # You can read/write characteristics here
            # Example: await client.read_gatt_char(<characteristic_uuid>)

        else:
            print(f"Failed to connect to {device_address}")

# Run the connection function
asyncio.run(connect_to_device(DEVICE_ADDRESS))
