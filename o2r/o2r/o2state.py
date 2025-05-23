# import time, json, pprint, struct, os.path, datetime

# from .defines import *
# from .o2pkt import o2pkt
# from .o2cmd import o2cmd
# from .o2file import *

# class o2state:
#     def __init__( self, name, data, args ):
#         self.name = name
#         #self.dev = data['self']
#         self.verbose = data['verbose']
#         self.send_func = data['send']
#         self.busy_func = data['busy']
#         self.disconnect_func = data['disconnect']
#         self.realtime = args.realtime
#         self.args = args
#         self.next_read = 0
#         self.need_cfg = False
#         self.sent_cfg = False
#         self.quiet_cfg = False
#         self.want_files = []
#         self.read_file_out = None
#         self.read_file_in = None
#         self.read_block = None
#         self.read_fp = None
#         self.read_size = 0
#         self.read_want = 0
#         self.no_finger_count = 0
#         self.disconnect_at = 1
#         print('Starting up for', self.name)

#         self.send_func( o2pkt(CMD_INFO) )
#         self.req_time_str = time.strftime( TIME_FORMAT )
#         #self.send_func( o2pkt(CMD_PING) )
#         #self.send_func( o2pkt(CMD_READ_SENSORS) )

#     def recv( self, pkt ):
#         if( self.verbose > 2 ):
#             print( '[%s]' % self.name, pkt.recv_data.hex() )

#         if( pkt.recv_cmd != 0 ):
#             print( '[%s] Command %d Failed!' % (self.name, pkt.cmd), pkt.recv_buf.hex() )

#         if( pkt.cmd == CMD_READ_SENSORS ):
#             self.next_read = time.time() + 1.0

#             # ffffff00000000600005000000
#             # ffffff00000000620100000000
#             # 624200000000006100920a0100
#             # oohh..........bbccmmaaff..

#             #(o2, hr, u1, u2) = struct.unpack( '<BBBB', pkt.recv_data )

#             o2 = int(pkt.recv_data[0])
#             hr = int(pkt.recv_data[1])
#             # [2]
#             # [3]
#             # [4]
#             # [5]
#             # [6]
#             batt = int(pkt.recv_data[7])
#             charging = int( pkt.recv_data[8] )
#             motion = int(pkt.recv_data[9])
#             hr_strength = int(pkt.recv_data[10]) # heart rate signal strength
#             finger_present = bool( pkt.recv_data[11] )
#             # [12]

#             #batts = str(batt) + '%' + ('++' if charging else '')

#             if( charging > 0 ):
#                 if( charging == 1 ):
#                     batts = str(batt) + '%++'
#                 elif( charging == 2 ):
#                     batts = 'CHGD'
#                 else:
#                     batts = ('% 3d' % batt) + '%-' + str(charging)

#             else:
#                 batts = ('% 3d' % batt) + '%'

#             print( '[%s] SpO2 %3d%%, HR %3d bpm, Perfusion Idx %3d, motion %3d, batt %s' % (self.name, o2, hr, hr_strength, motion, batts) )

#             if( (o2 > 100) or (o2 < 10) or (not finger_present) ):
#                 self.no_finger_count += 1
#                 if( (self.no_finger_count > self.disconnect_at) and (not self.args.keep_going) ):
#                     self.disconnect_func()
#                 else:
#                     self.quiet_cfg = True
#                     self.send_func( o2pkt(CMD_INFO) )
#                     self.req_time_str = time.strftime( TIME_FORMAT )
#             else:
#                 self.no_finger_count = 0
#                 self.disconnect_at = 11
                
#         elif( pkt.cmd == CMD_RT_DATA ):
#             ### Read in Realtime Data and save to .rt file
#             timestamp = datetime.datetime.utcnow().isoformat()
#             print(f"Realtime waveforms received at {timestamp}...")
#             realtime_filename = f"{self.name}_{self.req_time_str}.rt"
#             # print(f"Before putting the file: {pkt.recv_data}")
#             with open(realtime_filename, "a") as f:
#                 f.write(timestamp)
#                 f.write("|")
#                 f.write(pkt.recv_data.hex())
#                 f.write("\n")
#         elif( pkt.cmd == CMD_INFO ):
#             self.current_cfg = json.loads( pkt.recv_data.decode('ascii').rstrip( ' \t\r\n\0' ) )

