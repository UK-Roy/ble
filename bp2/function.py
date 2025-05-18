import asyncio
import csv
import time
import json
from datetime import datetime
from bleak import BleakScanner, BleakClient

# ── BLE UUIDs ────────────────────────────────────────────────────────────────
SERVICE_UUID     = "14839ac4-7d7e-415c-9a42-167340cf2339"
WRITE_CHAR_UUID  = "8B00ACE7-EB0B-49B0-BBE9-9AEE0A26E1A3"
NOTIFY_CHAR_UUID = "0734594A-A8E7-4B1A-A6B1-CD5243059A57"

# ── Opcodes ─────────────────────────────────────────────────────────────────
RT_PARAM = 0x06
RT_DATA  = 0x08

# ── Sequence Number ─────────────────────────────────────────────────────────
_seq_no = 0
def next_seq() -> int:
    global _seq_no
    val = _seq_no
    _seq_no = (_seq_no + 1) & 0xFF
    return val

# ── CRC8 Table & Helpers ────────────────────────────────────────────────────
CRC8_TABLE = [
    # ... (same 256-entry table as before) ...
]

def cal_crc8(buf: bytes) -> int:
    crc = 0
    for b in buf:
        crc = CRC8_TABLE[(crc ^ b) & 0xFF]
    return crc

def build_cmd(opcode: int, payload: bytes = b"") -> bytes:
    length = len(payload)
    hdr = bytes([
        0xA5,
        opcode,
        (~opcode) & 0xFF,
        0x00,
        next_seq(),
        length & 0xFF,
        (length >> 8) & 0xFF,
    ])
    pkt = hdr + payload
    return pkt + bytes([cal_crc8(pkt)])

cmd_get_rt_param = lambda: build_cmd(RT_PARAM)
cmd_get_rt_data  = lambda: build_cmd(RT_DATA)

# ── Parse Helpers ────────────────────────────────────────────────────────────
def u16(b: bytes) -> int: return int.from_bytes(b, 'little')
def i16(b: bytes) -> int: return int.from_bytes(b, 'little', signed=True)

def parse_rtdata(payload: bytes) -> dict:
    row = {
        'sys':           '',
        'dia':           '',
        'pr':            '',
        'ecg_duration_ms':'',
        'ecg_hr':        '',
        'wave_samples':  ''
    }
    blk = payload[9:]
    if not blk:
        return row
    dtype = blk[0]
    data  = blk[1:21]
    idx   = 21

    # wave samples
    if len(blk) >= idx+2:
        wave_len = u16(blk[idx:idx+2])
        idx += 2
        samples = []
        for i in range(wave_len):
            off = idx + 2*i
            samples.append(i16(blk[off:off+2]))
        row['wave_samples'] = json.dumps(samples)

    if dtype == 0x01:  # BP result
        row['sys'] = u16(data[2:4])
        row['dia'] = u16(data[4:6])
        row['pr']  = u16(data[8:10])
    elif dtype == 0x02:  # ECG measuring
        row['ecg_duration_ms'] = u16(data[0:2]) | (u16(data[2:4]) << 16)
        row['ecg_hr'] = u16(data[8:10])
    elif dtype == 0x03:  # ECG result
        row['ecg_hr'] = u16(data[4:6])

    return row

# ── Capture Function ─────────────────────────────────────────────────────────
async def capture_bp2(duration: float = 60.0,
                      scan_timeout: float = 20.0,
                      csv_filename: str = "bp2.csv"):
    """
    Scans for a BP2 device (timeout=scan_timeout), connects, streams RT_PARAM/RT_DATA
    for `duration` seconds, logs everything to `csv_filename`, and returns:
      (first_bp_reading_dict, csv_filename)
    """
    # prepare CSV
    with open(csv_filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'timestamp','sys','dia','pr',
            'ecg_duration_ms','ecg_hr','wave_samples'
        ])

    sensor_data = None
    buffer = bytearray()

    async def handle_notify(_, data: bytes):
        nonlocal sensor_data, buffer
        buffer += data
        i = 0
        while i + 8 <= len(buffer):
            if buffer[i] != 0xA5 or (buffer[i+1] ^ buffer[i+2]) != 0xFF:
                i += 1
                continue
            length = buffer[i+5] | (buffer[i+6] << 8)
            end = i + 8 + length
            if end > len(buffer):
                break
            frame = bytes(buffer[i:end])
            i = end
            if frame[-1] != cal_crc8(frame[:-1]):
                continue
            if frame[1] == RT_DATA:
                row = parse_rtdata(frame[8:-1])
                ts = datetime.now().isoformat()
                # first BP
                if row['sys'] and sensor_data is None:
                    sensor_data = {
                        'timestamp': ts,
                        'sys':        row['sys'],
                        'dia':        row['dia'],
                        'pr':         row['pr'],
                    }
                # append CSV
                with open(csv_filename, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        ts,
                        row['sys'], row['dia'], row['pr'],
                        row['ecg_duration_ms'], row['ecg_hr'],
                        row['wave_samples']
                    ])
        buffer = buffer[i:]

    async def rt_loop(client):
        try:
            while True:
                await client.write_gatt_char(WRITE_CHAR_UUID, cmd_get_rt_data())
                await asyncio.sleep(2)
        except asyncio.CancelledError:
            pass

    # scan
    devices = await BleakScanner.discover(timeout=scan_timeout)
    target = next((d for d in devices if d.name and "BP2" in d.name), None)
    if target is None:
        raise TimeoutError(f"No BP2 discovered in {scan_timeout} seconds")

    # connect & stream
    async with BleakClient(target.address) as client:
        await client.start_notify(NOTIFY_CHAR_UUID, handle_notify)
        await client.write_gatt_char(WRITE_CHAR_UUID, cmd_get_rt_param())
        await asyncio.sleep(1)
        task = asyncio.create_task(rt_loop(client))
        await asyncio.sleep(duration)
        task.cancel()
        await task
        await client.stop_notify(NOTIFY_CHAR_UUID)

    return sensor_data, csv_filename

# ── Example usage ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    async def _main():
        bp, path = await capture_bp2(duration=60, scan_timeout=20, csv_filename="bp2.csv")
        print("BP reading:", bp)
        print("Logged CSV:", path)
    asyncio.run(_main())

