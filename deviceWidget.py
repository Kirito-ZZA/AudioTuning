import os, json
from PyQt5.QtWidgets import QDockWidget, QFrame, QFormLayout, QComboBox, \
    QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QSizePolicy, QLayout, \
    QLineEdit, QMessageBox
from PyQt5.QtCore import Qt, QSortFilterProxyModel, QRegExp, pyqtSignal
from PyQt5.QtGui import QStandardItemModel, QStandardItem

import pyvisa
from serial.tools import list_ports

import config as settings
from conn.factory import protocol_factory

# 连接类型对应参数映射表
# 参数名 默认值 控件类型
_MAP = {
    "TCP": [
        ("IP", "127.0.0.1", "line_edit"),
        ("Port", "8000", "line_edit")
    ],
    "RS232": [
        ("COM", [], "combo_box"),
        ("Baurate", "115200", "line_edit"),
        ("Bits", "8", "line_edit"),
        ("StopBit", "1", "line_edit"),
        ("Parity", "None", "line_edit"),
        ("FlowControl", "None", "line_edit")
    ],
    "GPIB": [
        ("GPIB", [], "combo_box")
    ]
}


class SortFilterProxyModel(QSortFilterProxyModel):

    def __init__(self, *args, **kwargs):
        super(SortFilterProxyModel, self).__init__(*args, **kwargs)
        self.setFilterRole(Qt.ToolTipRole)  # 根据Qt.ToolTipRole角色过滤
        self._model = QStandardItemModel(self)
        self.setSourceModel(self._model)

    def appendRow(self, item):
        self._model.appendRow(item)

    def setFilter(self, _):
        # 过滤
        # self.sender()#发送者
        # 获取上一个下拉框中的item_code
        item_code = self.sender().currentData(Qt.ToolTipRole)
        if not item_code:
            return
        if item_code.endswith("0000"):  # 过滤通讯方式
            self.setFilterRegExp(QRegExp(item_code[:-4] + "\d\d00"))
        elif item_code.endswith("00"):  # 过滤通讯方式更下一级(如有)
            self.setFilterRegExp(QRegExp(item_code[:-2] + "\d\d"))