#             if( not self.quiet_cfg ):
#                 pp = pprint.PrettyPrinter(indent=6)
#                 print( '[%s] Config:' % self.name )
#                 pp.pprint( self.current_cfg )

#             o2_time = datetime.datetime(*time.strptime( self.current_cfg['CurTIME'], TIME_FORMAT )[:6])
#             sent_time = datetime.datetime(*time.strptime( self.req_time_str, TIME_FORMAT )[:6])
#             tdelta = (o2_time - sent_time).total_seconds()

#             if( abs(tdelta) > 1.0 ):
#                 print( '[%s] Time off by %d seconds, updating' % (self.name, tdelta) )
#                 self.send_func( o2cmd.SetTime() )

#             self.need_cfg = False
#             self.check_settings( )

#             self.add_files( self.current_cfg['FileList'] )
#             self.get_file()

#             if( (self.next_read < 1) and (self.read_file_in is None) ):
#                 self.next_read = time.time() + 1.0

#         elif( pkt.cmd == CMD_FILE_OPEN ):
#             if( pkt.recv_cmd != 0 ):
#                 print( '[%s] File Open Failed!' % self.name, self.read_file_in )
#                 self.send_func( o2pkt(CMD_FILE_CLOSE) )
#                 self.next_read = time.time() + 1.0
#                 return

#             self.read_block = 0
#             self.next_read = 0
#             self.read_want = self.read_size = struct.unpack( '<I', pkt.recv_data )[0]
#             if( self.verbose > 0 ):
#                 ostr = '[%s] File %s Opened, Size %d ' % (self.name, self.read_file_in, self.read_size)
#                 pad = 99 - len(ostr)
#                 if( pad > 0 ):
#                     ostr += ('-' * pad) + '|'
#                 print( ostr )
#                 print( '|', end='')
#                 self.read_percent = 1
#             self.send_func( o2pkt(CMD_FILE_READ, block=self.read_block) )
#             self.read_fp = open( self.read_file_out, 'wb' )
#         elif( pkt.cmd == CMD_FILE_READ ):
#             self.read_want -= len( pkt.recv_data )
#             self.read_block += 1
#             cur_percent = round(((self.read_size - self.read_want) / self.read_size) * 100)
#             if( (self.verbose > 0) and (cur_percent != self.read_percent) ):
#                 padc = ''
#                 if( cur_percent == 100 ):
#                     pad = 99 - self.read_percent
#                     if( pad > 0 ):
#                         padc = '=' * pad
#                     padc += '|'
#                     print( padc, flush=True )
#                 else:
#                     pad = cur_percent - self.read_percent
#                     padc = '=' * pad
#                     print( padc, end='', flush=True)

#             self.read_percent = cur_percent

#             if( self.read_want > 0 ):
#                 self.next_read = 0
#                 self.send_func( o2pkt(CMD_FILE_READ, block=self.read_block) )
#                 if( self.verbose > 2 ):
#                     print( '[%s] %d remaining' % (self.name, self.read_want) )
#                 if( self.read_fp ):
#                     self.read_fp.write(pkt.recv_data)
#             else:
#                 self.send_func( o2pkt(CMD_FILE_CLOSE) )
#                 if( self.read_fp ):
#                     self.read_fp.write(pkt.recv_data)
#                     self.read_fp.close()

#                     if( self.args.csv ):
#                         infile = o2fileread( self.read_file_out )
#                         oftype = 'csv'

#                         if( self.read_file_out[-4] == '.' ):
#                             outname = self.read_file_out[:-3] + oftype
#                         else:
#                             outname = self.read_file_out + '.' + oftype

#                         if( os.path.exists( outname ) ):
#                             print( 'Skipping %s: output file %s already exists' % (self.read_file_out, outname) )
#                         else:
#                             outfile = o2filewrite( outname, oftype )
#                             print( 'Converting %s (type: %s) to %s (type: %s)' % (self.read_file_out, infile.ftype, outname, outfile.ftype) )

#                             for rec in infile.records():
#                                 outfile.writerow( rec )

#                             outfile.close()
#                         infile.close()

#                 self.read_fp = None
#                 self.read_file_in = None
#                 self.read_file_out = None
#                 self.get_file()

