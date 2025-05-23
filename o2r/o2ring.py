# import o2r
# import threading, time, queue, traceback
# import argparse
# import json

# import asyncio

# def str2bool(v):
#     if isinstance(v, bool):
#        return v
#     if v.lower() in ('yes', 'true', 't', 'y', '1', 'on'):
#         return True
#     elif v.lower() in ('no', 'false', 'f', 'n', '0', 'off'):
#         return False
#     else:
#         raise argparse.ArgumentTypeError('Boolean value expected.')

# def str2bright(v):
#     if v.lower() in ('l', '0'):
#         return 0
#     elif v.lower() in ('m', '1'):
#         return 1
#     elif v.lower() in ('h', '2'):
#         return 2
#     else:
#         raise argparse.ArgumentTypeError('L/M/H or l/m/h or 0-2 expected.')

# async def main():
#     arg_parser = argparse.ArgumentParser(description="O2Ring BLE Downloader", epilog='Setting either --hr-alert-high or --hr-alert-low to 0 and leaving the other unset disables Heart Rate vibration alerts.  If one is 0 and the other is >0 then the 0 is ignored.')
#     #arg_parser.add_argument('mac_address', help="MAC address of device to connect")
#     arg_parser.add_argument( '-v', '--verbose', help='increase output verbosity (repeat to increase)', action="count", default=0 )
#     arg_parser.add_argument( '-s', '--scan', help='Scan Time (Seconds, 0 = forever, default = 30)', type=int, metavar='[scan time]', default=30 )
#     arg_parser.add_argument( '--keep-going', help='Do not disconnect when finger is not present', action="store_true" )
#     arg_parser.add_argument( '-m', '--multi', help='Keep scanning for multiple devices', action="store_true" )
#     arg_parser.add_argument( '-p', '--prefix', help='Downloaded file prefix (default: "[BT Name] - ")', metavar='PREFIX' )
#     arg_parser.add_argument( '-e', '--ext', help='Downloaded file extension (default: vld)', default='vld', metavar='EXT' )
#     arg_parser.add_argument( '--csv', help='Convert downloaded file to CSV', action="store_true" )
#     arg_parser.add_argument( '--realtime', help='Enable Realtime PPG data capture', action="store_true" )
#     # the O2Ring changes the o2 alert value to 90 if >95 is provided
#     #arg_parser.add_argument( '--o2-alert', help='Enable/Disable O2 vibration alerts', type=str2bool, metavar='[bool]' )
#     arg_parser.add_argument( '--o2-alert', help='O2 vibration alert at this %% (0-95, 0 = disabled)', type=int, metavar='[0-95]', choices=range(0,101) )

#     #arg_parser.add_argument( '--hr-alert', help='Enable/Disable Heart Rate vibration alerts', type=str2bool, metavar='[bool]' )
#     arg_parser.add_argument( '--hr-alert-high', help='Heart Rate High vibration alert (0-200, 0 = disabled)', type=int, metavar='[0-200]', choices=range(0,201) )
#     arg_parser.add_argument( '--hr-alert-low', help='Heart Rate Low vibration alert (0-200, 0 = disabled)', type=int, metavar='[0-200]', choices=range(0,201) )
#     arg_parser.add_argument( '--vibrate', help='Vibration Strength (1-100)', type=int, metavar='[1-100]', choices=range(1,101) )
#     #arg_parser.add_argument( '--pedtar', help='Pedtar Setting (0-99999)', type=int, metavar='[0-99999]', choices=range(0,100000) )
#     arg_parser.add_argument( '--screen', help='Enable/Disable "Screen Always On"', type=str2bool, metavar='[bool]' )
#     arg_parser.add_argument( '--brightness', help='Screen Brightness (Low/Med/High)', type=str2bright, metavar='[L/M/H or 0-2]', choices=range(0,3) )

#     args = arg_parser.parse_args()
#     print("Arguments: ", json.dumps(vars(args), indent=4))

#     if( args.scan and args.scan > 0 ):
#         stop_scanning_at = time.time() + args.scan
#     else:
#         stop_scanning_at = 0

#     print("Connecting...")

#     manager = o2r.O2DeviceManager()
#     manager.verbose = args.verbose + 1
#     manager.queue = asyncio.Queue()

