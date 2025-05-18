# import struct

# filename = "O2Ring 9266_2025-04-21,11:54:52.rt"
# with open(filename, "r") as f:
#     text = f.read().splitlines()

# for line in text:
    
#     line = line.zfill(301)[27:] #Ensure the correct # of bytes for the struct
   
#     spo2, hr, battery, activity, _, ppg_bytes = struct.unpack("<2BxBx2B5x125s", bytes.fromhex(line))
#     print(f"spo2: {spo2}, hr: {hr} ppg: {ppg_bytes} battery: {battery}")
#     # ppg = [x for x in ppg_bytes]

import struct
import matplotlib.pyplot as plt

def parse_rt_packet(pkt_data: bytes):
    """
    pkt_data: the pkt.recv_data from CMD_RT_DATA notification
    returns: (spo2, hr, battery, activity, samples_list)
    """
    # 1) Unpack the first 12 bytes:
    #    '<4B8x' means: 4 unsigned bytes, then skip 8 bytes
    spo2, hr, battery, activity = struct.unpack_from('<4B8x', pkt_data, 0)

    # 2) The rest are PPG samples, one byte each:
    samples = list(pkt_data[12:])

    return spo2, hr, battery, activity, samples

def parse_line(line):
    ts, hexstr = line.strip().split('|')
    pkt = bytes.fromhex(hexstr)
    return ts, *parse_rt_packet(pkt)

with open("ppg_data.rt") as f:
    n_line = 0
    for line in f:
        ts, spo2, hr, batt, act, samples = parse_line(line)
        # Now you have everything in Python objects:
        print(ts, spo2, hr, batt, act, samples)
        signed = [(s - 128) for s in samples]
        n_line += 1
    print(n_line)
    plt.plot(signed)
    plt.title("PPG Waveform")
    plt.show()
