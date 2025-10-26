"""
通信协议数据流编解码
"""
import struct
import re
import logging
import sys
from threading import Lock

import numpy as np
import pandas as pd


class Formatter(object):
    '''
    Package Format:
        ByteAddress     Name            Content         Memo
        0               FrameID         0x02            Start Character
        1               FrameType       0x00            Frame Type
        2               FrameSeq        0x00            Frame Number
        3               Destination     Addr            Srouce Address
        4               Srouce          Addr            Destination Address
        5               Length          High 8 bits     Frame Length(==N)
        6               Length          Low 8 bits  
        7
        ...             Data
        N-4
        N-3             CRC16           High 8 bits     TODO: need to update in the future
        N-2             CRC16           Low 8 bits
        N-1             EndID           0x03            End Character
        N~N+2           Redundant       0x03 
    '''
    _frame_id = 0x02
    _frame_type = 0x00
    _frame_seq = 0x00
    _frame_end = 0x03

    CRC16Table = [ 
        0x0, 0x1021, 0x2042, 0x3063, 0x4084, 0x50a5, 0x60c6, 0x70e7, 
        0x8108, 0x9129, 0xa14a, 0xb16b, 0xc18c, 0xd1ad, 0xe1ce, 0xf1ef, 
        0x1231, 0x210, 0x3273, 0x2252, 0x52b5, 0x4294, 0x72f7, 0x62d6, 
        0x9339, 0x8318, 0xb37b, 0xa35a, 0xd3bd, 0xc39c, 0xf3ff, 0xe3de, 
        0x2462, 0x3443, 0x420, 0x1401, 0x64e6, 0x74c7, 0x44a4, 0x5485, 
        0xa56a, 0xb54b, 0x8528, 0x9509, 0xe5ee, 0xf5cf, 0xc5ac, 0xd58d, 
        0x3653, 0x2672, 0x1611, 0x630, 0x76d7, 0x66f6, 0x5695, 0x46b4, 
        0xb75b, 0xa77a, 0x9719, 0x8738, 0xf7df, 0xe7fe, 0xd79d, 0xc7bc, 
        0x48c4, 0x58e5, 0x6886, 0x78a7, 0x840, 0x1861, 0x2802, 0x3823, 
        0xc9cc, 0xd9ed, 0xe98e, 0xf9af, 0x8948, 0x9969, 0xa90a, 0xb92b, 
        0x5af5, 0x4ad4, 0x7ab7, 0x6a96, 0x1a71, 0xa50, 0x3a33, 0x2a12, 
        0xdbfd, 0xcbdc, 0xfbbf, 0xeb9e, 0x9b79, 0x8b58, 0xbb3b, 0xab1a, 
        0x6ca6, 0x7c87, 0x4ce4, 0x5cc5, 0x2c22, 0x3c03, 0xc60, 0x1c41, 
        0xedae, 0xfd8f, 0xcdec, 0xddcd, 0xad2a, 0xbd0b, 0x8d68, 0x9d49, 
        0x7e97, 0x6eb6, 0x5ed5, 0x4ef4, 0x3e13, 0x2e32, 0x1e51, 0xe70, 
        0xff9f, 0xefbe, 0xdfdd, 0xcffc, 0xbf1b, 0xaf3a, 0x9f59, 0x8f78, 
        0x9188, 0x81a9, 0xb1ca, 0xa1eb, 0xd10c, 0xc12d, 0xf14e, 0xe16f, 
        0x1080, 0xa1, 0x30c2, 0x20e3, 0x5004, 0x4025, 0x7046, 0x6067, 
        0x83b9, 0x9398, 0xa3fb, 0xb3da, 0xc33d, 0xd31c, 0xe37f, 0xf35e, 
        0x2b1, 0x1290, 0x22f3, 0x32d2, 0x4235, 0x5214, 0x6277, 0x7256, 
        0xb5ea, 0xa5cb, 0x95a8, 0x8589, 0xf56e, 0xe54f, 0xd52c, 0xc50d, 
        0x34e2, 0x24c3, 0x14a0, 0x481, 0x7466, 0x6447, 0x5424, 0x4405, 
        0xa7db, 0xb7fa, 0x8799, 0x97b8, 0xe75f, 0xf77e, 0xc71d, 0xd73c, 
        0x26d3, 0x36f2, 0x691, 0x16b0, 0x6657, 0x7676, 0x4615, 0x5634, 
        0xd94c, 0xc96d, 0xf90e, 0xe92f, 0x99c8, 0x89e9, 0xb98a, 0xa9ab, 
        0x5844, 0x4865, 0x7806, 0x6827, 0x18c0, 0x8e1, 0x3882, 0x28a3, 
        0xcb7d, 0xdb5c, 0xeb3f, 0xfb1e, 0x8bf9, 0x9bd8, 0xabbb, 0xbb9a, 
        0x4a75, 0x5a54, 0x6a37, 0x7a16, 0xaf1, 0x1ad0, 0x2ab3, 0x3a92, 
        0xfd2e, 0xed0f, 0xdd6c, 0xcd4d, 0xbdaa, 0xad8b, 0x9de8, 0x8dc9, 
        0x7c26, 0x6c07, 0x5c64, 0x4c45, 0x3ca2, 0x2c83, 0x1ce0, 0xcc1, 
        0xef1f, 0xff3e, 0xcf5d, 0xdf7c, 0xaf9b, 0xbfba, 0x8fd9, 0x9ff8, 
        0x6e17, 0x7e36, 0x4e55, 0x5e74, 0x2e93, 0x3eb2, 0xed1, 0x1ef0]

    def __init__(self, logger=None):
        if logger is None:
            self.logger = logging.getLogger(__name__)
            self.logger.setLevel(logging.INFO)
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        else:
            self.logger = logger

    def crc16(self, data):
        
        crc = (data[0] << 8) | data[1]
        for byte in data[2:]:
            tableNo = (crc >> 8) & 0xff
            crc = (((crc << 8) | byte) ^ self.CRC16Table[tableNo]) & 0xffff
        
        return (crc>>8) & 0xff, crc & 0xff

    def crc8(self, data):
        high, low = data[0], data[1]
        
        for byte in data[2:]:
            t = byte
            
            for i in range(8):
                b1 = ((t&0x80)>>7) &0x01
                t = (t<<1) & 0xff

                b2 = ((low&0x80)>>7) &0x01
                low = (low<<1) | b1

                b3 = ((high&0x80)>>7) &0x01
                high = (high<<1)|b2

                high &= 0xff

                if(b3==1):
                    high = high ^ 0x10
                    low = low ^ 0x21

                high &= 0xff
                low &= 0xff

        return high, low
        # return ((high<<8)&0xff00) | low


    def pack(self, data):
        '''
        data:    unicode str
        '''
        # format_str = '>5BH{}sH4B'.format(len(data))  # big-endian
        # return struct.pack(format_str, 2, 0, 0, 0, 0, len(data) + 10, data.encode('UTF-8'), len(data) + 10, 3, 3, 3, 3)

        format_str = '>5BH{}s2B'.format(len(data))  # big-endian
        d =  struct.pack(format_str, 2, 0, 0, 0, 0, len(data) + 10, data.encode('UTF-8'), 0, 0)
        # crc = self.crc16(d)
        high, low = self.crc16(d)
        return struct.pack("{}s6B".format(len(d[:-2])), d[:-2], high, low, 3, 3, 3, 3)
        
    def unpack(self, data):
        '''
        data:   bytes
        '''
        unpacked_data = b''
        start_index = data.index(self._frame_id)
        # frame_id, frame_type, frame_seq, dsr, src, length
        _, _, _, _, _, length = struct.unpack(
            '>5BH', data[start_index:start_index+7])
        end_index = start_index + length - 1

        if self._frame_end == data[end_index]:
            package = data[start_index:end_index+1]
            # unpacked_data, crc, end
            unpacked_data, _, _ = struct.unpack(
                '>{}sHB'.format(length-10), package[7:])
        return unpacked_data


