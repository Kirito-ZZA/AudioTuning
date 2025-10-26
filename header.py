"""
Header widget for App
"""
import os, sys
from PyQt5.QtGui import QFont, QIcon, QPixmap
from PyQt5.QtCore import Qt, QSize, QCoreApplication, QTranslator, pyqtSignal, \
    QTimer
from PyQt5.QtWidgets import QFrame, QWidget, QHBoxLayout, QLabel, \
    QVBoxLayout, QSpacerItem, QSizePolicy, QPushButton, QProgressBar

from CustomQWidget.TTitleBtn import TTitleBtn
from CustomQWidget.TTitleBtn_combo import TTitleBtn_combo

import config as settings


class Header(QFrame):
    msg_from_header = pyqtSignal(str)
    start_collect = pyqtSignal(bool)

    def __init__(self, parent=None, size=None, config=None, logger=None):
        super().__init__()
        self.parent, self.config, self.logger = parent, config, logger
        self.setObjectName("Header_title")

        self.app_eventCenter = settings.app_event

        if size:
            self.resize(size)

        self.wenjianBtn = TTitleBtn_combo(
            '文件', 'wenjianBtn', actionlist=[
                    ("打开...", False), ("保存", False), ("另存为...", False)
                ],
            parent=self, logger=self.logger
        )
        self.shebeiBtn = TTitleBtn_combo(
            '设备', 'shebeiBtn', actionlist=[("通信接口", True)], parent=self,
            logger=self.logger
        )
        self.caiyangBtn = TTitleBtn_combo(
            '采样', 'caiyangBtn', actionlist=[
                    ("采样设置", True), ('separator', False), ("数据信息", True)
                ],
            parent=self, logger=self.logger
        )
        self.chuangkouBtn = TTitleBtn_combo(
            '窗口', 'chuangkouBtn', actionlist=[
                    ("时频噪声", True), ("噪声分布", True),
                    ("噪声密度", True), ("噪声——f", True)
                ],
            parent=self, logger=self.logger
        )
        self.infoBtn = TTitleBtn(
            'info', 'infoBtn', checkable=False, parent=self
        )

        self.btns = [
            self.wenjianBtn, self.shebeiBtn, self.caiyangBtn,
            self.chuangkouBtn, self.infoBtn
            ]

        # self.qidong_btn = QPushButton("启动")
        # self.qidong_btn.setFixedSize(90, 40)
        # self.qidong_btn.setObjectName("StartStopBtn")
        # self.qidong_btn.setCursor(Qt.PointingHandCursor)
        # self.qidong_btn.setProperty('started', False)
        # icon_path = os.path.join(settings.basepath, "resource/pic/qidong.png")
        # self.qidong_btn.setIcon(QIcon(QPixmap(icon_path)))
        # self.qidong_btn.clicked.connect(self.start_sw)

        # self.TProgressBar_title = QProgressBar(self)
        # self.TProgressBar_title.setObjectName('ProgressBar')

        self._layout()

        # self.timer = QTimer()
        # self.timer.timeout.connect(self.update_progress)

        for btn in self.btns[1:-1]:
            btn.hide()
        self.infoBtn.hide()     # 隐藏info按钮,有需要再显示

        for btn in self.btns[:-1]:
            btn.menu_clicked.connect(self.app_eventCenter.header_menu_event)
        self.infoBtn.clicked.connect(self.app_eventCenter.info_clicked_event)
        self.start_collect.connect(self.app_eventCenter.collect_stat_event)
        self.app_eventCenter.msg_from_tabBar.connect(
            self.chuangkouBtn.action_setChecked
        )
        self.app_eventCenter.msg_from_devwidget.connect(
            self.shebeiBtn.action_setChecked
        )
        self.app_eventCenter.msg_from_samplingwidget.connect(
            self.caiyangBtn.action_setChecked
        )

    # def update_value(self, value):
    #     '''进度条刷新'''
    #     value_v = float(value)
    #     self.TProgressBar_title.setValue(value_v)
    #     if value_v >= 100:
    #         self.timer.stop()

    # def update_progress(self):
    #     current_value = self.TProgressBar_title.value()
    #     if current_value < 90:
    #         value = current_value + 5
    #     elif current_value >= 90 and current_value < 99:
    #         value = current_value + 1
    #     else:
    #         value = current_value
    #     self.update_value(value)

    # def reset_progressbar(self):
    #     '''进度条归零'''
    #     self.TProgressBar_title.setValue(0)

    # def start_sw(self):
    #     if self.qidong_btn.property('started'):  # 停止
    #         icon = os.path.join(settings.basepath, "resource/pic/qidong.png")
    #         self.qidong_btn.setText("启动")
    #         self.qidong_btn.setProperty('started', False)
    #     else:
    #         icon = os.path.join(settings.basepath, "resource/pic/tingzhi.png")
    #         self.qidong_btn.setText("停止")
    #         self.qidong_btn.setProperty('started', True)
    #     self.qidong_btn.setIcon(QIcon(QPixmap(icon)))
    #     self.qidong_btn.style().unpolish(self.qidong_btn)  # 弃用原样式
    #     self.qidong_btn.style().polish(self.qidong_btn)  # 采用新样式
    #     self.start_collect.emit(self.qidong_btn.property('started'))

    # def reset_qidongBtn(self):
    #     self.qidong_btn.setProperty('started', False)
    #     icon = os.path.join(settings.basepath, "resource/pic/qidong.png")
    #     self.qidong_btn.setText("启动")
    #     self.qidong_btn.setIcon(QIcon(QPixmap(icon)))
    #     self.qidong_btn.style().unpolish(self.qidong_btn)  # 弃用原样式
    #     self.qidong_btn.style().polish(self.qidong_btn)  # 采用新样式

    def _layout(self):
        layout_basic = QHBoxLayout()

        splitter1 = QLabel()
        splitter1.setObjectName('HeaderSplitter1')
        splitter2 = QLabel()
        splitter2.setObjectName('HeaderSplitter2')

        m_spacer = QSpacerItem(
            40, 68, QSizePolicy.Expanding, QSizePolicy.Minimum)  # w, h

        m_spacer_2 = QSpacerItem(
            30, 68, QSizePolicy.Expanding, QSizePolicy.Minimum)  # w, h

        layout_basic.addWidget(self.wenjianBtn)
        layout_basic.addWidget(self.shebeiBtn)
        layout_basic.addWidget(self.caiyangBtn)
        layout_basic.addWidget(splitter1)
        layout_basic.addWidget(self.chuangkouBtn)
        layout_basic.addWidget(self.infoBtn)
        layout_basic.addWidget(splitter2)

        layout_basic.addItem(m_spacer)

        # layout_basic.addWidget(self.qidong_btn)

        layout_basic.addItem(m_spacer_2)

        # layout_basic.addWidget(self.TProgressBar_title)

        layout_basic.setContentsMargins(0, 0, 0, 0)
        layout_basic.setSpacing(0)  # 控件间距

        self.setLayout(layout_basic)


if __name__ == '__main__':
    import os, sys
    from PyQt5.QtWidgets import QApplication

    base_path = os.path.dirname(__file__)
    qss_path = os.path.join(base_path, "resource/qss/app_bt.qss")
    sys.path.append(base_path)

    app = QApplication(sys.argv)

    widget = Header(QSize(1024, 68))
    with open(qss_path, 'r') as f:
        widget.setStyleSheet(f.read())

    widget.show()
    app.exec_()
