'''
全局的单例类AppEvent，公共的信号放这里，然后窗体A对应信号绑定到AppEvent，
窗体D绑定AppEvent的信号到对应的槽函数即可，干净清爽整洁
'''
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot


class AppEvent(QObject):

    msg_from_tabBar = pyqtSignal(str)
    msg_from_devwidget = pyqtSignal(str)
    msg_from_samplingwidget = pyqtSignal(str)
    tabbar_sw = pyqtSignal(int)
    devwidget_sw = pyqtSignal()
    samplingwidget_sw = pyqtSignal()
    samplingMsgwidget_sw = pyqtSignal()
    file_open = pyqtSignal()
    save_file = pyqtSignal(int)
    dev_init_connected = pyqtSignal()
    meas_ch_change = pyqtSignal(str)
    collect_start = pyqtSignal(bool)
    plot_auto_range = pyqtSignal()

    def __init__(self, config=None, logger=None):
        super(AppEvent, self).__init__()
        self.config, self.logger = config, logger

        self.tab_list = ['噪声', '噪声分布', '噪声谱密度', '带宽噪声']

    def header_clicked(self, name):
        '''
        顶部导航栏点击事件槽函数
        Args:
            name (str) : 点击按钮名称
        returns:
            None
        '''
        self.msg_from_header.emit(name)

    def header_menu_event(self, name, isChecked):
        '''导航栏下拉菜单按钮点击槽函数'''
        if name in self.tab_list:  # tabBar事件
            self.tabbar_sw.emit(self.tab_list.index(name))
        elif name == '通信接口':
            self.devwidget_sw.emit()
        elif name == '采样设置':
            self.samplingwidget_sw.emit()
        elif name == '数据信息':
            self.samplingMsgwidget_sw.emit()
        elif name == '打开...':
            self.file_open.emit()
        elif name == '保存':
            self.save_file.emit(0)
        elif name == '另存为...':
            self.save_file.emit(1)
        else:
            print(name, isChecked)

    def info_clicked_event(self):
        print('info 按钮按下')

    def device_connected_event(self):
        '''设备连接槽函数'''
        self.dev_init_connected.emit()

    def collect_stat_event(self, _start):
        '''启动/停止按钮点击信号槽函数'''
        if _start:  # 启动
            self.collect_start.emit(True)
        else:       # 停止
            self.collect_start.emit(False)

    def tabBar_close_event(self, tab_bar_name):
        '''tabBar关闭按钮点击槽函数'''
        self.msg_from_tabBar.emit(tab_bar_name)

    def devicewidget_close_event(self, win_title):
        '''设备连接页面关闭信号槽函数'''
        self.msg_from_devwidget.emit(win_title)

    def samplingwidget_close_event(self, win_title):
        '''采样设置页面/数据信息页面关闭信号槽函数'''
        self.msg_from_samplingwidget.emit(win_title)

    def ch_change_event(self, ch):
        '''采样设置通道变换槽函数'''
        self.meas_ch_change.emit(ch)

    def auto_plot_range(self):
        '''绘图画布自适应槽函数'''
        self.plot_auto_range.emit()
