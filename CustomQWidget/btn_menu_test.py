from PyQt5.QtWidgets import QPushButton, QLabel, QFrame, QMenu, QAction, QHBoxLayout, QSizePolicy
from PyQt5.QtCore import Qt, QEvent, QCoreApplication
from PyQt5.QtGui import QCursor


class TitleBtn_Menu(QPushButton):
    def __init__(
        self, text='文件', objname='TitleBtn_Menu', checkable=False, menu=True
    ):
        super(TitleBtn_Menu, self).__init__()
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setText(text)
        self.setObjectName(objname)
        self.setCheckable(checkable)

        self.setContextMenuPolicy(Qt.DefaultContextMenu)
        self.released.connect(self.show_menu)

        self.menu = QMenu(self)
        # self.menu.setAttribute(Qt.WA_StyledBackground, True)
        # self.menu.setWindowFlags(Qt.Popup|Qt.FramelessWindowHint|Qt.NoDropShadowWindowHint)
        # self.menu.setAttribute(Qt.WA_TranslucentBackground)
        self.menu.setObjectName('BtnMenu')
        open_action = self.menu.addAction(u"打开")
        save_action = self.menu.addAction(u"保存")
        open_action.triggered.connect(lambda: self.menu_func(self.sender().text()))
        save_action.triggered.connect(lambda: self.menu_func(self.sender().text()))

    def show_menu(self):
        _bl = self.mapToGlobal(self.rect().bottomLeft())
        self.menu.exec_(_bl)

    def menu_func(self, name):
        print(name)


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



class testWin(QFrame):
    def __init__(self):
        super(testWin, self).__init__()

        self._layout()

    def _layout(self):
        basic_layout = QHBoxLayout()

        btn = TitleBtn_Menu()
        self.tab_btn = TTabBtn()
        basic_layout.addWidget(btn)
        basic_layout.addWidget(self.tab_btn)
        btn.clicked.connect(self.tab_btn.show_tab)

        self.setLayout(basic_layout)

if __name__ == '__main__':
    import os, sys
    from PyQt5.QtWidgets import QSplashScreen, QApplication
    app = QApplication(sys.argv)

    viewer = testWin()
    with open('./CustomQWidget/test.qss', 'r') as f:
        viewer.setStyleSheet(f.read())
        f.close()
    viewer.show()
    sys.exit(app.exec_())

