"""Qt offscreen 界面冒烟脚本：渲染主窗口并导出截图，不做人工试听。

用法：QT_QPA_PLATFORM=offscreen .venv/Scripts/python test/ui_smoke_offscreen.py [dark|light]
截图输出到 test/ui_shots/，文件名带主题后缀。
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config as settings  # noqa: E402
import theme  # noqa: E402
from PyQt5.QtCore import QTimer  # noqa: E402
from PyQt5.QtWidgets import QApplication  # noqa: E402

from app import AudioTuningApp  # noqa: E402
from appEvent import AppEvent  # noqa: E402
from config import Config  # noqa: E402

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui_shots")


def main():
    theme_name = sys.argv[1] if len(sys.argv) > 1 else "dark"
    theme.set_theme(theme_name)
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    settings.basepath = base_path
    os.makedirs(OUT_DIR, exist_ok=True)
    app = QApplication(sys.argv)
    config = Config(os.path.join(base_path, "conf/setup.ini"))
    settings.app_event = AppEvent(config, None)
    viewer = AudioTuningApp(config=config, logger=None)
    viewer.setStyleSheet(theme.render_qss())
    viewer.show()
    app.processEvents()

    def shoot():
        viewer.grab().save(os.path.join(OUT_DIR, "main_%s.png" % theme_name))
        # 逐个页签截图
        tab_bar = viewer.center.tabBar
        stack = viewer.center.plotStackedWidget
        for index in range(stack.count()):
            stack.setCurrentIndex(index)
            tab_bar.tabs[index].setChecked(True)
            app.processEvents()
            name = stack.widget(index).metaObject().className()
            viewer.grab().save(
                os.path.join(OUT_DIR, "tab_%d_%s_%s.png" % (index, name, theme_name))
            )
        app.quit()

    QTimer.singleShot(800, shoot)
    app.exec_()
    print("screenshots saved to", OUT_DIR, "theme:", theme.current_theme())


if __name__ == "__main__":
    main()
