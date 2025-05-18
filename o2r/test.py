import asyncio
from o2ring import main

if __name__ == "__main__":
    spo2, rt_file = asyncio.run(main())
    print("→ Sensor reading:", spo2)
    print("→ PPG log saved to:", rt_file)