"""
物理接口，支持：TCP/IP， Serial, GPIB, USB ...
"""
import serial
import logging
import socket
import visa


class LinkTCP(object):
    '''
    '''
    _max_number = 10240      # 每包最大字节数
    _timeout_unit = 0.01    # seconds socket.recv 超时

    def __init__(self, host=None, port=None, logger=None):
        self.logger = logger

        self.is_open = False
        
        self.host = host
        self.port = int(port)
        self.client = None
    
    def __del__(self):
        self.close()

    def clear(self):
        pass

    def open(self):
        socket.setdefaulttimeout(5)  # socket全局timeout
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((self.host, self.port))
        self.client.settimeout(self._timeout_unit)
        self.is_open = True

    def close(self):
        if self.client is not None:
            self.client.close()
            self.client = None
            self.is_open = False

    def send(self, data):
        '''
        发送命令， data是已经打包好的命令数据
        return:  命令对应的返回数据或 None
        '''
        if self.client:
            self.client.send(data)

    def recv(self, timeout=1):
        '''
        命令数据接收
        '''
        if self.client:
            return self.client.recv(self._max_number)
        return ''

class LinkRS232(object):
    '''
    '''
    _max_number = 10240      # 每包最大字节数
    _timeout_unit = 0.01    # seconds socket.recv 超时
    _timeout_serial = 0.01   # 串口读超时

    def __init__(self, serial_dev=None, com_parameter=None, logger=None):
        self.logger = logger

        self.is_open = False
        
        self.serial_dev = serial_dev
        self.com_parameter = com_parameter if com_parameter is not None else (115200,'N',8,1)
        self.client = None
        
    
    def __del__(self):
        self.close()
    
    def clear(self):
        if self.client:
            self.client.flushInput()

    def open(self):
        self.client = serial.Serial(self.serial_dev,
                                    baudrate=int(self.com_parameter[0]), 
                                    parity=self.com_parameter[1],
                                    bytesize=int(self.com_parameter[2]),
                                    stopbits=int(self.com_parameter[3]),
                                    timeout=self._timeout_serial)
        self.is_open = True

    def close(self):
        if self.client is not None:
            self.client.close()
            self.client = None
            self.is_open = False

    def send(self, data):
        '''
        发送命令， data是已经打包好的命令数据
        return:  命令对应的返回数据或 None
        '''
        if self.client:
            self.client.write(data)

    def recv(self, timeout=1):
        '''
        命令数据接收
        '''
        if self.client:
            return self.client.read(self._max_number)
        return ''

class LinkGPIB(object):
    '''
    '''

    def __init__(self, gpib='GPIB0::16::INSTR', logger=None):
        self.logger = logger

        self.is_open = False
        
        self.gpib = gpib
        self.client = None
        
    
    def __del__(self):
        self.close()

    def clear(self):
        pass

    def open(self):
        # self.client = serial.Serial(self.serial_dev,
        rm = visa.ResourceManager()
        self.client = rm.open_resource(self.gpib)
        self.client.timeout = 40000  # 5 sec
        self.is_open = True

    def close(self):
        if self.client is not None:
            self.client.close()
            self.client = None
            self.is_open = False

    def send(self, data):
        '''
        发送命令， data是已经打包好的命令数据
        return:  命令对应的返回数据或 None
        '''
        if self.client:
            self.client.write(data)

    def read_raw(self):
        '''
        发送命令， data是已经打包好的命令数据
        return:  命令对应的返回数据或 None
        '''
        if self.client:
            return self.client.read_raw()
        return ""
    
    def read_byte(self, num=20):
        '''
        发送命令， data是已经打包好的命令数据
        return:  命令对应的返回数据或 None
        '''
        if self.client:
            return self.client.read_bytes(num).decode()
        return b""
    
    
    def read(self):
        '''
        命令数据读取
        '''
        if self.client:
            return self.client.read()
        return ''

    def query(self, data, timeout=1):
        '''
        命令数据接收
        '''
        if self.client:
            return self.client.query(data)
        return ''

