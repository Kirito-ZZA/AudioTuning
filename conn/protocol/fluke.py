"""
Fluke 通信协议应用接口类
"""
import logging
import sys
import time

import numpy as np

from utility.unit_converter import unit_split
from .interface.link import LinkGPIB, LinkUSB, LinkVISARS232


class Protocol8588():
    _timeout_unit = 0.01

    def __init__(self, model=None, phy=None, protocol=None, logger=None, **kwargc):
        super().__init__()
        self.logger = logger

        if phy.upper() == 'GPIB':
            gpib_addr = kwargc.get('GPIB')
            self.phy_link = LinkGPIB(gpib=gpib_addr, logger=self.logger)
        else:
            usb_addr = kwargc.get('usb')
            self.phy_link = LinkUSB(usb=usb_addr, logger=self.logger)

        self.interface = self.phy_link

        self.phy_link.open()

        self.map_unit = {
            'MEAS:VOLT:DC?': ('DC', 'V'),
            'READ?DC': ('DC', 'V'),
            'READ?AC': ('AC', 'V'),
            'READ?R': ('R', 'ohm'),
            'MEAS:VOLT:AC?': ('AC', 'V'),
        }

        self.read_only = ['MEAS:VOLT:DC?', 'READ?', 'READ?DC', 'READ?AC', 'READ?R']

    def __del__(self):
        self.close()

    def close(self):
        self.phy_link.close()

    def get_name(self):
        try:
            return self.interface.query("*IDN?")
        except:
            return ""

    def cmd(self, cmds, skip_formatter=False):
        response_str = ""
        for cmd in cmds.split('|'):
            self.logger.info('Send Command: {}'.format(cmd))
            if cmd.split(' ')[0] not in self.read_only:
                self.interface.send(cmd)
            else:
                response_str = self.interface.query('READ?' if 'READ?' in cmd else cmd).split("\n")[0]
                # self.logger.info('Command Recv: {}'.format(response_str))
        return response_str


if __name__ == "__main__":

    pl = Protocol8588(gpib='GPIB0::17::INSTR')

    r = pl.cmd('*CLS')
    r = pl.cmd('OUT 10mV')
    print(r)
    time.sleep(1)
    r = pl.cmd('OPER')
    print(r)
