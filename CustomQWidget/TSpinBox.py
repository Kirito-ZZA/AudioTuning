from PyQt5.QtWidgets import QSpinBox, QDoubleSpinBox
from PyQt5.QtCore import QEvent


class TSpinBox(QSpinBox):
    def __init__(self):
        super(TSpinBox, self).__init__()
        self.old_value, self.new_value = None, None
        self.lineEdit().installEventFilter(self)  # 加载事件，用于点击事件判定

    def set_oldValue(self):
        self.old_value = self.value()

    def textFromValue(self, value):
        return str(format(value, ",")).replace(",", " ")

    def eventFilter(self, source, event):
        if event.type() == QEvent.MouseButtonRelease:
            self.old_value = self.value()
            length = len(self.lineEdit().text()) - len(self.suffix())
            self.lineEdit().setSelection(0, length)
        if event.type() == QEvent.Leave:
            self.new_value = self.value()
            self.lineEdit().deselect()
            if self.new_value != self.old_value:
                self.old_value = self.new_value
                self.editingFinished.emit()
        return super(TSpinBox, self).eventFilter(source, event)


class TDoubleSpinBox(QDoubleSpinBox):
    def __init__(self):
        super(TDoubleSpinBox, self).__init__()
        self.old_value, self.new_value = None, None
        self.lineEdit().installEventFilter(self)  # 加载事件，用于点击事件判定

    def set_oldValue(self):
        self.old_value = self.value()

    def textFromValue(self, value):
        return str(format(value, ",")).replace(",", " ")

    def eventFilter(self, source, event):
        if event.type() == QEvent.MouseButtonRelease:
            self.old_value = self.value()
            length = len(self.lineEdit().text()) - len(self.suffix())
            self.lineEdit().setSelection(0, length)
        if event.type() == QEvent.Leave:
            self.new_value = self.value()
            self.lineEdit().deselect()
            if self.new_value != self.old_value:
                self.old_value = self.new_value
                self.editingFinished.emit()
        return super(TDoubleSpinBox, self).eventFilter(source, event)
