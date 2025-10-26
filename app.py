import multiprocessing
multiprocessing.freeze_support()
import sys, datetime, logging
from logging import handlers
import os
import numpy as np
from PyQt5.QtWidgets import QMainWindow, QFrame, QDockWidget, QDesktopWidget, \
    QVBoxLayout, QMessageBox, QFileDialog
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon
import config as settings
from config import Config
from appEvent import AppEvent
from header import Header
from center import Center
from deviceWidget import DeviceConnWidget
# from samplingWidget import SamplingDockWidget
# from samplingMsgWidget import SamplingMsgDockWidget
from utility.psd import psd_tool_fft


class AudioTuningApp(QMainWindow):
    def __init__(self, config=None, logger=None):
        super(AudioTuningApp, self).__init__()
        self.config, self.logger = config, logger
        self.data, self.sampling_msg = None, None  # 数据, 采样信息
        self.app_eventCenter = settings.app_event
        self.default_path = self.config.read_key(
            'data', 'default_save', './', str
        )
        if not os.path.exists(self.default_path):
            os.mkdir(self.default_path)
        self.setWindowTitle("AudioTuning V1.0")
        icon_path = os.path.join(settings.basepath, "resource/pic/icon.png")
        self.setWindowIcon(QIcon(icon_path))
        # 窗口关闭关掉进程(效果同taskkill)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setDockNestingEnabled(True)
        self.setDockOptions(
            QMainWindow.AnimatedDocks | QMainWindow.AllowTabbedDocks
        )
        self.header = Header(
            config=self.config, parent=self, logger=self.logger
        )
        self.center = Center(
            config=self.config, parent=self, logger=self.logger
        )
        self.device_connect = DeviceConnWidget(
            self.config, self, self.logger
        )
        # self.sampling_setting = SamplingDockWidget(
        #     self.config, self, self.logger
        # )
        # self.sampling_display = SamplingMsgDockWidget(
        #     self.config, self, self.logger
        # )
        self.setCentralWidget(self.center)

        self._layout()
        self.adjustSize()
        self.move_center()

        # self.app_eventCenter.file_open.connect(self.open_file)
        # self.app_eventCenter.save_file.connect(self.save_file)
        # self.app_eventCenter.collect_start.connect(self.start_collect)
        # self.app_eventCenter.dev_init_connected.connect(self.device_connected)

    def _layout(self):
        # 设置header导航栏
        header_docker = QDockWidget(self)
        header_docker.setObjectName("HeadDocker")
        newheader_docker_titleBar = QFrame()
        header_docker.setTitleBarWidget(newheader_docker_titleBar)
        header_docker.setWidget(self.header)
        header_docker.setFeatures(QDockWidget.NoDockWidgetFeatures)
        header_docker.setAllowedAreas(Qt.TopDockWidgetArea)
        self.addDockWidget(Qt.TopDockWidgetArea, header_docker)
        # 设置设备连接窗口
        self.addDockWidget(Qt.RightDockWidgetArea, self.device_connect)
        # # 设置采样设置窗口
        # self.addDockWidget(Qt.RightDockWidgetArea, self.sampling_setting)
        # # 设置数据信息窗口
        # self.addDockWidget(Qt.RightDockWidgetArea, self.sampling_display)

    def move_center(self):
        '''窗体移动至屏幕中央'''
        screen = QDesktopWidget().screenGeometry()
        self.resize(QSize(screen.width()/3*2, screen.height()/3*2))
        size = self.geometry()
        self.move((screen.width()-size.width())/2,
                  (screen.height()-size.height()-80)/2)

    def device_connected(self):
        '''设备(首次)连接'''
        try:
            device = self.device_connect.get_device()
            cmds = self.sampling_setting.get_cmds()
            if device:
                for _cmd in cmds:
                    device.cmd(_cmd)
                    self.logger.debug(_cmd)
        except Exception as e:
            self.logger.exception(e)

    # def open_file(self):
    #     '''打开文件'''
    #     filename, _ = QFileDialog.getOpenFileName(
    #         self, '打开数据', './', 'h5 (*.h5)'
    #     )
    #     if filename:
    #         try:
    #             params_dict = dict()
    #             h5_file = h5py.File(filename, 'r')  # h5文件
    #             data = h5_file['data'][:]
    #             for key in h5_file['metadata'].keys():
    #                 params_dict[key] = h5_file[f'metadata/{key}'][()]
    #             self.sampling_setting.set_ch(params_dict['ch'])
    #             self.sampling_display.update_msg(params_dict)
    #             self.center.file_plot(data, params_dict)
    #         except Exception as e:
    #             self.logger.exception(e)

    def closeEvent(self, event):
        self.logger.debug('App closed.')


def logStart(debug=False, _level='INFO'):
    '''日志启动'''
    pwd = os.path.dirname(__file__)

    if not os.path.exists(os.path.join(pwd, "log")):
        os.makedirs(os.path.join(pwd, "log"))

    if not debug:
        log_filename = os.path.join(pwd, "log/running.log")
        handler = handlers.RotatingFileHandler(
            log_filename, maxBytes=1024*1024*10, backupCount=10
        )
        logging.basicConfig(
            format='[%(levelname)-8s] %(asctime)s %(filename)s[%(funcName)s-\
                line:%(lineno)d] %(message)s',
            datefmt='%a, %Y-%m-%d %H:%M:%S',
            level=_level,
            handlers=[handler]
        )
        logger = logging.getLogger("TR0100 v1.0")
    else:
        logger = logging.getLogger(__name__)
        logger.setLevel(f'{_level}')
        handler = logging.StreamHandler(sys.stdout)
        logformat = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(logformat)
        logger.addHandler(handler)
    logger.info("Starting TR0100 v1.0...")

    return logger


if __name__ == '__main__':
    import os, sys
    from PyQt5.QtWidgets import QSplashScreen, QApplication
    from PyQt5.QtCore import QCoreApplication, QT_VERSION_STR
    from PyQt5.QtGui import QPixmap

    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)

    QtVersion = QT_VERSION_STR
    qtVersionCompare = tuple(map(int, QtVersion.split(".")))
    if qtVersionCompare > (6, 0):
        # Qt6 seems to support hidpi without needing to do anything so continue
        pass
    elif qtVersionCompare > (5, 14):
        os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    else:  # qt 5.12 and 5.13
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    base_path = os.path.dirname(__file__)
    qss_path = os.path.join(base_path, "resource/qss/app.qss")
    settings.basepath = base_path
    app = QApplication(sys.argv)
    welcome = QSplashScreen(QPixmap(
        os.path.join(base_path, 'resource/pic/welcome.png')))
    welcome.show()
    config = Config(os.path.join(base_path, "conf/setup.ini"))
    log_mode = config.read_key(
            'logger', 'debug_mode',
            False, bool
        )
    log_level = config.read_key(
            'logger', 'log_level',
            'INFO', str
        )
    logger = logStart(debug=log_mode, _level=log_level)
    config = Config(os.path.join(base_path, "conf/setup.ini"))

    app.processEvents()  # 防进程卡死
    settings.app_event = AppEvent(config, logger)
    settings.psd_tool = psd_tool_fft(np.zeros(10), None, 1000)
    viewer = AudioTuningApp(config=config, logger=logger)

    with open(qss_path, 'r') as f:
        viewer.setStyleSheet(f.read())
        f.close()

    welcome.finish(viewer)
    viewer.show()
    sys.exit(app.exec_())