#             if( self.verbose > 3 ):
#                 # here self.read_block is +1 which displays nicer
#                 print( '[%s] Block %d File Data:' % (self.name, self.read_block), pkt.recv_data.hex() )
#         elif( pkt.cmd == CMD_FILE_CLOSE ):
#             if( self.read_file_in is None ):
#                 self.send_func( o2pkt(CMD_READ_SENSORS) )
#         elif( pkt.cmd == CMD_CONFIG ):
#             if( pkt.recv_cmd != 0 ):
#                 print( '[%s] Config Write Failed!' % self.name, pkt.extra )
#         #elif( pkt.cmd == CMD_DISCONNECT ):
#         #    self.next_read = 0
#         #    print( '[%s] Disconnected' )
#         else:
#             print( '[%s] Unhandled Command %d, data:' % (self.name, pkt.cmd), pkt.recv_data.hex())


#     def check( self ):
#         if self.busy_func():
#             return

#         if( self.next_read > 0 and time.time() >= self.next_read ):
#             self.next_read = 0
#             if( self.need_cfg ):
#                 self.send_func( o2pkt(CMD_INFO) )
#                 self.req_time_str = time.strftime( TIME_FORMAT )
#             else:
#                 self.next_read = time.time() + 1.0
#                 self.send_func( o2pkt(CMD_READ_SENSORS) )
#                 if self.realtime:
#                     self.send_func( o2pkt(CMD_RT_DATA, long=True) )

#     def add_files( self, flist ):
#         self.want_files.extend( [i for i in flist.split(',') if i] )
#         if( (self.verbose > 0) and (not self.quiet_cfg) ):
#             print( '[%s] File List is now' % self.name, self.want_files )

#     def get_next_filename( self ):
#         if( len( self.want_files ) > 0 ):
#             return self.want_files.pop(0)

#         return None

#     def get_file( self ):
#         if( self.read_file_in is not None ):
#             return

#         ext = self.args.ext if self.args.ext is not None else 'vld'
#         prefix = self.args.prefix if self.args.prefix is not None else ('%s - ' % self.name)
#         fname = self.get_next_filename()

#         while( fname is not None ):
#             ofname = prefix + fname + ('.' if len(ext) > 0 else '') + ext
#             if( not os.path.exists(ofname) ):
#                 break

#             if( not self.quiet_cfg ):
#                 print( '[%s] Already Have File "%s"' % (self.name, ofname) )

#             fname = self.get_next_filename()

#         if( fname is not None ):
#             self.read_file_out = ofname
#             self.read_file_in = fname
#             self.read_percent = 0
#             self.read_block = self.read_want = self.read_size = 0
#             if( self.verbose > 0 ):
#                 ostr = '[%s] Requesting File %s, saving to "%s"' % (self.name, fname, ofname)
#                 print( ostr )
#             fname += chr(0)
#             self.send_func( o2pkt(CMD_FILE_OPEN, block=self.read_block, data=fname) )
#         #else:
#         #    self.send_func( o2pkt(CMD_READ_SENSORS) )

#     def close( self ):
#         self.next_read = 0
#         self.want_files = [ ]
#         self.read_want = 0
#         #self.dev.disconnect()

#     def check_settings( self ):
#         if( self.sent_cfg ):
#             return

#         check = {}
#         want_o2 = 2
#         if( self.args.o2_alert is not None ):
#             if( self.args.o2_alert < 1 ):
#                 check['OxiSwitch'] = 0
#             elif( self.args.o2_alert <= 100 ):
#                 check['CurOxiThr'] = self.args.o2_alert
#                 check['OxiSwitch'] = 1

#         if( self.args.hr_alert_high is not None ):
#             if( self.args.hr_alert_high < 1 ):
#                 check['HRSwitch'] = 0
#             elif( self.args.hr_alert_high <= 200 ):
#                 check['HRSwitch'] = 1
#                 check['HRHighThr'] = self.args.hr_alert_high

#         if( self.args.hr_alert_low is not None ):
#             if( self.args.hr_alert_low < 1 ):
#                 if 'HRSwitch' not in check:
#                     check['HRSwitch'] = 0
#             elif( self.args.hr_alert_low <= 200 ):
#                 check['HRSwitch'] = 1
#                 check['HRLowThr'] = self.args.hr_alert_low

