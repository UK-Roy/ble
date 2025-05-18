import asyncio
from function import capture_bp2

# async def go():
    # bp, path = await capture_bp2()
    # print("BP:", bp)
    # print("Saved:", path)

# if __name__ == "__main__":
    # asyncio.run(go())
if __name__ == "__main__":
    # scan 20 s, stream 60 s, write to bp2.csv
    bp, path = asyncio.run(capture_bp2(
        duration=60,
        scan_timeout=20,
        csv_filename="bp2.csv"
    ))
    print("BP reading:", bp)
    print("Logged CSV:", path)