class RegexFormatter(Formatter):
    '''
    '''

    def __init__(self, logger=None):
        if logger is None:
            self.logger = logging.getLogger(__name__)
            self.logger.setLevel(logging.INFO)
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        else:
            self.logger = logger

    def group(self, subject):
        group_map = {}
        dev_sel = None
        # for item in self.unpack(subject).decode('UTF-8').replace(' ', '').split('|'):
        unpacked_data = self.unpack(subject).decode('GBK').replace(' ', '')
        self.logger.info('Command Recv RawByte: {}'.format(unpacked_data))
        for item in unpacked_data.split('|'):
            l = item.split('=')
            if len(l) >= 2:
                if l[0].upper() == 'DEVSEL':
                    dev_sel = l[1]
                else:
                    key = "{}.{}".format(dev_sel, l[0]) if dev_sel is not None else l[0]
                    group_map[key] = l[1]
            else:
                group_map[l[0]] = ""
            # group_map[l[0]] = l[1] if len(l) >= 2 else ""
        return group_map

    def group_value(self, subject, retrive_number=True):
        group_map = {}
        for key, value in self.group(subject).items():
            list_value = value.split(',')
            if len(list_value) > 1:
                list_number = []
                for item in list_value:
                    match = re.search(r"^[0-9.\-\+]+[0-9.eE\-\+]*", item, re.IGNORECASE)
                    if match:
                        number = float(match.group(0))
                        list_number.append(number)
                group_map[key] = {"value": list_number, "unit": "", "type": "list"} 
            else:
                # unit removal
                match = re.search(r"^[0-9.\-\+]+[0-9.eE\-\+]*", list_value[0], re.IGNORECASE)
                if retrive_number and match:
                    number = float(match.group(0))
                    unit = list_value[0][len(match.group(0)):]
                    group_map[key] = {"value": number, "unit": unit, "type": "number"}
                else:
                    group_map[key] = {"value": value, "type": "str"}
        return group_map

    def group_binary(self, subject, formatter='f'):
        binary = self.unpack(subject)
        # start, cmd, devstat, length
        # _, _, devstat, length = struct.unpack('<2BHL', binary[:8])
        _, _, devstat, length, offset, _ = struct.unpack('<2B2H2B', binary[:8])
        # length = (len(binary) - 8) // 4
        data = struct.unpack('<{}{}'.format(length, formatter), binary[8:])
        group_map = {
            'channel': devstat,
            'offset': offset,
            'data': data
        }
        return group_map


