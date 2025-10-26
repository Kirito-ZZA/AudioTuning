"""
物理接口，支持：TCP/IP， Serial
"""
import struct, time


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

    def __init__(self, phy_link=None, logger=None):
        self.logger = logger

        self.is_open = False
        
        self.phy_link = phy_link
        self.recv_buf = b''

    def send_raw(self, data, ack=None, limit=1, enable_recv=True):
        '''
        发送命令， data是已经打包好的命令数据
        return:  命令对应的返回数据或 None
        '''
        self.clear_buf()
        self.phy_link.write(data)
        
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
                self.recv_buf += self.phy_link.read(self._max_number)
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

    def clear_buf(self):
        self.recv_buf = b''
        self.phy_link.clear()