class DeviceWidget(QFrame):
    device_connected = pyqtSignal()

    def __init__(self, config=None, parent=None, logger=None):
        super(DeviceWidget, self).__init__(parent)
        self.config, self.parent, self.logger = config, parent, logger
        self.device = None
        self.dev_label = QLabel()
        self.dev_label.setObjectName("DevLabel")
        self.device_manufactorLabel = QLabel()
        self.device_manufactorLabel.setText('设备选择')
        self.device_manufactor = QComboBox()
        self.device_conntypeLabel = QLabel()
        self.device_conntypeLabel.setText('连接方式')
        self.device_conntype = QComboBox()
        self.connectBtn = QPushButton()
        self.connectBtn.setText('连接')
        self.connectBtn.setCursor(Qt.PointingHandCursor)
        self.disconnectBtn = QPushButton()
        self.disconnectBtn.setText('断开')
        self.disconnectBtn.setCursor(Qt.PointingHandCursor)
        self.disconnectBtn.setEnabled(False)

        self._layout()
        self.initModel()
        self.initSignal()
        self.initData()

        self.connectBtn.clicked.connect(self.connect_func)
        self.disconnectBtn.clicked.connect(self.disconnect_func)

    def initModel(self):
        # 初始化模型
        self.manufactor_model = SortFilterProxyModel(self)
        self.conntype_model = SortFilterProxyModel(self)
        # 设置模型
        self.device_manufactor.setModel(self.manufactor_model)
        self.device_conntype.setModel(self.conntype_model)

    def initSignal(self):
        # 初始化信号槽
        self.device_manufactor.currentIndexChanged.connect(
            self.conntype_model.setFilter)
        self.device_conntype.currentTextChanged.connect(
            self.connect_type_changed
        )

    def initData(self):
        # 初始化数据
        data_path = os.path.join(settings.basepath, 'resource/device.json')
        with open(data_path) as f:
            content = f.read()
        datas = json.loads(content)
        f.close()
        # 开始解析数据
        for data in datas:
            item_code = data.get("item_code")  # 编码
            item_name = data.get("item_name")  # 名字
            item = QStandardItem(item_name)
            item.setData(item_code, Qt.ToolTipRole)
            if item_code.endswith("0000"):  # 4个0结尾的是设备制造商
                self.manufactor_model.appendRow(item)
            elif item_code.endswith("000"):  # 3个0结尾的是连接方式
                self.conntype_model.appendRow(item)

    def _layout(self):
        basic_layout = QVBoxLayout()
        _spacer = QLabel()
        _spacer.setSizePolicy(
            QSizePolicy.Minimum, QSizePolicy.Expanding
        )
        button_layout = QHBoxLayout()
        self.form_layout = QFormLayout()
        self.form_layout.addRow(
            self.device_manufactorLabel, self.device_manufactor
        )  # 第一行
        self.form_layout.addRow(
            self.device_conntypeLabel, self.device_conntype
        )  # 第二行
        self.form_layout.setLabelAlignment(Qt.AlignRight)  # label右对齐
        self.form_layout.setContentsMargins(8, 8, 8, 8)
        self.form_layout.setHorizontalSpacing(4)
        self.form_layout.setVerticalSpacing(6)
        self.form_layout.setSizeConstraint(QLayout.SetFixedSize)  # 保证layout跟随内部控件大小
        botton_spacer = QLabel()
        botton_spacer.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Minimum
        )
        button_layout.addWidget(botton_spacer)
        button_layout.addWidget(self.connectBtn)
        button_layout.addWidget(self.disconnectBtn)
        button_layout.setContentsMargins(0, 0, 8, 8)
        button_layout.setSpacing(4)
        basic_layout.addLayout(self.form_layout)
        basic_layout.addWidget(_spacer)
        basic_layout.addLayout(button_layout)
        basic_layout.setContentsMargins(0, 0, 0, 0)
        basic_layout.setSpacing(0)
        self.setLayout(basic_layout)

    def connect_type_changed(self, _type):
        '''设备连接方式变化槽函数'''
        row_count = self.form_layout.rowCount()
        if _type:
            if row_count > 2:
                for _ in range(row_count)[2:]:
                    self.form_layout.removeRow(2)
            for param_item in _MAP[_type]:
                label = QLabel()
                label.setText(param_item[0])
                if param_item[-1] == 'line_edit':
                    _edit = QLineEdit()
                    _edit.setText(param_item[1])
                elif param_item[-1] == 'combo_box':
                    if _type == 'GPIB':
                        rm = pyvisa.ResourceManager()
                        _l = rm.list_resources()
                    elif _type == 'RS232':
                        _l = [item[0] for item in list(list_ports.comports())]
                    _edit = QComboBox()
                    _edit.addItems(_l)
                self.form_layout.addRow(label, _edit)

    # def update_devices(self, devices):
    #     '''动态更新设备服务items'''
    #     if self.connectBtn.isEnabled():
    #         for new_item in devices:
    #             if new_item not in self.device_list:
    #                 self.device_list.append(new_item)
    #                 self.deviceBox.addItem(new_item)
    #         for index, old_item in enumerate(self.device_list):
    #             count = self.device_list.count(old_item)
    #             if count > 1:  # 除重, 基本可以不用
    #                 self.deviceBox.removeItem(index)
    #                 self.device_list.remove(old_item)
    #             if old_item not in devices:
    #                 self.deviceBox.removeItem(index)
    #                 self.device_list.remove(old_item)

    def get_connect_param(self):
        '''
        数据获取
        returns:
            return_dict (dict) : 内容字典,
                键为标签文字, 值为输入框中输入内容
        '''
        return_dict = dict()
        try:
            count = self.form_layout.rowCount()
            for i in range(count):
                label = self.form_layout.itemAt(i, QFormLayout.LabelRole)  # 标签
                _edit = self.form_layout.itemAt(i, QFormLayout.FieldRole)  # 内容
                key = label.widget().text()
                if isinstance(_edit.widget(), QLineEdit):
                    val = _edit.widget().text()
                elif isinstance(_edit.widget(), QComboBox):
                    val = _edit.widget().currentText()
                else:
                    val = _edit.widget().value()
                return_dict[key] = val
                # Fluke 5500 GPIB
            return return_dict
        except Exception as e:
            if self.logger:
                self.logger.exception(e)
            return return_dict

    def param_edited_enable(self, enable):
        '''设备连接参数是否允许编辑'''
        count = self.form_layout.rowCount()
        for i in range(count):
            _edit = self.form_layout.itemAt(i, QFormLayout.FieldRole)  # 内容
            _edit.widget().setEnabled(enable)

    def connect_func(self):
        '''连接按钮点击槽函数'''
        try:
            param_dict = self.get_connect_param()
            self.logger.debug(param_dict)
            dev_msg = param_dict.get('设备选择', None)
            typ = param_dict.get('连接方式', None)
            self.device = protocol_factory(
                dev_msg, typ, logger=self.logger, **param_dict
            )
            if self.device is not None:
                self.logger.debug(self.device)
                self.param_edited_enable(False)
                self.connectBtn.setEnabled(False)
                self.disconnectBtn.setEnabled(True)
                settings.device = self.device
                self.device_connected.emit()
            else:
                QMessageBox.warning(self, '警告', '未找到设备')
        except Exception as e:
            self.logger.exception(e)

    def disconnect_func(self):
        '''断开按钮点击槽函数'''
        self.device = None
        self.param_edited_enable(True)
        self.disconnectBtn.setEnabled(False)
        self.connectBtn.setEnabled(True)
        settings.device = None


class DeviceConnWidget(QDockWidget):
    def __init__(self, config=None, parent=None, logger=None):
        super(DeviceConnWidget, self).__init__(parent)
        self.setWindowTitle('通信接口')
        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WA_StyledBackground)  # 解决背景设置不成功问题
        self.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)
        self.setFeatures(QDockWidget.NoDockWidgetFeatures)  # 取消还原/关闭按钮
        self.config, self.parent, self.logger = config, parent, logger
        self.app_eventCenter = settings.app_event
        self.widget = DeviceWidget(
            self.config, self.parent, self.logger
        )
        self.setWidget(self.widget)
        self.widget.device_connected.connect(
            self.app_eventCenter.device_connected_event
        )
        self.app_eventCenter.devwidget_sw.connect(self.widget_sw)

    def get_device(self):
        return self.widget.device

    def widget_sw(self):
        '''窗口显隐槽函数'''
        if self.isHidden():
            self.show()
        else:
            self.hide()

    def closeEvent(self, event):
        self.app_eventCenter.devicewidget_close_event(self.windowTitle())