def synchronized(lock):
    """ Synchronization decorator. """
    def wrap(f):
        def new_function(*args, **kw):
            lock.acquire(timeout=25)
            try:
                return f(*args, **kw)
            finally:
                lock.release()
        return new_function
    return wrap

class PandasFormatter(object):
    '''
    pandas 数据结构生成
    '''
    _channel_name = {
        0x01: 'UA',
        0x02: 'UB',
        0x03: 'UC',
        0x04: 'IA',
        0x05: 'IB',
        0x06: 'IC',
        0x36: 'DCV',
        0x37: 'DCI',
        0x54: 'B1',
        0x55: 'B2',
        0x56: 'B3',
    }

    lock1, lock2 = Lock(), Lock()

    def __init__(self):
        self.data = {}
        self.points = {}
        self.points_cum = 0

    @synchronized(lock1)
    def add(self, package):
        '''
        package:{
            'channel':  int
            'offset': int
            'data':     list
        }
        '''
        s = pd.Series(package['data'])
        
        if package['channel'] not in self._channel_name.keys():
            self._channel_name[package['channel']] = '{}'.format(package['channel'])
        if self._channel_name[package['channel']] not in self.data.keys():
            self.data[self._channel_name[package['channel']]] = s
        else:
            self.data[self._channel_name[package['channel']]] = pd.concat(
                [self.data[self._channel_name[package['channel']]], s], ignore_index=True)

    def get(self):
        df = pd.DataFrame(self.data)
        return df.dropna()

    @synchronized(lock1)
    def cut(self, size=1000):
        cut_data = {}
        for key, s in self.data.items():
            if s.shape[0] > size:
                cut_data[key] = s[:size].values
                self.data[key] = s.drop(range(size)).reset_index(drop=True)
                # self.data[key].reset_index(drop=True, inplace=True)
        return cut_data

    @synchronized(lock2)
    def add_point(self, package):
        '''
        package:{'ENER': '', 'ACF.MEAS_LISTVAL': '49.99997Hz'}
        '''
        if 'ENER' in package.keys():
            for key, val in package.items():
                if key != 'ENER':
                    if key in self.points.keys():
                        for item in val.split(','):
                            self.points[key].append(item)
                    else:
                        self.points[key] = val.split(',')
                    if key == 'UA.MEAS_LISTVAL':
                        self.points_cum += len(val.split(','))

    @synchronized(lock2)
    def cut_point(self):
        cut_data = {}
        
        if self.points_cum >= 4:
            for key, val in self.points.items():
                if len(self.points[key]) > 0:
                    cut_data[key.split('.')[0]] = self.points[key].pop(0)
            self.points_cum -= 1

        return cut_data