#     await manager.start_discovery()
#     scanning = True
#     multi = args.multi
#     rings = {}
#     want_exit = False
#     run = True

#     try:
#         while run:
#             try:
#                 cmd = await asyncio.wait_for(manager.queue.get(), 1.0)
#             except asyncio.TimeoutError:
#                 cmd = None
#             #except KeyboardInterrupt:
#             except asyncio.CancelledError:
#                 if( want_exit ):
#                     traceback.print_exc()
#                     run = False
#                     break
#                 print('Shutting Down')
#                 want_exit = True
#                 if( scanning ):
#                     await manager.stop_discovery()
#                     scanning = False
#                 for r in rings:
#                     rings[r].close()

#                 del rings
#                 rings = {}

#                 break
#             except:
#                 traceback.print_exc()
#                 run = False
#                 if( scanning ):
#                     await manager.stop_discovery()
#                     scanning = False
#                 break

#             if( cmd is None ):
#                 pass
#             else:
#                 (ident, command, data) = cmd

#                 if( command == 'READY' ):
#                     if( 'verbose' not in data ):
#                         data['verbose'] = args.verbose + 1
#                     if( ident in rings ):
#                         rings[ident].close()
#                     rings[ident] = o2r.o2state( data['name'], data, args )
#                     if( not multi and scanning ):
#                         await manager.stop_discovery()
#                         scanning = False
#                 elif( command == 'DISCONNECT' ):
#                     rings[ident].close()
#                     del rings[ident]
#                     if( (not scanning) and len(rings) < 1 ):
#                         want_exit = True
#                 elif( command == 'BTDATA' ):
#                     rings[ident].recv( data )
#                 else:
#                     print('unhandled command:', cmd)

#             for r in rings:
#                 #if( not rings[r].dev.awaiting_response ):
#                 rings[r].check()

#             if( want_exit and len(rings) == 0 ):
#                 run = False
#                 #break

#             if( (stop_scanning_at > 0) and (stop_scanning_at <= time.time()) ):
#                 stop_scanning_at = 0
#                 if( scanning ):
#                     scanning = False
#                     await manager.stop_discovery()
#                 if( len(rings) < 1 ):
#                     print('No devices found!')
#                     want_exit = True
#                     run = False
#     except:
#         traceback.print_exc()

#     if( scanning ):
#         await manager.stop_discovery()

#     #print(manager.devices.values())
#     print('disconnecting all')
#     to_disconnect = []
#     for dev in manager.devices.values():
#         if( dev.is_connected ):
#             print('disconnecting:', dev.mac_address)
#             to_disconnect.append(dev.disconnect_async())
#     asyncio.gather(*to_disconnect)

#     await asyncio.sleep(0.5)

# if __name__ == "__main__":
#     # https://stackoverflow.com/questions/30765606/whats-the-correct-way-to-clean-up-after-an-interrupted-event-loop
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)
#     task = asyncio.Task(main())
#     try:
#         loop.run_until_complete(task)
#     except KeyboardInterrupt:
#         task.cancel()
#         loop.run_until_complete(task)
#         task.exception()

import o2r
import threading, time, queue, traceback
import argparse
import json


import asyncio

def str2bool(v):
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'true', 't', 'y', '1', 'on'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0', 'off'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

def str2bright(v):
    if v.lower() in ('l', '0'):
        return 0
    elif v.lower() in ('m', '1'):
        return 1
    elif v.lower() in ('h', '2'):
        return 2
    else:
        raise argparse.ArgumentTypeError('L/M/H or l/m/h or 0-2 expected.')

