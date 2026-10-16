import os

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QStackedWidget, QToolButton

import config as settings
from CustomQWidget.TTabBtn import TTabBtn


class TabBar(QFrame):
    tab_change = pyqtSignal(int)
    tab_close_event = pyqtSignal(str)

    def __init__(self, config=None, parent=None, logger=None):
        super().__init__(parent)
        self.config, self.parent, self.logger = config, parent, logger
        self.app_eventCenter = settings.app_event
        self.tabs_name = ["音效调试", "波形", "频响", "哈曼对比"]
        self.ini_tabs()
        self.displayWidget = QStackedWidget()
        for _ in self.tabs_name:
            self.displayWidget.addWidget(QFrame())

        self.autoBtn = QToolButton()
        self.autoBtn.setIcon(
            QIcon(os.path.join(settings.basepath, "resource/pic/autorange.png"))
        )
        self.autoBtn.setCursor(Qt.PointingHandCursor)
        self.autoBtn.setToolTip("绘图自适应")

        self._layout()
        self.tabs[0].setChecked(True)
        self.name = self.tabs[0]
        for button in self.tabs:
            button.clicked.connect(
                lambda: self.btn_state_change(name=self.sender())
            )
            button.close_event.connect(self.tab_close)
        self.app_eventCenter.tabbar_sw.connect(self.tab_sw)
        self.tab_close_event.connect(self.app_eventCenter.tabBar_close_event)
        self.autoBtn.clicked.connect(self.app_eventCenter.auto_plot_range)

    def ini_tabs(self):
        self.tabs = []
        for name in self.tabs_name:
            self.tabs.append(TTabBtn(name, "{}Tab".format(name), True, False, self))

    def _layout(self):
        layout = QHBoxLayout()
        for tab in self.tabs:
            layout.addWidget(tab)
        layout.addWidget(self.displayWidget)
        layout.addWidget(self.autoBtn)
        layout.setContentsMargins(0, 0, 4, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

    def btn_state_change(self, name):
        if self.name == name:
            name.setChecked(True)
        elif name.isChecked():
            self.name = name
            index = self.tabs.index(name)
            self.displayWidget.setCurrentIndex(index)
            self.tab_change.emit(index)
        for item in self.tabs:
            if item != self.name:
                item.setChecked(False)

    def tab_close(self):
        self.tab_close_event.emit(self.sender().text())
        if self.name == self.sender():
            for tab in self.tabs:
                if not tab.isHidden():
                    tab.click()
                    return
            self.name = None

    def tab_sw(self, index):
        if not 0 <= index < len(self.tabs):
            return
        if self.tabs[index].isHidden():
            self.tabs[index].show_tab()
            self.tabs[index].click()
        else:
            self.tabs[index].hide_tab()
