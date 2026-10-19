"""复现 EQ 增益手动输入 >=10 / <=-10 时 "0" 打不进去的问题。

用法：QT_QPA_PLATFORM=offscreen .venv/Scripts/python test/eq_input_probe.py
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
from PyQt5.QtCore import Qt  # noqa: E402
from PyQt5.QtTest import QTest  # noqa: E402
from PyQt5.QtWidgets import QApplication  # noqa: E402

import config as settings  # noqa: E402
from appEvent import AppEvent  # noqa: E402
from audio_engine import AudioDocument, save_wav  # noqa: E402
from audio_widgets import AudioProcessingPage  # noqa: E402


def gain_spin(page, row=8, column=2):
    """EQ 表格第 row 行（默认 1000 Hz 段）的增益列 spinbox。"""
    return page._eq_table.cellWidget(row, column)


def type_seq(page, spin, keys_with_pause):
    spin.setFocus()
    spin.selectAll()
    for keys, pause_ms in keys_with_pause:
        QTest.keyClicks(spin, keys)
        if pause_ms:
            QTest.qWait(pause_ms)
    QTest.keyClick(spin, Qt.Key_Enter)
    return spin.value()


def main():
    app = QApplication(sys.argv)
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    settings.basepath = base
    settings.app_event = AppEvent(None, None)
    document = AudioDocument(os.path.join(base, "conf", "algorithms.json"))
    page = AudioProcessingPage(document)
    page.show()
    app.processEvents()

    print("== A. 未加载音频（立即生效），输入 1 -> 0 ==")
    spin = gain_spin(page)
    value = type_seq(page, spin, [("1", 0), ("0", 0)])
    print("  最终值: %.2f（期望 10.0）" % value)

    print("== B. 加载音频后（220ms 防抖 + 后台处理），慢速输入 1 ... 0 ==")
    rng = np.random.default_rng(0)
    wav_path = os.path.join(base, "test", "_probe.wav")
    save_wav(wav_path, 44100, (rng.standard_normal(44100) * 0.1).astype(np.float32))
    document.load(wav_path)
    QTest.qWait(2500)  # 等待解码与初始处理完成
    spin = gain_spin(page)
    spin.setValue(0.0)
    app.processEvents()
    value = type_seq(page, spin, [("1", 600), ("0", 0)])
    print("  最终值: %.2f（期望 10.0）" % value)
    print("  spin 可用: %s, 文档忙碌: %s" % (spin.isEnabled(), document.processing))

    print("== C. 加载音频，快速连续输入 -10 ==")
    QTest.qWait(2500)
    spin = gain_spin(page)
    spin.setValue(0.0)
    app.processEvents()
    value = type_seq(page, spin, [("-10", 0)])
    print("  最终值: %.2f（期望 -10.0）" % value)

    document.shutdown()
    if os.path.exists(wav_path):
        os.remove(wav_path)


if __name__ == "__main__":
    main()
