"""Application header and menu actions."""

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QSpacerItem

import config as settings
from CustomQWidget.TTitleBtn import TTitleBtn
from CustomQWidget.TTitleBtn_combo import TTitleBtn_combo


class Header(QFrame):
    msg_from_header = pyqtSignal(str)
    start_collect = pyqtSignal(bool)

    def __init__(self, parent=None, size=None, config=None, logger=None):
        super().__init__(parent)
        self.parent, self.config, self.logger = parent, config, logger
        self.setObjectName("Header_title")
        self.app_eventCenter = settings.app_event
        if size:
            self.resize(size)

        self.wenjianBtn = TTitleBtn_combo(
            "文件", "wenjianBtn",
            actionlist=[
                ("打开...", False), ("保存原始...", False), ("保存处理后...", False),
            ],
            parent=self, logger=self.logger,
        )
        self.shebeiBtn = TTitleBtn_combo(
            "音频", "shebeiBtn", actionlist=[("音频控制", True)],
            parent=self, logger=self.logger,
        )
        self.caiyangBtn = TTitleBtn_combo(
            "采样", "caiyangBtn",
            actionlist=[("采样设置", True), ("separator", False), ("数据信息", True)],
            parent=self, logger=self.logger,
        )
        self.chuangkouBtn = TTitleBtn_combo(
            "窗口", "chuangkouBtn",
            actionlist=[
                ("音效调试", True), ("波形", True), ("频响", True), ("哈曼对比", True),
            ],
            parent=self, logger=self.logger,
        )
        self.infoBtn = TTitleBtn("info", "infoBtn", checkable=False, parent=self)
        self.btns = [
            self.wenjianBtn, self.shebeiBtn, self.caiyangBtn,
            self.chuangkouBtn, self.infoBtn,
        ]
        self._layout()

        for button in self.btns[1:-1]:
            button.hide()
        self.infoBtn.hide()
        for button in self.btns[:-1]:
            button.menu_clicked.connect(self.app_eventCenter.header_menu_event)
        self.infoBtn.clicked.connect(self.app_eventCenter.info_clicked_event)
        self.start_collect.connect(self.app_eventCenter.collect_stat_event)
        self.app_eventCenter.msg_from_tabBar.connect(self.chuangkouBtn.action_setChecked)
        self.app_eventCenter.msg_from_devwidget.connect(self.shebeiBtn.action_setChecked)
        self.app_eventCenter.msg_from_samplingwidget.connect(
            self.caiyangBtn.action_setChecked
        )

    def _layout(self):
        layout = QHBoxLayout()
        splitter1 = QLabel()
        splitter1.setObjectName("HeaderSplitter1")
        splitter2 = QLabel()
        splitter2.setObjectName("HeaderSplitter2")
        spacer = QSpacerItem(40, 68, QSizePolicy.Expanding, QSizePolicy.Minimum)
        right_spacer = QSpacerItem(30, 68, QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout.addWidget(self.wenjianBtn)
        layout.addWidget(self.shebeiBtn)
        layout.addWidget(self.caiyangBtn)
        layout.addWidget(splitter1)
        layout.addWidget(self.chuangkouBtn)
        layout.addWidget(self.infoBtn)
        layout.addWidget(splitter2)
        layout.addItem(spacer)
        layout.addItem(right_spacer)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)
