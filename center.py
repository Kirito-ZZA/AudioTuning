from PyQt5.QtWidgets import QFrame, QStackedWidget, \
    QVBoxLayout, QHBoxLayout
import numpy as np
from tabBar import TabBar
# from noisePlotWidget import NoisePlotWidget
# from distributePlotWidget import DisributePlotWidget
# from spectrumPlotWidget import SpectrumPlotWidget
# from specNoisePlotWidget import SpecNoisePlotWidget
import config as settings


class Center(QFrame):
    def __init__(self, config=None, parent=None, logger=None):
        super(Center, self).__init__(parent)
        self.config, self.parent, self.logger = config, parent, logger

        self.app_eventCenter = settings.app_event

        self.tabBar = TabBar(self.config, self, self.logger)

        #TODO: 以下widget待完善
        self.plotStackedWidget = QStackedWidget()  # 绘图切换
        # self.noisePlotWidget = NoisePlotWidget(
        #     config, parent, logger
        # )
        # self.distributePlotWidget = DisributePlotWidget(
        #     config, parent, logger
        # )
        # self.spectrumPlotWidget = SpectrumPlotWidget(
        #     config, parent, logger
        # )
        # self.specNoisePlotWidget = SpecNoisePlotWidget(
        #     config, parent, logger
        # )
        # self.plotStackedWidget.addWidget(self.noisePlotWidget)
        # self.plotStackedWidget.addWidget(self.distributePlotWidget)
        # self.plotStackedWidget.addWidget(self.spectrumPlotWidget)
        # self.plotStackedWidget.addWidget(self.specNoisePlotWidget)
        self.plotStackedWidget.addWidget(QFrame())  # 空窗口 index 0
        self.plotStackedWidget.addWidget(QFrame())  # 空窗口 index 1
        self.plotStackedWidget.addWidget(QFrame())  # 空窗口 index 2
        self.plotStackedWidget.addWidget(QFrame())  # 空窗口 index 3
        self.plotStackedWidget.addWidget(QFrame())  # 空窗口 index 4
        self._layout()

        self.tabBar.tab_change.connect(self.plot_sw)
        self.app_eventCenter.meas_ch_change.connect(self.ch_change_event)
        self.app_eventCenter.plot_auto_range.connect(self.auto_range_event)

    def _layout(self):
        basic_layout = QVBoxLayout()
        # 上方控制， 下方绘图
        basic_layout.addWidget(self.tabBar)
        basic_layout.addWidget(self.plotStackedWidget)
        basic_layout.setContentsMargins(0, 0, 0, 0)
        basic_layout.setSpacing(0)
        self.setLayout(basic_layout)

    def plot(self, data, sampling):
        '''绘图'''
        try:
            sample_rate = sampling['采样率']
            cut_off_freq = sampling['截止频率']
            _unit = 'A' if sampling['测量通道'] in ['CURR'] else 'V'
            settings.psd_tool.update_data(
                data, _unit, sample_rate, cut_off_freq
            )
            sample_rate, raw_data = settings.psd_tool.get_raw_data()
            t_list = np.arange(0, len(raw_data)) * (1 / sample_rate)
            self.noisePlotWidget.set_plot(t_list, raw_data)
            self.distributePlotWidget.set_plot(raw_data)
            self.tabBar.update_analysis_value(
                settings.psd_tool.Vpp, settings.psd_tool.Vrms,
                settings.psd_tool.data_std, settings.psd_tool.e_n
            )
            self.spectrumPlotWidget.set_plot(data, sample_rate)
            self.specNoisePlotWidget.set_plot(data, sample_rate)
            self.tabBar.autoBtn.click()
        except Exception as e:
            self.logger.exception(e)

    def file_plot(self, data, params_dict):
        '''
        文件打开绘图
        Args:
            data (list) : 原始数据列表
            params_dict (dict): 数据采集参数字典
                key_list: ['APER', 'Filter', 'Z', 'ch',
                    'end_freq', 'range', 'sample_rate', 'start_freq']
        '''
        try:
            sample_rate = params_dict['sample_rate']
            cut_off_freq = params_dict['end_freq']
            _unit = 'A' if params_dict['ch'] in ['CURR'] else 'V'
            # t_list = np.linspace(0, _t, len(data))
            # t_list = np.arange(0, len(data)) * _t
            settings.psd_tool.update_data(
                data, _unit, sample_rate, cut_off_freq
            )
            sample_rate, raw_data = settings.psd_tool.get_raw_data()
            t_list = np.arange(0, len(raw_data)) * (1 / sample_rate)
            self.noisePlotWidget.set_plot(t_list, raw_data)
            self.distributePlotWidget.set_plot(raw_data)
            self.tabBar.update_analysis_value(
                settings.psd_tool.Vpp, settings.psd_tool.Vrms,
                settings.psd_tool.data_std, settings.psd_tool.e_n
            )
            self.spectrumPlotWidget.set_plot(data, sample_rate)
            self.specNoisePlotWidget.set_plot(data, sample_rate)
            self.tabBar.autoBtn.click()
        except Exception as e:
            self.logger.exception(e)

    def ch_change_event(self, ch):
        '''
        测量通道切换槽函数
        Args:
            ch (str): 通道 (VOLT, CURR)
        '''
        if ch == 'VOLT':
            self.noisePlotWidget.set_yLabel('Volt', 'V')
            self.distributePlotWidget.set_xLabel('Vos', 'V')
            self.spectrumPlotWidget.set_yLabel('e<sub>n</sub>', 'V/√Hz')
            self.specNoisePlotWidget.set_yLabel('Volt', 'V')
            self.tabBar.noiseWidget.refresh_label('V')
            self.tabBar.distributeWidget.refresh_label('V')
            self.tabBar.noiseSpectrumWidget.refresh_label('e')
        elif ch == 'CURR':
            self.noisePlotWidget.set_yLabel('Curr', 'A')
            self.distributePlotWidget.set_xLabel('Ios', 'A')
            self.spectrumPlotWidget.set_yLabel('i<sub>n</sub>', 'A/√Hz')
            self.specNoisePlotWidget.set_yLabel('Curr', 'A')
            self.tabBar.noiseWidget.refresh_label('A')
            self.tabBar.distributeWidget.refresh_label('A')
            self.tabBar.noiseSpectrumWidget.refresh_label('i')

    def auto_range_event(self):
        '''绘图显示自适应事件槽函数'''
        self.noisePlotWidget.plot.enableAutoRange()
        self.distributePlotWidget.plot.enableAutoRange()
        self.spectrumPlotWidget.plot.enableAutoRange()
        self.specNoisePlotWidget.plot.enableAutoRange()

    def plot_sw(self, tab_index):
        '''绘图stackedWidget切换槽函数'''
        self.plotStackedWidget.setCurrentIndex(tab_index)
