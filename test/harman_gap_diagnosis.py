"""哈曼对比页曲线偏差诊断实验（不改业务代码）。

模拟调音工作流：构造测试信号 -> 按哈曼目标反推最优 EQ 增益 -> 走与页面完全
相同的处理与绘图计算链路 -> 量化处理后曲线与哈曼目标的残差。

用法：.venv/Scripts/python test/harman_gap_diagnosis.py
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio_analysis import smoothed_response, target_response  # noqa: E402
from filters.EQFilters import EQ_FREQUENCIES, apply_eq_bands, build_eq_sos_bands  # noqa: E402
from scipy.signal import sosfreqz  # noqa: E402

SR = 44100
SECONDS = 30


def make_white(rng):
    data = rng.standard_normal(SR * SECONDS)
    return (data / np.max(np.abs(data)) * 0.5).astype(np.float32)


def make_pink(rng):
    white = rng.standard_normal(SR * SECONDS)
    spectrum = np.fft.rfft(white)
    freqs = np.fft.rfftfreq(len(white), 1.0 / SR)
    freqs[0] = freqs[1]
    spectrum = spectrum / np.sqrt(freqs)
    pink = np.fft.irfft(spectrum, len(white))
    return (pink / np.max(np.abs(pink)) * 0.5).astype(np.float32)


def best_effort_bands(source_name, source_smooth_x, source_smooth_y, target_y):
    """按页面口径反推每段 EQ 增益：gain(f) = target(f) - source(f)。"""
    bands = []
    for frequency in EQ_FREQUENCIES:
        source_at_f = np.interp(
            np.log(frequency), np.log(source_smooth_x), source_smooth_y
        )
        target_at_f = np.interp(
            np.log(frequency), np.log(source_smooth_x), target_y
        )
        gain = float(np.clip(target_at_f - source_at_f, -15.0, 15.0))
        bands.append((frequency, gain, 1.4))
    return bands


def residual_report(tag, grid, after_y, target_y):
    residual = after_y - target_y
    regions = ((20, 100), (100, 1000), (1000, 8000), (8000, 20000), (20, 20000))
    print("  [%s]" % tag)
    for low, high in regions:
        mask = (grid >= low) & (grid <= high)
        seg = residual[mask]
        print(
            "    %5d-%5d Hz: max %+5.2f dB  min %+5.2f dB  RMS %5.2f dB"
            % (low, high, seg.max(), seg.min(), np.sqrt(np.mean(seg ** 2)))
        )
    return residual


def main():
    rng = np.random.default_rng(42)
    print("== 1. 白噪声（平坦谱）输入，EQ 增益按目标曲线最优反推 ==")
    white = make_white(rng)
    before_x, before_y = smoothed_response(white, SR)
    target_y = target_response("harman_in_ear_2019", before_x)
    bands = best_effort_bands("white", before_x, before_y, target_y)
    processed = apply_eq_bands(white, SR, bands)
    after_x, after_y = smoothed_response(processed, SR)
    assert np.allclose(before_x, after_x)
    residual_report("白噪声 + 最优EQ", before_x, after_y, target_y)

    print("== 2. 粉噪声（-3dB/oct）输入，同样的最优 EQ ==")
    pink = make_pink(rng)
    pbefore_x, pbefore_y = smoothed_response(pink, SR)
    pbands = best_effort_bands("pink", pbefore_x, pbefore_y, target_y)
    pprocessed = apply_eq_bands(pink, SR, pbands)
    _, pafter_y = smoothed_response(pprocessed, SR)
    residual_report("粉噪声 + 最优EQ", pbefore_x, pafter_y, target_y)

    print("== 3. EQ 全 0（当前默认状态），白噪声输入 ==")
    residual_report("白噪声 + 平EQ", before_x, before_y, target_y)

    print("== 4. EQ 实际频响与目标之差（滤波器本身的能力上限）==")
    sos = build_eq_sos_bands(SR, bands)
    grid = np.geomspace(20, 20000, 512)
    _, response = sosfreqz(sos, worN=grid, fs=SR)
    eq_db = 20.0 * np.log10(np.maximum(np.abs(response), 1e-9))
    eq_db = eq_db - np.interp(np.log(1000.0), np.log(grid), eq_db)
    target_on_grid = target_response("harman_in_ear_2019", grid)
    residual_report("EQ传递函数", grid, eq_db, target_on_grid)

    print("== 5. 反推得到的 16 段增益（检查是否触顶 ±12dB）==")
    for (frequency, gain, q) in bands:
        clipped = "  << 触顶" if abs(gain) >= 11.99 else ""
        print("    %6.0f Hz  gain %+6.2f dB  Q %.1f%s" % (frequency, gain, q, clipped))


if __name__ == "__main__":
    main()
