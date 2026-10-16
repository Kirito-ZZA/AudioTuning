import os
from PyQt5.QtCore import QSettings


basepath = os.path.dirname(__file__)
app_event = None


class Config(object):
    '''Config配置模块，读写.ini配置文件'''
    def __init__(self, filename):
        self.settings = QSettings(filename, QSettings.IniFormat)

    def write_key(self, section, key, val):
        '''
        配置文件写入键值
        Args:
            section (str) : 配置文件section
            key (str) : 配置文件待写入的键名
            val (str/list/int/...) : 配置文件键名对应的值
        returns:
            None : 无返回
        '''
        self.settings.setValue(
            f"{section}/{key}", val
        )

    def read_key(self, section, key, default_val=0, type=int):
        '''
        配置文件读取键值
        Args:
            section (str) : 配置文件section
            key (str) : 配置文件待读取的键名
            default_val (str/int/...) : 如未读到返回的默认值
            type (dtype) : 键值类型
        returns:
            result (str/list/int/...) : 相应键名对应的值
        '''
        return self.settings.value(
            f"{section}/{key}", default_val, type
        )