class LinkUSB(object):
    '''
    '''

    def __init__(self, usb='USB0::0x2A8D::0x0201::MY57700228::INSTR', logger=None):
        self.logger = logger

        self.is_open = False
        
        self.usb = usb
        self.client = None
        
    
    def __del__(self):
        self.close()

    def clear(self):
        pass

    def open(self):
        rm = visa.ResourceManager()
        self.client = rm.open_resource(self.usb)
        self.client.timeout = 40000  # 5 sec
        self.is_open = True

    def close(self):
        if self.client is not None:
            self.client.close()
            self.client = None
            self.is_open = False

    def send(self, data):
        '''
        发送命令， data是已经打包好的命令数据
        return:  命令对应的返回数据或 None
        '''
        if self.client:
            self.client.write(data)

    def query(self, data, timeout=1):
        '''
        命令数据接收
        '''
        if self.client:
            return self.client.query(data)
        return ''

    
    def read(self):
        '''
        命令数据读取
        '''
        if self.client:
            return self.client.read()
        return ''

class LinkVISARS232(object):
    '''
    '''

    def __init__(self, serial_dev=None, baud=None, termination="", logger=None):
        self.logger = logger

        self.is_open = False
        
        self.serial_dev = serial_dev
        self.baud, self.termination = baud, termination
        self.client = None

        self.__map = {
            "CR": '\r',
            "LF": '\n',
            "CRLF": '\r\n'
        }
        
    
    def __del__(self):
        self.close()

    def clear(self):
        pass

    def open(self):
        rm = visa.ResourceManager()
        self.client = rm.open_resource(self.serial_dev)
        self.client.baud_rate = self.baud
        self.client.read_termination = self.__map[self.termination.upper()]
        self.client.write_termination = self.__map[self.termination.upper()]

        self.client.timeout = 40000  # 5 sec
        self.is_open = True

    def close(self):
        if self.client is not None:
            self.client.close()
            self.client = None
            self.is_open = False

    def send(self, data):
        '''
        发送命令， data是已经打包好的命令数据
        return:  命令对应的返回数据或 None
        '''
        if self.client:
            self.client.write(data)

    def query(self, data, timeout=1):
        '''
        命令数据接收
        '''
        if self.client:
            return self.client.query(data)
        return ''

    
    def read(self):
        '''
        命令数据读取
        '''
        if self.client:
            return self.client.read()
        return ''

class LinkVISATCP(object):
    '''
    '''

    def __init__(self, host=None, port=None, logger=None):
        self.logger = logger

        self.is_open = False
        
        self.host = host
        self.port = int(port)
        self.client = None
    
    def __del__(self):
        self.close()

    def clear(self):
        pass

    def open(self):
        rm = visa.ResourceManager()
        self.client = rm.open_resource("TCPIP::{}::inst0::INSTR".format(self.host))
        self.client.timeout = 40000  # 5 sec
        self.is_open = True

    def close(self):
        if self.client is not None:
            self.client.close()
            self.client = None
            self.is_open = False

    def send(self, data):
        '''
        发送命令， data是已经打包好的命令数据
        return:  命令对应的返回数据或 None
        '''
        if self.client:
            self.client.write(data)

    def query(self, data, timeout=1):
        '''
        命令数据接收
        '''
        if self.client:
            return self.client.query(data)
        return ''

    def read(self):
        '''
        命令数据读取
        '''
        if self.client:
            return self.client.read()
        return ''


if __name__ == "__main__":
    import time

    obj = LinkVISARS232(serial_dev="ASRL3::INSTR", baud=115200, termination="LF", logger=None)
    obj.open()

    # print(obj.query("*IDN?"))
    # print(obj.client.read())

    # print(obj.query("RANGE 1V"))
    # print(obj.query("RANGE?"))
    # print(obj.client.read())

    # print(obj.query("MEAS?"))
    # print(obj.client.read())

    # print(obj.query("VAL?"))
    # print(obj.client.read())

    print(obj.query("INPUT INPUT1;MEAS?"))
    print(obj.client.read())