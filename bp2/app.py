import asyncio
import csv
import json
from datetime import datetime
from bleak import BleakScanner, BleakClient

# BLE UUIDs
SERVICE_UUID     = "14839ac4-7d7e-415c-9a42-167340cf2339"
WRITE_CHAR_UUID  = "8B00ACE7-EB0B-49B0-BBE9-9AEE0A26E1A3"
NOTIFY_CHAR_UUID = "0734594A-A8E7-4B1A-A6B1-CD5243059A57"

# Opcodes
RT_PARAM     = 0x06
RT_DATA      = 0x08

# Sequence Number Management
_seq_no = 0
def next_seq() -> int:
    global _seq_no
    val = _seq_no
    _seq_no = (_seq_no + 1) & 0xFF
    return val

CRC8_TABLE = [
    0x00,0x07,0x0E,0x09,0x1C,0x1B,0x12,0x15,0x38,0x3F,0x36,0x31,0x24,0x23,0x2A,0x2D,
    0x70,0x77,0x7E,0x79,0x6C,0x6B,0x62,0x65,0x48,0x4F,0x46,0x41,0x54,0x53,0x5A,0x5D,
    0xE0,0xE7,0xEE,0xE9,0xFC,0xFB,0xF2,0xF5,0xD8,0xDF,0xD6,0xD1,0xC4,0xC3,0xCA,0xCD,
    0x90,0x97,0x9E,0x99,0x8C,0x8B,0x82,0x85,0xA8,0xAF,0xA6,0xA1,0xB4,0xB3,0xBA,0xBD,
    0xC7,0xC0,0xC9,0xCE,0xDB,0xDC,0xD5,0xD2,0xFF,0xF8,0xF1,0xF6,0xE3,0xE4,0xED,0xEA,
    0xB7,0xB0,0xB9,0xBE,0xAB,0xAC,0xA5,0xA2,0x8F,0x88,0x81,0x86,0x93,0x94,0x9D,0x9A,
    0x27,0x20,0x29,0x2E,0x3B,0x3C,0x35,0x32,0x1F,0x18,0x11,0x16,0x03,0x04,0x0D,0x0A,
    0x57,0x50,0x59,0x5E,0x4B,0x4C,0x45,0x42,0x6F,0x68,0x61,0x66,0x73,0x74,0x7D,0x7A,
    0x89,0x8E,0x87,0x80,0x95,0x92,0x9B,0x9C,0xB1,0xB6,0xBF,0xB8,0xAD,0xAA,0xA3,0xA4,
    0xF9,0xFE,0xF7,0xF0,0xE5,0xE2,0xEB,0xEC,0xC1,0xC6,0xCF,0xC8,0xDD,0xDA,0xD3,0xD4,
    0x69,0x6E,0x67,0x60,0x75,0x72,0x7B,0x7C,0x51,0x56,0x5F,0x58,0x4D,0x4A,0x43,0x44,
    0x19,0x1E,0x17,0x10,0x05,0x02,0x0B,0x0C,0x21,0x26,0x2F,0x28,0x3D,0x3A,0x33,0x34,
    0x4E,0x49,0x40,0x47,0x52,0x55,0x5C,0x5B,0x76,0x71,0x78,0x7F,0x6A,0x6D,0x64,0x63,
    0x3E,0x39,0x30,0x37,0x22,0x25,0x2C,0x2B,0x06,0x01,0x08,0x0F,0x1A,0x1D,0x14,0x13,
    0xAE,0xA9,0xA0,0xA7,0xB2,0xB5,0xBC,0xBB,0x96,0x91,0x98,0x9F,0x8A,0x8D,0x84,0x83,
    0xDE,0xD9,0xD0,0xD7,0xC2,0xC5,0xCC,0xCB,0xE6,0xE1,0xE8,0xEF,0xFA,0xFD,0xF4,0xF3,
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

# parse little-endian helpers
def u16(b: bytes) -> int: return int.from_bytes(b, 'little')
def i16(b: bytes) -> int: return int.from_bytes(b, 'little', signed=True)

# parse the RT_DATA payload: handles BP‐result, ECG‐measuring, ECG‐result
def parse_rtdata(payload: bytes) -> dict:
    row = {'sys': '', 'dia': '', 'pr': '', 'ecg_hr': '', 
           'ecg_duration_ms': '', 'wave_samples': ''}
    # payload[0]..payload[8] = RtParam, then payload[9:] is wave block
    blk = payload[9:]
    dtype = blk[0]
    data = blk[1:21]
    idx = 21
    # waveLen present?
    wave_samples = []
    if len(blk) >= idx+2:
        wave_len = u16(blk[idx:idx+2])
        idx += 2
        for i in range(wave_len):
            off = idx + 2*i
            wave_samples.append(i16(blk[off:off+2]))
        row['wave_samples'] = json.dumps(wave_samples)
    if dtype == 0x01:
        # BP result
        row['sys'] = u16(data[2:4])
        row['dia'] = u16(data[4:6])
        row['pr']  = u16(data[8:10])
    elif dtype == 0x02:
        # ECG measuring
        row['ecg_duration_ms'] = u16(data[0:2]) | (u16(data[2:4])<<16)  # adjust if 4-byte
        row['ecg_hr'] = u16(data[8:10])
    elif dtype == 0x03:
        # ECG result
        row['ecg_hr'] = u16(data[4:6])
    return row

# frame buffer
_buffer = bytearray()

# prepare CSV
csv_file = "bp2.csv"
with open(csv_file, 'w', newline='') as f:
    writer = csv.writer(f)
    # writer.writerow([
    #     'timestamp','sys','dia','pr',
    #     'ecg_duration_ms','ecg_hr','wave_samples'
    # ])
    writer.writerow([
        'timestamp','sys','dia','pr'
        # 'ecg_duration_ms','ecg_hr','wave_samples'
    ])

async def handle_notify(_, data: bytes):
    global _buffer
    _buffer += data
    i = 0
    while i + 8 <= len(_buffer):
        if _buffer[i] != 0xA5 or (_buffer[i+1] ^ _buffer[i+2]) != 0xFF:
            i += 1; continue
        length = _buffer[i+5] | (_buffer[i+6] << 8)
        end = i + 8 + length
        if end > len(_buffer): break
        frame = bytes(_buffer[i:end])
        if frame[-1] == cal_crc8(frame[:-1]):
            if frame[1] == RT_DATA:
                row = parse_rtdata(frame[8:-1])
                ts = datetime.now().isoformat()
                # print(ts, row)
                with open(csv_file, 'a', newline='') as f:
                    csv.writer(f).writerow([
                        ts,
                        row['sys'], row['dia'], row['pr'],
                        # row['ecg_duration_ms'], row['ecg_hr'],
                        # row['wave_samples']
                    ])
            i = end
        else:
            i += 1
    _buffer = _buffer[i:]

async def rt_loop(client):
    try:
        while True:
            await client.write_gatt_char(WRITE_CHAR_UUID, cmd_get_rt_data())
            await asyncio.sleep(2)
    except asyncio.CancelledError:
        pass

async def run(address: str):
    async with BleakClient(address) as client:
        await client.start_notify(NOTIFY_CHAR_UUID, handle_notify)
        await client.write_gatt_char(WRITE_CHAR_UUID, cmd_get_rt_param())
        await asyncio.sleep(1)
        task = asyncio.create_task(rt_loop(client))
        await asyncio.sleep(60)   # e.g. run for 1 minute
        task.cancel(); await task
        await client.stop_notify(NOTIFY_CHAR_UUID)

async def main():
    # devices = await BleakScanner.discover(timeout=10)
    # for d in devices:
        # if d.name and "BP2" in d.name:
            # print("Connecting to", d.address)
            # await run(d.address)
            # break
    # scan for up to 20 seconds
    print("Scanning for BP2 devices (20 s timeout)…")
    devices = await BleakScanner.discover(timeout=20.0)
    # pick the first that matches
    target = next((d for d in devices if d.name and "BP2" in d.name), None)
    if target is None:
        raise RuntimeError("Scan timed out: no BP2 found within 20 seconds")
    print("Connecting to", target.address)
    await run(target.address)

    
if __name__ == "__main__":
    asyncio.run(main())
