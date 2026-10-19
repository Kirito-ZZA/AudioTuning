import multiprocessing

multiprocessing.freeze_support()

import logging
import os
import sys
from logging import handlers

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDesktopWidget, QDockWidget, QFrame, QMainWindow

import config as settings
import theme
from appEvent import AppEvent
from audio_io import configure_ffmpeg
from center import Center
from config import Config
from deviceWidget import DeviceConnWidget
from header import Header


class AudioTuningApp(QMainWindow):
    def __init__(self, config=None, logger=None):
        super().__init__()
        self.config, self.logger = config, logger
        self.app_eventCenter = settings.app_event
        self.default_path = self.config.read_key("data", "default_save", "./data", str)
        if not os.path.isabs(self.default_path):
            self.default_path = os.path.join(settings.basepath, self.default_path)
        os.makedirs(self.default_path, exist_ok=True)

        self.setWindowTitle("AudioTuning V1.0")
        self.setWindowIcon(QIcon(os.path.join(settings.basepath, "resource/pic/icon.png")))
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setDockNestingEnabled(True)
        self.setDockOptions(QMainWindow.AnimatedDocks | QMainWindow.AllowTabbedDocks)
        self.header = Header(config=self.config, parent=self, logger=self.logger)
        self.center = Center(config=self.config, parent=self, logger=self.logger)
        self.device_connect = DeviceConnWidget(self.config, self, self.logger)
        self.setCentralWidget(self.center)
        self._layout()
        self.adjustSize()
        self.move_center()

    def _layout(self):
        header_docker = QDockWidget(self)
        header_docker.setObjectName("HeadDocker")
        header_docker.setTitleBarWidget(QFrame())
        header_docker.setWidget(self.header)
        header_docker.setFeatures(QDockWidget.NoDockWidgetFeatures)
        header_docker.setAllowedAreas(Qt.TopDockWidgetArea)
        self.addDockWidget(Qt.TopDockWidgetArea, header_docker)
        self.addDockWidget(Qt.RightDockWidgetArea, self.device_connect)

    def move_center(self):
        screen = QDesktopWidget().screenGeometry()
        self.resize(QSize(int(screen.width() / 3 * 2), int(screen.height() / 3 * 2)))
        size = self.geometry()
        self.move(
            int((screen.width() - size.width()) / 2),
            int((screen.height() - size.height() - 80) / 2),
        )

    def closeEvent(self, event):
        self.center.shutdown()
        if self.logger:
            self.logger.debug("App closed.")
        super().closeEvent(event)


def logStart(debug=False, _level="INFO"):
    pwd = os.path.dirname(__file__)
    os.makedirs(os.path.join(pwd, "log"), exist_ok=True)
    if not debug:
        handler = handlers.RotatingFileHandler(
            os.path.join(pwd, "log/running.log"),
            maxBytes=1024 * 1024 * 10,
            backupCount=10,
        )
        logging.basicConfig(
            format="[%(levelname)-8s] %(asctime)s %(filename)s[%(funcName)s-line:%(lineno)d] %(message)s",
            datefmt="%a, %Y-%m-%d %H:%M:%S",
            level=_level,
            handlers=[handler],
        )
        logger = logging.getLogger("AudioTuning")
    else:
        logger = logging.getLogger("AudioTuning")
        logger.setLevel(_level)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))
        logger.addHandler(handler)
    logger.info("Starting AudioTuning V1.0...")
    return logger


if __name__ == "__main__":
    from PyQt5.QtCore import QCoreApplication, QT_VERSION_STR
    from PyQt5.QtGui import QPixmap
    from PyQt5.QtWidgets import QApplication, QSplashScreen

    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    qt_version = tuple(map(int, QT_VERSION_STR.split(".")))
    if qt_version > (5, 14):
        os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    else:
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    base_path = os.path.dirname(os.path.abspath(__file__))
    settings.basepath = base_path
    app = QApplication(sys.argv)
    welcome = QSplashScreen(QPixmap(os.path.join(base_path, "resource/pic/welcome.png")))
    welcome.show()
    config = Config(os.path.join(base_path, "conf/setup.ini"))
    logger = logStart(
        debug=config.read_key("logger", "debug_mode", False, bool),
        _level=config.read_key("logger", "log_level", "INFO", str),
    )
    theme_name = config.read_key("ui", "theme", "dark", str)
    try:
        theme.set_theme(theme_name)
    except ValueError as exc:
        logger.warning("%s，回退到默认主题 dark", exc)
        theme.set_theme("dark")
    ffmpeg_dir = config.read_key("tools", "ffmpeg_dir", "", str)
    if ffmpeg_dir:
        if configure_ffmpeg(ffmpeg_dir):
            logger.info("ffmpeg 已配置：%s", ffmpeg_dir)
        else:
            logger.warning(
                "ffmpeg 目录无效：%s（MP3/AAC 等非 WAV/PCM 文件将无法解码）", ffmpeg_dir
            )
    app.processEvents()
    settings.app_event = AppEvent(config, logger)
    viewer = AudioTuningApp(config=config, logger=logger)
    viewer.setStyleSheet(theme.render_qss())
    welcome.finish(viewer)
    viewer.show()
    sys.exit(app.exec_())
