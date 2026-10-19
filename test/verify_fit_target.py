"""离屏验证：目标曲线拟合对真实粉噪文件的端到端效果。"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from PyQt5.QtWidgets import QApplication

import config as settings
from audio_engine import AudioDocument
from audio_widgets import AudioProcessingPage
from audio_analysis import available_targets, smoothed_response, target_response

app = QApplication([])
doc = AudioDocument(os.path.join(settings.basepath, "conf", "algorithms.json"))
doc.load(os.path.join(settings.basepath, "data", "PinkNoise_30s.wav"))
assert doc.loaded, "加载失败"

page = AudioProcessingPage(doc)
key, label = available_targets()[0]
page.fit_target_provider = lambda: (key, label)
print("目标曲线：{} ({})".format(label, key))

page.control("fit_target")
print("状态栏：", page.status_label.text())

slot = doc.chain.get_slot("eq")
print("EQ 启用：", slot.enabled)
print("各段增益：", [round(b["gain_db"], 2) for b in slot.params["bands"]])

# 独立复算：拟合后“原始+EQ 响应”相对目标的残差
from scipy.signal import sosfreqz
from filters.EQFilters import build_eq_sos_bands
grid, before = smoothed_response(doc.original, doc.sample_rate)
target = target_response(key, grid)
sos = build_eq_sos_bands(doc.sample_rate, slot.params["bands"])
_, h = sosfreqz(sos, worN=grid, fs=doc.sample_rate)
eq_resp = 20.0 * np.log10(np.maximum(np.abs(h), 1e-9))
residual = (before + eq_resp) - target
valid = before > -45.0
print("有效频段：{:.0f}-{:.0f} Hz".format(grid[valid][0], grid[valid][-1]))
print("拟合后残差 RMS（有效频段）：{:.2f} dB".format(np.sqrt(np.mean(residual[valid] ** 2))))
print("拟合前残差 RMS（有效频段）：{:.2f} dB".format(np.sqrt(np.mean((before - target)[valid] ** 2))))