async def main():
    arg_parser = argparse.ArgumentParser(description="O2Ring BLE Downloader")
    arg_parser.add_argument( '-v', '--verbose', action="count", default=0 )
    arg_parser.add_argument( '-s', '--scan', type=int, default=20)
    arg_parser.add_argument( '-r', '--read', type=int, default=75)
    arg_parser.add_argument( '--keep-going', action="store_true" )
    arg_parser.add_argument( '-m', '--multi', action="store_true" )
    arg_parser.add_argument( '-p', '--prefix', metavar='PREFIX' )
    arg_parser.add_argument( '-e', '--ext', default='vld', metavar='EXT' )
    arg_parser.add_argument( '--csv', action="store_true", default=False)
    arg_parser.add_argument( '--realtime', action="store_true", default=True)
    arg_parser.add_argument( '--o2-alert', type=int, choices=range(0,101) )
    arg_parser.add_argument( '--hr-alert-high', type=int, choices=range(0,201) )
    arg_parser.add_argument( '--hr-alert-low',  type=int, choices=range(0,201) )
    arg_parser.add_argument( '--vibrate',     type=int, choices=range(1,101) )
    arg_parser.add_argument( '--screen',      type=str2bool )
    arg_parser.add_argument( '--brightness',  type=str2bright, choices=range(0,3) )

    args = arg_parser.parse_args()
    print("Arguments:", json.dumps(vars(args), indent=4))

    stop_scanning_at = time.time() + args.scan if args.scan>0 else 0
    stop_reading_at = time.time() + args.read if args.read>0 else 0

    print("Connecting...")

    manager = o2r.O2DeviceManager()
    manager.verbose = args.verbose + 1
    manager.queue = asyncio.Queue()

    await manager.start_discovery()
    scanning = True
    rings = {}
    want_exit = False
    run = True

    # Sensors Variable
    sensor = None
    ppg_file = None

    try:
        while run:
            try:
                cmd = await asyncio.wait_for(manager.queue.get(), 1.0)
            except asyncio.TimeoutError:
                cmd = None
            except asyncio.CancelledError:
                # handle shutdown…
                want_exit = True
                break
            except:
                traceback.print_exc()
                break

            if cmd:
                ident, command, data = cmd

                if command == 'READY':
                    data.setdefault('verbose', args.verbose+1)
                    if ident in rings:
                        rings[ident].close()
                    rings[ident] = o2r.o2state(data['name'], data, args)
                    if not args.multi and scanning:
                        await manager.stop_discovery()
                        scanning = False

                elif command == 'DISCONNECT':
                    rings[ident].close()
                    del rings[ident]
                    if not scanning and not rings:
                        want_exit = True

                elif command == 'BTDATA':
                    # **HERE** we capture and print returned dict
                    result = rings[ident].recv(data)
                    if result:
                        # sensor reading
                        if 'spo2' in result:
                            sensor  = {
                                    'device'        : rings[ident].name,
                                    'spo2'          : result['spo2'],
                                    'hr'            : result['hr'],
                                    'battery'       : result['battery'],
                                    'motion'        : result['motion'],
                                    'finger_present': 'Yes' if result['finger_present'] else 'No'
                                }
                            # print(f"[{rings[ident].name}] Sensor → SpO2={result['spo2']}%, "
                            #       f"HR={result['hr']} bpm, Batt={result['battery']}%, "
                            #       f"Motion={result['motion']}, Finger={'Yes' if result['finger_present'] else 'No'}")
                        # realtime PPG
                        if 'ppg_bytes' in result:
                            ts = result['timestamp']
                            ppg = result['ppg_bytes'].hex()

                            ppg_file = f"ppg_data.rt"
                            # print(f"Before putting the file: {pkt.recv_data}")
                            with open(ppg_file, "a") as f:
                                f.write(ts)
                                f.write("|")
                                f.write(ppg)
                                f.write("\n")
                            # print(f"[{rings[ident].name}] PPG @ {ts}: {ppg}")

                else:
                    print('unhandled command:', cmd)

            # run each state machine’s periodic check
            for st in rings.values():
                st.check()

            if want_exit or time.time()>=stop_reading_at or (stop_scanning_at and time.time()>=stop_scanning_at and not rings):
                run = False
            
    
    finally:
        if scanning:
            await manager.stop_discovery()

        print('Disconnecting all...')
        tasks = [dev.disconnect_async()
                 for dev in manager.devices.values()
                 if dev.is_connected]
        await asyncio.gather(*tasks, return_exceptions=True)
        # asyncio.gather(*tasks)
        # await asyncio.sleep(0.5)
    return sensor, ppg_file

# if __name__ == "__main__":
#     spo2, rt_file = asyncio.run(main())
#     print("→ Sensor reading:", spo2)
#     print("→ PPG log saved to:", rt_file)
