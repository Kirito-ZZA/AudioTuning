import os
from PyQt5.QtWidgets import QFrame, QStackedWidget, QHBoxLayout, QSizePolicy, \
    QToolButton
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon
from CustomQWidget.TTabBtn import TTabBtn
from CustomQWidget.TLabel import TLabel
import config as settings


class TabBar(QFrame):
    tab_change = pyqtSignal(int)  # 切页
    tab_close_event = pyqtSignal(str)  # 关闭事件(联动菜单栏状态变动)

    def __init__(self, config=None, parent=None, logger=None):
        super(TabBar, self).__init__(parent)
        self.config, self.parent, self.logger = config, parent, logger
        self.app_eventCenter = settings.app_event
        self.tabs_name = ['时频噪声', '噪声分布', '噪声密度', '噪声-f']
        self.ini_tabs()
        self.analysis_bits = self.config.read_key(
            'analysis', 'bits', 8, int
        )
        # 实时数值显示窗口
        self.displayWidget = QStackedWidget()
        #TODO: 以下widget待完善
        self.displayWidget.addWidget(QFrame())
        self.displayWidget.addWidget(QFrame())
        self.displayWidget.addWidget(QFrame())
        blank_widget = QFrame()  # index=3
        self.displayWidget.addWidget(blank_widget)
        blank_widget = QFrame()  # index=4
        self.displayWidget.addWidget(blank_widget)

        self.autoBtn = QToolButton()
        self.autoBtn.setIcon(
            QIcon(os.path.join(settings.basepath, 'resource/pic/autorange.png'))
        )
        self.autoBtn.setCursor(Qt.PointingHandCursor)
        self.autoBtn.setToolTip('绘图自适应')

        self._layout()
        self.tabs[0].setChecked(True)
        self.name = self.tabs[0]
        for btn in self.tabs:
            btn.clicked.connect(
                lambda: self.btn_state_change(name=self.sender()))
            btn.close_event.connect(self.tab_close)
        self.app_eventCenter.tabbar_sw.connect(self.tab_sw)
        self.tab_close_event.connect(self.app_eventCenter.tabBar_close_event)
        self.autoBtn.clicked.connect(self.app_eventCenter.auto_plot_range)

    def ini_tabs(self):
        self.tabs = list()
        for name in self.tabs_name:
            tab = TTabBtn(
                name, f'{name}Tab', True, False, self
            )
            self.tabs.append(tab)

    def update_analysis_value(self, pp, rms, _std, e_n):
        values = dict()
        values['pp'], values['rms'], values['std'], values['e_n'] = pp, \
            rms, _std, e_n
        self.noiseWidget.update_value(values)
        self.distributeWidget.update_value(values)
        self.noiseSpectrumWidget.update_value(values)

    def _layout(self):
        basic_layout = QHBoxLayout()
        for tab in self.tabs:
            basic_layout.addWidget(tab)
        basic_layout.addWidget(self.displayWidget)
        basic_layout.addWidget(self.autoBtn)
        basic_layout.setContentsMargins(0, 0, 4, 0)
        basic_layout.setSpacing(0)
        self.setLayout(basic_layout)

    def btn_state_change(self, name):
        '''按钮点击槽函数'''
        if self.name == name:
            name.setChecked(True)
            for item in self.tabs:
                if item != name:
                    item.setChecked(False)
        else:
            if name.isChecked():
                self.name = name
                for item in self.tabs:
                    if item != name:
                        item.setChecked(False)
                _index = self.tabs.index(name)
                self.displayWidget.setCurrentIndex(_index)
                self.tab_change.emit(_index)

    def tab_close(self):
        '''tab按钮关闭点击槽函数'''
        self.tab_close_event.emit(self.sender().text())
        if self.name == self.sender():
            for tab in self.tabs:
                if not tab.isHidden():
                    tab.click()
                    return
            else:  # 当没有可打开的标签页时，打开空白页
                self.displayWidget.setCurrentIndex(4)
                self.name.setChecked(False)
                self.name = None
                self.tab_change.emit(4)

    def tab_sw(self, _index):
        '''
        tab按钮关闭/恢复槽函数
        Args:
            _index (int): tab在tabs中的index
        '''
        if self.name:
            if not self.tabs[_index].isHidden():
                self.tabs[_index].hide_tab()
            else:
                self.tabs[_index].show_tab()
        else:
            if not self.tabs[_index].isHidden():
                self.tabs[_index].hide_tab()
            else:
                self.tabs[_index].show_tab()
                self.tabs[_index].click()
