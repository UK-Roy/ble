import asyncio
from bleak import BleakScanner

async def scan_bp_devices():
    print("Scanning for BP devices...")

    # Create a scanner object
    scanner = BleakScanner()

    # Register a callback to handle detected devices
    def on_detection(device, advertisement_data):
        # Print the device name and address
        print(f"Found device: {device.name} ({device.address})")

        # You can also check if the device is a BP machine here based on name or UUID
        # For now, we are just listing all nearby devices

    # Register the detection callback
    scanner.register_detection_callback(on_detection)

    # Start scanning for nearby devices
    await scanner.start()

    # Allow scanning for a limited amount of time (optional)
    await asyncio.sleep(10)  # Scan for 10 seconds (adjust as needed)

    # Stop scanning
    await scanner.stop()
    print("Scanning complete.")

# Run the scanning function
asyncio.run(scan_bp_devices())
