from PyQt5.QtCore import Qt, QSize, QCoreApplication
from PyQt5.QtGui import QPalette, QPixmap
from PyQt5.QtWidgets import (
    QPushButton, QStyle, QStyleOptionButton, QStylePainter,
)


class TTitleBtn(QPushButton):
    '''
    自定义导航栏按钮
    Args:
        text (str) : 按钮上显示文字
        objname (str) : 按钮名称设置
        size (tuple) : 设置按钮为固定大小(w, h), 可在qss覆盖
        checkable (bool) : 设置按钮是否可以被按下
        parent (obj) : 父子类继承关系
    returns:
        obj: 返回该控件实例
    '''
    def __init__(
        self, text='', objname='titleBtn', size=(100, 68),
            checkable=False, parent=None):
        super(TTitleBtn, self).__init__(parent)
        self.parent = parent
        self.setObjectName(objname)
        self.setCursor(Qt.PointingHandCursor)
        self.setText(QCoreApplication.translate('TTitleBtn', text))
        if size:
            self.setFixedSize(size[0], size[1])
        if checkable:
            self.setCheckable(True)
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
