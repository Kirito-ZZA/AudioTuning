'''
虚拟设备工厂
'''
from .protocol.fluke import Protocol8588


def protocol_factory(device_msg='Fluke 8558/8588', phy=None, protocol="", logger=None, **kwargc):
    '''
    工厂函数
    device_msg:    设备信息 (“<厂商> <型号>”)
    phy:            设备物理接口
    protocol:       设备通信协议
    '''
    manufacture, model = device_msg.strip().lower().split(' ')[0], \
        device_msg.strip().lower().split(' ')[-1]

    protocol_class = None
    if manufacture in ['fluke']:
        if model in ["8558", "8588", "8558/8588"]:
            protocol_class = Protocol8588

    if protocol_class:
        return protocol_class(model=model, phy=phy, protocol=protocol, logger=logger, **kwargc)

    return None
