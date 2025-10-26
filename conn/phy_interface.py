"""
物理接口，支持：TCP/IP， Serial
"""
import serial
import logging
import sys
import socket
import time
import struct
import threading


class Interface(object):
    '''
    Physical Interface, support serial and tcp now.
    '''
    _max_number = 10240      # 每包最大字节数
    _timeout_unit = 0.01    # seconds socket.recv 超时
    _timeout_counts = 100   # 允许超时次数

    _timeout_serial = _timeout_unit   # 串口读超时

    _frame_id = 0x02
    _frame_type = 0x00
    _frame_seq = 0x00
    _frame_end = 0x03

    def __init__(self, host=None, port=None, serial_dev=None, com_parameter=None, logger=None):
        if logger is None:
            self.logger = logging.getLogger(__name__)
            self.logger.setLevel(logging.INFO)
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        else:
            self.logger = logger

        self.is_open = False
        
        self.client = None
        if host is not None and port is not None:
            self.host = host
            self.port = int(port)
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        elif serial_dev is not None:
            self.serial_dev = serial_dev
            if com_parameter is None:
                self.client = serial.Serial(serial_dev, 115200, timeout=self._timeout_serial)
            else:
                self.client = serial.Serial(serial_dev, baudrate=com_parameter[0], 
                    parity=com_parameter[1], bytesize=com_parameter[2], stopbits=com_parameter[3], timeout=self._timeout_serial)

        self.recv_buf = b''
    
    def __del__(self):
        self.close()

    def open(self):
        if isinstance(self.client, socket.socket):
            self.client.connect((self.host, self.port))
            self.client.settimeout(self._timeout_unit)
            self.is_open = True
        elif isinstance(self.client, serial.Serial):
            if not self.client.isOpen():
                self.client.open()
            self.is_open = self.client.isOpen()
        else:
            self.is_open = False

    def close(self):
        if self.client is not None:
            self.client.close()
            self.client = None
            self.is_open = False

    def send(self, data, typ=None, errors=[b'SPI_ERR'], timeout=1):
        '''
        发送命令， data是已经打包好的命令数据
        return:  命令对应的返回数据或 None
        '''
        self.clear_buf()
        if isinstance(self.client, socket.socket):
            self.client.send(data)
        elif isinstance(self.client, serial.Serial):
            self.client.write(data)
        r = self.recv(timeout=timeout)

        for i in range(100):
            if r is None:
                return None
            is_err = False
            # 类型检查
            if typ is not None and typ not in r:
                is_err = True
            # 错误代码检查
            for err in errors:
                if err in r:
                    is_err = True
                    break
            if is_err is True:
                # print("{}, r={}".format(i, r))
                r = self.recv(timeout=timeout)
            else:
                break
        return r

    def send_multi_recv(self, data, typ=None, errors=[b'SPI_ERR'], recv_count=1):
        '''
        发送命令， data是已经打包好的命令数据
        return:  命令对应的返回数据或 None
        '''
        self.clear_buf()
        if isinstance(self.client, socket.socket):
            self.client.send(data)
        elif isinstance(self.client, serial.Serial):
            self.client.write(data)
        recv_list = []
        time_out = 1
        pre = time.time()
        for i in range(recv_count):
            r = self.recv()
            now = time.time()
            if r is not None and b'Net Init OK' not in r:
                recv_list.append(r)
                pre = now
            if now - pre > time_out:
                break
        return recv_list

    def send_raw(self, data, ack=None, limit=1, enable_recv=True):
        '''
        发送命令， data是已经打包好的命令数据
        return:  命令对应的返回数据或 None
        '''
        self.clear_buf()
        if isinstance(self.client, socket.socket):
            self.client.send(data)
        elif isinstance(self.client, serial.Serial):
            self.client.write(data)
        
        if enable_recv:
            return self.recv_raw(ack=ack, limit=limit)
        else:
            return ""

    def recv_raw(self, ack=None, limit=1):
        '''
        命令 原始数据接收
        '''
        timeout_counts = 0
        while timeout_counts < self._timeout_counts:
            try:
                if isinstance(self.client, socket.socket):
                    self.recv_buf += self.client.recv(self._max_number)
                elif isinstance(self.client, serial.Serial):
                    self.recv_buf += self.client.read(self._max_number)
            except:
                timeout_counts += 1
                time.sleep(self._timeout_unit)
            finally:
                if ack is None and len(self.recv_buf)>=limit:
                    return self.recv_buf

                if ack is not None and ack in self.recv_buf:
                    return self.recv_buf

                if timeout_counts > self._timeout_counts:
                    self.logger.error('Do not recieve response')
                    return None

        self.logger.error('Do not recieve response')
        return None

    def recv(self, timeout=1):
        '''
        命令数据接收
        '''
        # recv_buf = b''
        timeout_counts = 0
        exceed_hits = 0
        while True:
            try:
                if len(self.recv_buf) < 10240:
                    if isinstance(self.client, socket.socket):
                        self.recv_buf += self.client.recv(self._max_number)
                    elif isinstance(self.client, serial.Serial):
                        tl = self.client.read(self._max_number)
                        if len(tl) > 0:
                            self.recv_buf += tl
                        else:
                            timeout_counts += 1
                    exceed_hits = 0
                else:
                    exceed_hits += 1
            except:
                if len(self.recv_buf) < 10240:
                    timeout_counts += 1
                    time.sleep(self._timeout_unit)
                    exceed_hits = 0
                else:
                    exceed_hits += 1
            finally:
                if self._frame_id in self.recv_buf and self._frame_end in self.recv_buf:
                    # frame_id, frame_type, frame_seq, dsr, src, length 
                    _, _, _, _, _, length = struct.unpack('>5BH', self.recv_buf[self.recv_buf.index(self._frame_id):self.recv_buf.index(self._frame_id)+7])
                    if len(self.recv_buf) >= (length+self.recv_buf.index(self._frame_id)-1) and \
                        self._frame_end == self.recv_buf[self.recv_buf.index(self._frame_id) + length - 1]:
                        
                        package = self.recv_buf[self.recv_buf.index(self._frame_id): self.recv_buf.index(self._frame_id) + length]
                        self.recv_buf = self.recv_buf[self.recv_buf.index(self._frame_id) + length:]
                        return package
                if timeout_counts > max(self._timeout_counts, timeout//self._timeout_unit):
                    self.logger.error('Do not recieve response')
                    return None
                if exceed_hits>100:
                    self.recv_buf = b''
                l= len(self.recv_buf)

    def clear_buf(self):
        self.recv_buf = b''
        try:
            if isinstance(self.client, socket.socket):
                # self.client.recv(self._max_number)
                pass
            elif isinstance(self.client, serial.Serial):
                self.client.flushInput()
        except:
            self.logger.warning('flushInput')
