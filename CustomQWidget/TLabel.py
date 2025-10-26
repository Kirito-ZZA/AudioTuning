from PyQt5.QtWidgets import QLabel
from utility.unit_converter import unit_split_raw
from .formater import value_format


class TLabel(QLabel):
    '''
    自定义数值显示label(千分位空格分隔)
    Args:
        val (float/int): 初始值
        unit (str): 单位
        parent (obj): 父类关系
        logger (obj): 日志
    '''
    def __init__(self, val=0000.000, unit='V', parent=None, logger=None):
        super(TLabel, self).__init__(parent)
        self.parent, self.logger = parent, logger
        self.val, self.unit = val, unit
        self.set_val(val, unit)

    def set_val(self, value, unit, bits=8):
        '''当为数值时, 设置数值'''
        self.val, self.unit = value, unit
        v, u = value_format(value, unit, bits)
        text = f'{v} {u}'
        self.setText(text)

    def set_sval(self, value, bits=8):
        '''当为字符串时, 设置数值'''
        self.val, self.unit = unit_split_raw(value)
        v, u = value_format(self.val, self.unit, bits)
        text = f'{v} {u}'
        self.setText(text)

    def get_val(self):
        '''
        获取当前值(返回储存的原始值)
        return:
            value (tuple) (value, unit)
        '''
        return self.val, self.unit