#         # FIXME flip low/high if reversed

#         if( self.args.vibrate is not None ):
#             check['CurMotor'] = self.args.vibrate

#         if( self.args.screen is not None ):
#             if( self.args.screen ):
#                 check['LightingMode'] = 2
#             else:
#                 check['LightingMode'] = 0

#         if( self.args.brightness is not None ):
#             check['LightStr'] = self.args.brightness

#         #if( self.args.pedtar is not None ):
#         #    check['CurPedtar'] = self.args.pedtar

#         if( 'HRLowThr' in check ):
#             if( 'HRHighThr' in check ):
#                 if( check['HRLowThr'] > check['HRHighThr'] ):
#                     i = check['HRHighThr']
#                     check['HRHighThr'] = check['HRLowThr']
#                     check['HRLowThr'] = i
#             else:
#                 if( check['HRLowThr'] > int(self.current_cfg['HRHighThr']) ):
#                     check['HRHighThr'] = check['HRLowThr']
#                     #check['HRLowThr'] = int(self.current_cfg['HRHighThr'])
#                     del check['HRLowThr']
#         elif( 'HRHighThr' in check ):
#             if( check['HRHighThr'] < int(self.current_cfg['HRLowThr']) ):
#                 check['HRLowThr'] = check['HRHighThr']
#                 #check['HRHighThr'] = int(self.current_cfg['HRLowThr'])
#                 del check['HRHighThr']

#         update = {}

#         for i in check:
#             if( str(check[i]) != self.current_cfg[i] ):
#                 print('Updating', i, 'from', self.current_cfg[i], 'to', check[i])
#                 k = 'Set'
#                 if( i[:3] == 'Cur' ):
#                     k += i[3:]
#                 else:
#                     k += i

#                 update[k] = check[i]

#         #print('checked:', check)
#         #print('updating:', update)

#         if( len(update) > 0 ):
#             self.send_func( o2cmd.SetConfig(update) )
#             self.need_cfg = True
#             self.sent_cfg = True
#             self.quiet_cfg = False

import time
import json
import pprint
import struct
import os.path
import datetime

from .defines import *
from .o2pkt import o2pkt
from .o2cmd import o2cmd
from .o2file import *

