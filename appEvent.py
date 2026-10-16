"""Global Qt signals used to decouple application widgets."""

from PyQt5.QtCore import QObject, pyqtSignal


class AppEvent(QObject):
    msg_from_header = pyqtSignal(str)
    msg_from_tabBar = pyqtSignal(str)
    msg_from_devwidget = pyqtSignal(str)
    msg_from_samplingwidget = pyqtSignal(str)
    tabbar_sw = pyqtSignal(int)
    devwidget_sw = pyqtSignal()
    samplingwidget_sw = pyqtSignal()
    samplingMsgwidget_sw = pyqtSignal()
    file_open = pyqtSignal()
    save_file = pyqtSignal(str)
    audio_control = pyqtSignal(str)
    audio_controls_state = pyqtSignal(bool, bool, str, str)
    meas_ch_change = pyqtSignal(str)
    collect_start = pyqtSignal(bool)
    plot_auto_range = pyqtSignal()

    def __init__(self, config=None, logger=None):
        super().__init__()
        self.config, self.logger = config, logger
        self.tab_list = ["音效调试", "波形", "频响", "哈曼对比"]

    def header_clicked(self, name):
        self.msg_from_header.emit(name)

    def header_menu_event(self, name, _is_checked=False):
        if name in self.tab_list:
            self.tabbar_sw.emit(self.tab_list.index(name))
        elif name == "音频控制":
            self.devwidget_sw.emit()
        elif name == "采样设置":
            self.samplingwidget_sw.emit()
        elif name == "数据信息":
            self.samplingMsgwidget_sw.emit()
        elif name == "打开...":
            self.file_open.emit()
        elif name == "保存原始...":
            self.save_file.emit("original")
        elif name == "保存处理后...":
            self.save_file.emit("processed")
        elif self.logger:
            self.logger.debug("未处理的菜单动作：%s", name)

    def audio_control_event(self, action):
        self.audio_control.emit(action)

    def info_clicked_event(self):
        if self.logger:
            self.logger.debug("info 按钮按下")

    def collect_stat_event(self, start):
        self.collect_start.emit(bool(start))

    def tabBar_close_event(self, tab_bar_name):
        self.msg_from_tabBar.emit(tab_bar_name)

    def devicewidget_close_event(self, win_title):
        self.msg_from_devwidget.emit(win_title)

    def samplingwidget_close_event(self, win_title):
        self.msg_from_samplingwidget.emit(win_title)

    def ch_change_event(self, ch):
        self.meas_ch_change.emit(ch)

    def auto_plot_range(self):
        self.plot_auto_range.emit()
