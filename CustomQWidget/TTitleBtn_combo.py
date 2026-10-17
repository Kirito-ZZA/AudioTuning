from PyQt5.QtCore import Qt, QSize, pyqtSignal, QCoreApplication
from PyQt5.QtGui import QPalette, QPixmap
from PyQt5.QtWidgets import (
    QPushButton, QMenu, QStyle, QStyleOptionButton, QStylePainter,
)


class TTitleBtn_combo(QPushButton):
    '''
    自定义导航栏按钮
    Args:
        text (str) : 按钮上显示文字
        objname (str) : 按钮名称设置
        actionlist (list) : Action列表
            [('示例', False), ..., ('separator')] tuple前一项为显示文字, 后一项为是否可选中
        parent (obj) : 父子类继承关系
        logger (obj) : 系统日志
    returns:
        obj: 返回该控件实例
    '''
    menu_clicked = pyqtSignal(str, bool)

    def __init__(
        self, text='', objname='titleBtn_combo',
        actionlist=[], parent=None, logger=None
    ):
        super(TTitleBtn_combo, self).__init__(parent)
        self.parent, self.logger = parent, logger
        self.setObjectName(objname)
        self.setCursor(Qt.PointingHandCursor)
        self.setText(QCoreApplication.translate('TTitleBtn', text))

        self.menu = QMenu(self)
        for action in actionlist:
            if action[0] != 'separator':
                _action = self.menu.addAction(action[0])
                _action.setCheckable(action[-1])
                if _action.isCheckable():
                    _action.setChecked(True)
                _action.triggered.connect(
                    lambda: self.menu_func(self.sender().text())
                )
            else:
                self.menu.addSeparator()

        self.setContextMenuPolicy(Qt.DefaultContextMenu)
        self.released.connect(self.show_menu)
        self._icon_pixmap = QPixmap()
        self._icon_top = 8
        self._text_bottom_margin = 5

    def setIconFile(self, path, top=8):
        '''设置按钮图标文件，绘制在按钮顶部居中位置。'''
        self._icon_pixmap = QPixmap(path)
        self._icon_top = top
        self.update()

    def paintEvent(self, event):
        # 背景、hover、checked 等状态交给样式表风格绘制；
        # 图标顶部居中、文字底部居中由代码绘制，位置与 Qt 版本无关。
        painter = QStylePainter(self)
        option = QStyleOptionButton()
        self.initStyleOption(option)
        text = option.text
        option.text = ""
        painter.drawControl(QStyle.CE_PushButton, option)
        if not self._icon_pixmap.isNull():
            x = int((self.width() - self._icon_pixmap.width()) / 2)
            painter.drawPixmap(x, self._icon_top, self._icon_pixmap)
        if text:
            painter.setPen(self.palette().color(QPalette.ButtonText))
            painter.drawText(
                self.rect().adjusted(0, 0, 0, -self._text_bottom_margin),
                Qt.AlignHCenter | Qt.AlignBottom, text,
            )
        painter.end()

    def show_menu(self):
        _bl = self.mapToGlobal(self.rect().bottomLeft())
        self.menu.exec_(_bl)

    def menu_func(self, name):
        '''菜单按钮点击槽函数'''
        self.menu_clicked.emit(name, self.sender().isChecked())

    def action_setChecked(self, name):
        '''菜单按钮勾选与否槽函数'''
        for action in self.menu.actions():
            if action.text() == name:
                action.setChecked(False)
