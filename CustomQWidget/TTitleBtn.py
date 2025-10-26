from PyQt5.QtCore import Qt, QSize, QCoreApplication
from PyQt5.QtWidgets import QPushButton


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
