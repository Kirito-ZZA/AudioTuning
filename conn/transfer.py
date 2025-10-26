"""
转换类
"""
import numpy as np
from utility.unit_converter import unit_converter

class ValueTransfer(object):

    def __init__(self):

        self.converter = {
            'U2I': self.U2I,
            'I2U': self.I2U,
            'U_SPILIT': self.U_SPILIT,
            'POLYNOMIAL': self.POLYNOMIAL,
            'MUL': self.MUL,
            'DIV': self.DIV
        }
    
    def MUL(self, val, k, unit):
        
        if isinstance(k, tuple):
            d = k[0]
        else:
            d = k
        return val * d, unit

    def DIV(self, val, k, unit):
        
        if isinstance(k, tuple):
            d = k[0]
        else:
            d = k
        return val / d, unit

    def U2I(self, val, k, unit):
        
        if isinstance(k, tuple):
            std_val, _ = unit_converter(val, unit)
            temp_I = std_val / k[0]
            ohm = k[0] * (1 - k[1]/1E6*(1-(temp_I/k[2])**2))
        else:
            ohm = k[0]
        return val / ohm, unit.replace("V", "A")

    def I2U(self, val, k, unit):
        
        if isinstance(k, tuple):
            std_val, _ = unit_converter(val, unit)
            temp_I = std_val / k[0]
            ohm = k[0] * (1 - k[1]/1E6*(1-(temp_I/k[2])**2))
        else:
            ohm = k[0]
        return val * ohm, unit.replace("A", "V")
    
    def U_SPILIT(self, val, p, unit):
        R1, R2 = p[0], p[1]
        return val * R2 / R1, unit

    def POLYNOMIAL(self, val, p, unit):
        
        z, freq = p[:-1], p[-1]
        p1 = np.poly1d(z[::-1])
        y = p1(freq)

        return val/y, unit