class o2state:
    def __init__(self, name, data, args):
        self.name = name
        self.verbose = data['verbose']
        self.send_func = data['send']
        self.busy_func = data['busy']
        self.disconnect_func = data['disconnect']
        self.realtime = args.realtime
        self.args = args

        # internal state
        self.next_read = 0
        self.need_cfg = False
        self.sent_cfg = False
        self.quiet_cfg = False
        self.want_files = []
        self.read_file_out = None
        self.read_file_in = None
        self.read_block = None
        self.read_fp = None
        self.read_size = 0
        self.read_want = 0
        self.no_finger_count = 0
        self.disconnect_at = 1

        print('Starting up for', self.name)
        # kick off with an INFO request
        self.send_func(o2pkt(CMD_INFO))
        self.req_time_str = time.strftime(TIME_FORMAT)

    def recv(self, pkt):
        """
        Process an incoming packet and return parsed data:
          - CMD_READ_SENSORS: returns {
                'spo2','hr','battery','charging',
                'motion','hr_strength','finger_present'
            }
          - CMD_RT_DATA: returns {
                'timestamp','ppg_bytes'
            }
        Returns None for all other commands.
        """
        # debug‐print raw if verbose
        if self.verbose > 2:
            print(f"[{self.name}] RAW: {pkt.recv_data.hex()}")

        # on <src>=0 packet error
        if pkt.recv_cmd != 0:
            raise RuntimeError(f"[{self.name}] Command {pkt.cmd} failed: {pkt.recv_buf.hex()}")

        # 1) one‐shot sensor read
        if pkt.cmd == CMD_READ_SENSORS:
            # schedule next reading in 1s
            self.next_read = time.time() + 1.0

            buf = pkt.recv_data
            o2 = buf[0]
            hr = buf[1]
            batt = buf[7]
            charging = buf[8]
            motion = buf[9]
            hr_strength = buf[10]
            finger_present = bool(buf[11])

            return {
                'spo2':           o2,
                'hr':             hr,
                'battery':        batt,
                'charging':       charging,
                'motion':         motion,
                'hr_strength':    hr_strength,
                'finger_present': finger_present
            }

        # 2) realtime PPG waveform
        elif pkt.cmd == CMD_RT_DATA:
            ts = datetime.datetime.utcnow().isoformat()
            ppg = pkt.recv_data  # raw bytes of waveform
            return {
                'timestamp': ts,
                'ppg_bytes': ppg
            }

        # 3) info/config reply
        elif pkt.cmd == CMD_INFO:
            self.current_cfg = json.loads(pkt.recv_data.decode('ascii').rstrip('\0\r\n\t '))
            if not self.quiet_cfg:
                print(f"[{self.name}] Config:")
                pprint.PrettyPrinter(indent=4).pprint(self.current_cfg)

            # time drift adjustment
            o2_time = datetime.datetime(*time.strptime(self.current_cfg['CurTIME'], TIME_FORMAT)[:6])
            sent_time = datetime.datetime(*time.strptime(self.req_time_str, TIME_FORMAT)[:6])
            if abs((o2_time - sent_time).total_seconds()) > 1:
                print(f"[{self.name}] Clock off by {(o2_time - sent_time).total_seconds():.0f}s, syncing")
                self.send_func(o2cmd.SetTime())

            self.need_cfg = False
            self.check_settings()
            self.add_files(self.current_cfg['FileList'])
            # self.get_file()

            # trigger first sensor if idle
            if self.next_read < 1 and self.read_file_in is None:
                self.next_read = time.time() + 1.0

            return None

        # 4) file‐transfer flow
        elif pkt.cmd == CMD_FILE_OPEN:
            if pkt.recv_cmd != 0:
                print(f"[{self.name}] File open failed: {self.read_file_in}")
                self.send_func(o2pkt(CMD_FILE_CLOSE))
                self.next_read = time.time() + 1.0
                return None

            # initialize file read
            self.read_block = 0
            self.next_read = 0
            self.read_want = self.read_size = struct.unpack('<I', pkt.recv_data)[0]
            if self.verbose > 0:
                print(f"[{self.name}] Opened {self.read_file_in}, size={self.read_size}")
                print('|', end='', flush=True)
                self.read_percent = 1

            self.send_func(o2pkt(CMD_FILE_READ, block=self.read_block))
            self.read_fp = open(self.read_file_out, 'wb')
            return None

        elif pkt.cmd == CMD_FILE_READ:
            # write chunk, progress bar update
            self.read_want -= len(pkt.recv_data)
            self.read_block += 1
            if self.read_fp:
                self.read_fp.write(pkt.recv_data)

            if self.read_want > 0:
                # still more
                self.send_func(o2pkt(CMD_FILE_READ, block=self.read_block))
            else:
                # done reading
                self.send_func(o2pkt(CMD_FILE_CLOSE))
                if self.read_fp:
                    self.read_fp.close()
                # optionally convert to CSV
                # if self.args.csv:
                #     self._convert_vld_to_csv()
                # reset and grab next
                self.read_fp = None
                self.read_file_in = None
                self.read_file_out = None
                # self.get_file()
            return None

        elif pkt.cmd == CMD_FILE_CLOSE:
            # once files done, resume sensors
            if self.read_file_in is None:
                self.send_func(o2pkt(CMD_READ_SENSORS))
            return None

        elif pkt.cmd == CMD_CONFIG:
            if pkt.recv_cmd != 0:
                print(f"[{self.name}] Config write failed: {pkt.extra}")
            return None

        # everything else
        return None

    def check(self):
        if self.busy_func():
            return

        # time for next read?
        if self.next_read > 0 and time.time() >= self.next_read:
            self.next_read = 0
            if self.need_cfg:
                self.send_func(o2pkt(CMD_INFO))
                self.req_time_str = time.strftime(TIME_FORMAT)
            else:
                self.next_read = time.time() + 1.0
                self.send_func(o2pkt(CMD_READ_SENSORS))
                if self.realtime:
                    self.send_func(o2pkt(CMD_RT_DATA, long=True))

    def add_files( self, flist ):
        self.want_files.extend( [i for i in flist.split(',') if i] )
        if( (self.verbose > 0) and (not self.quiet_cfg) ):
            print( '[%s] File List is now' % self.name, self.want_files )

    def get_next_filename( self ):
        if( len( self.want_files ) > 0 ):
            return self.want_files.pop(0)

        return None

    def get_file( self ):
        if( self.read_file_in is not None ):
            return

        ext = self.args.ext if self.args.ext is not None else 'vld'
        prefix = self.args.prefix if self.args.prefix is not None else ('%s - ' % self.name)
        fname = self.get_next_filename()

        while( fname is not None ):
            ofname = prefix + fname + ('.' if len(ext) > 0 else '') + ext
            if( not os.path.exists(ofname) ):
                break

            if( not self.quiet_cfg ):
                print( '[%s] Already Have File "%s"' % (self.name, ofname) )

            fname = self.get_next_filename()

        if( fname is not None ):
            self.read_file_out = ofname
            self.read_file_in = fname
            self.read_percent = 0
            self.read_block = self.read_want = self.read_size = 0
            if( self.verbose > 0 ):
                ostr = '[%s] Requesting File %s, saving to "%s"' % (self.name, fname, ofname)
                print( ostr )
            fname += chr(0)
            self.send_func( o2pkt(CMD_FILE_OPEN, block=self.read_block, data=fname) )
        #else:
        #    self.send_func( o2pkt(CMD_READ_SENSORS) )

    def close( self ):
        self.next_read = 0
        self.want_files = [ ]
        self.read_want = 0
        #self.dev.disconnect()

    def check_settings( self ):
        if( self.sent_cfg ):
            return

        check = {}
        want_o2 = 2
        if( self.args.o2_alert is not None ):
            if( self.args.o2_alert < 1 ):
                check['OxiSwitch'] = 0
            elif( self.args.o2_alert <= 100 ):
                check['CurOxiThr'] = self.args.o2_alert
                check['OxiSwitch'] = 1

        if( self.args.hr_alert_high is not None ):
            if( self.args.hr_alert_high < 1 ):
                check['HRSwitch'] = 0
            elif( self.args.hr_alert_high <= 200 ):
                check['HRSwitch'] = 1
                check['HRHighThr'] = self.args.hr_alert_high

        if( self.args.hr_alert_low is not None ):
            if( self.args.hr_alert_low < 1 ):
                if 'HRSwitch' not in check:
                    check['HRSwitch'] = 0
            elif( self.args.hr_alert_low <= 200 ):
                check['HRSwitch'] = 1
                check['HRLowThr'] = self.args.hr_alert_low

        # FIXME flip low/high if reversed

        if( self.args.vibrate is not None ):
            check['CurMotor'] = self.args.vibrate

        if( self.args.screen is not None ):
            if( self.args.screen ):
                check['LightingMode'] = 2
            else:
                check['LightingMode'] = 0

        if( self.args.brightness is not None ):
            check['LightStr'] = self.args.brightness

        #if( self.args.pedtar is not None ):
        #    check['CurPedtar'] = self.args.pedtar

        if( 'HRLowThr' in check ):
            if( 'HRHighThr' in check ):
                if( check['HRLowThr'] > check['HRHighThr'] ):
                    i = check['HRHighThr']
                    check['HRHighThr'] = check['HRLowThr']
                    check['HRLowThr'] = i
            else:
                if( check['HRLowThr'] > int(self.current_cfg['HRHighThr']) ):
                    check['HRHighThr'] = check['HRLowThr']
                    #check['HRLowThr'] = int(self.current_cfg['HRHighThr'])
                    del check['HRLowThr']
        elif( 'HRHighThr' in check ):
            if( check['HRHighThr'] < int(self.current_cfg['HRLowThr']) ):
                check['HRLowThr'] = check['HRHighThr']
                #check['HRHighThr'] = int(self.current_cfg['HRLowThr'])
                del check['HRHighThr']

        update = {}

        for i in check:
            if( str(check[i]) != self.current_cfg[i] ):
                print('Updating', i, 'from', self.current_cfg[i], 'to', check[i])
                k = 'Set'
                if( i[:3] == 'Cur' ):
                    k += i[3:]
                else:
                    k += i

                update[k] = check[i]

        #print('checked:', check)
        #print('updating:', update)

        if( len(update) > 0 ):
            self.send_func( o2cmd.SetConfig(update) )
            self.need_cfg = True
            self.sent_cfg = True
            self.quiet_cfg = False

