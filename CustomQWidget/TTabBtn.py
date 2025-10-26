from PyQt5.QtWidgets import QPushButton, QLabel, QHBoxLayout, QSizePolicy
from PyQt5.QtCore import Qt, QCoreApplication, pyqtSignal


class TTabBtn(QPushButton):
    '''
    自定义仿Tab按钮(带关闭按钮)
    Args:
        text (str) : 按钮上显示文字
        objname (str) : 按钮名称设置
        checkable (bool) : 设置按钮是否可以被按下(默认可以按下,请勿修改该参数)
        closeable (bool) : 是否可关闭Tab(默认有关闭按钮)
        parent (obj) : 父子类继承关系
    returns:
        obj: 返回该控件实例
    '''
    close_event = pyqtSignal()  # closeEvent通知

    def __init__(
        self, text='Noise', objname='TTabBtn', checkable=True,
            closeable=True, parent=None):
        super(TTabBtn, self).__init__(parent)
        self.parent = parent
        self.setObjectName(objname)
        self.setCursor(Qt.PointingHandCursor)
        self.setText(QCoreApplication.translate('TTabBtn', text))
        if checkable:
            self.setCheckable(True)
        if closeable:
            self.closeBtn = QPushButton()
            self.closeBtn.setObjectName('CloseBtn')
            self.closeBtn.setText('×')
            self.closeBtn.setSizePolicy(
                QSizePolicy.Minimum, QSizePolicy.Minimum
            )
            self.closeBtn.clicked.connect(self.hide_tab)
            self._layout(mode=0)
        else:
            self._layout(mode=1)

    def _layout(self, mode=0):
        basic_layout = QHBoxLayout()
        _spacer = QLabel()
        _spacer.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        basic_layout.addWidget(_spacer)
        if mode == 0:
            basic_layout.addWidget(self.closeBtn)
        basic_layout.setContentsMargins(0, 0, 2, 0)
        self.setLayout(basic_layout)

    def show_tab(self):
        self.show()

    def hide_tab(self):
        self.hide()
        self.close_event.emit()
