from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDockWidget, QFrame, QGridLayout, QGroupBox, QPushButton, QVBoxLayout,
)

import config as settings


class DeviceWidget(QFrame):
    def __init__(self, config=None, parent=None, logger=None):
        super().__init__(parent)
        self.config, self.parent, self.logger = config, parent, logger
        self.app_eventCenter = settings.app_event
        self.audio_control_buttons = {}
        for action, text in (
            ("play_original", "播放原始"),
            ("play_processed", "播放处理后"),
            ("stop", "停止"),
            ("reset", "参数重置"),
            ("save_config", "保存算法配置"),
            ("reload_config", "重载算法配置"),
            ("fit_target", "目标曲线拟合"),
        ):
            button = QPushButton(text, self)
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(
                lambda _checked=False, name=action:
                    self.app_eventCenter.audio_control_event(name)
            )
            self.audio_control_buttons[action] = button

        self._layout()
        self.app_eventCenter.audio_controls_state.connect(self.update_audio_controls)
        self.update_audio_controls(False, False, "stopped", "")

    def _layout(self):
        layout = QVBoxLayout(self)
        control_group = QGroupBox("音频控制", self)
        control_layout = QGridLayout(control_group)
        for index, button in enumerate(self.audio_control_buttons.values()):
            row, column = divmod(index, 2)
            control_layout.addWidget(button, row, column)
        control_layout.setContentsMargins(8, 8, 8, 8)
        control_layout.setHorizontalSpacing(6)
        control_layout.setVerticalSpacing(6)
        layout.addWidget(control_group)
        layout.addStretch(1)
        layout.setContentsMargins(0, 0, 0, 0)

    def update_audio_controls(self, loaded, processed_ready, player_state, source):
        self.audio_control_buttons["play_original"].setEnabled(loaded)
        self.audio_control_buttons["play_processed"].setEnabled(processed_ready)
        self.audio_control_buttons["stop"].setEnabled(player_state != "stopped")
        self.audio_control_buttons["fit_target"].setEnabled(loaded)
        for action, label in (
            ("play_original", "original"), ("play_processed", "processed")
        ):
            button = self.audio_control_buttons[action]
            button.setText("播放原始" if label == "original" else "播放处理后")
            if source == label and player_state == "playing":
                button.setText("暂停")
            elif source == label and player_state == "paused":
                button.setText("继续原始" if label == "original" else "继续处理后")


class DeviceConnWidget(QDockWidget):
    def __init__(self, config=None, parent=None, logger=None):
        super().__init__(parent)
        self.setWindowTitle("音频控制")
        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WA_StyledBackground)
        self.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)
        self.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.config, self.parent, self.logger = config, parent, logger
        self.app_eventCenter = settings.app_event
        self.widget = DeviceWidget(self.config, self.parent, self.logger)
        self.setWidget(self.widget)
        self.app_eventCenter.devwidget_sw.connect(self.widget_sw)

    def widget_sw(self):
        if self.isHidden():
            self.show()
        else:
            self.hide()

    def closeEvent(self, event):
        self.app_eventCenter.devicewidget_close_event(self.windowTitle())
        super().closeEvent(event)
