"""Application header and menu actions."""

import os

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QActionGroup, QFrame, QHBoxLayout, QLabel, QMessageBox, QSizePolicy,
    QSpacerItem,
)

import config as settings
import theme
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
        self.shezhiBtn = TTitleBtn_combo(
            "设置", "shezhiBtn", actionlist=[], parent=self, logger=self.logger,
        )
        self._build_theme_menu()
        # 图标由按钮自绘（顶部居中），不再走 QSS background-image
        _pic = os.path.join(settings.basepath, "resource", "pic")
        for button, icon in (
            (self.wenjianBtn, "wenjian.png"), (self.shebeiBtn, "shebei.png"),
            (self.caiyangBtn, "caiyang.png"), (self.chuangkouBtn, "chuangkou.png"),
            (self.infoBtn, "info.png"), (self.shezhiBtn, "shezhi.png"),
        ):
            button.setIconFile(os.path.join(_pic, icon))
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
        # --- 隐藏控件：已从布局移除（不占位），实例与信号连接保留 ---
        # 以下 4 个按钮当前均为隐藏状态，是否彻底删除由用户决策；
        # 如需恢复显示，取消注释对应 addWidget 并移除 __init__ 中的 hide()。
        # layout.addWidget(self.shebeiBtn)      # 隐藏：音频
        # layout.addWidget(self.caiyangBtn)     # 隐藏：采样
        # layout.addWidget(splitter1)           # 隐藏按钮间的分隔线
        # layout.addWidget(self.chuangkouBtn)   # 隐藏：窗口
        # layout.addWidget(self.infoBtn)        # 隐藏：info
        # layout.addWidget(splitter2)           # 隐藏按钮后的分隔线
        layout.addItem(spacer)
        layout.addItem(right_spacer)
        layout.addWidget(self.shezhiBtn)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

    def _build_theme_menu(self):
        """设置按钮下拉菜单：主题切换（深色/浅色，单选）。"""
        theme_menu = self.shezhiBtn.menu.addMenu("主题切换")
        group = QActionGroup(self)
        group.setExclusive(True)
        self._theme_actions = {}
        for key, label in (("dark", "深色"), ("light", "浅色")):
            action = theme_menu.addAction(label)
            action.setCheckable(True)
            action.setChecked(theme.current_theme() == key)
            group.addAction(action)
            action.triggered.connect(
                lambda _checked, k=key, text=label: self._on_theme_selected(k, text)
            )
            self._theme_actions[key] = action

    def _on_theme_selected(self, name, label):
        """切换主题：写入配置、立即刷新 QSS；图表颜色需重启生效。"""
        self._theme_actions[name].setChecked(True)
        if theme.current_theme() == name:
            return
        theme.set_theme(name)
        if self.config is not None:
            self.config.write_key("ui", "theme", name)
        window = self.window()
        if window is not None:
            window.setStyleSheet(theme.render_qss())
        if self.logger:
            self.logger.info("界面主题切换为 %s", name)
        QMessageBox.information(
            self, "主题切换",
            "界面主题已切换为「%s」，图表颜色将在重启应用后完全生效。" % label,
        )
