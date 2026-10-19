"""RBJ peaking equalizer with independently configurable bands."""

import numpy as np
from scipy.signal import sosfilt, sosfreqz

from filters.base import AudioAlgorithm, ParameterSpec


EQ_FREQUENCIES = (
    25, 40, 63, 100, 160, 250, 400, 630,
    1000, 1600, 2500, 4000, 6300, 10000, 16000, 20000,
)
EQ_BAND_COLUMNS = (
    ParameterSpec("frequency", "频率", 1000.0, 10.0, 24000.0, 1.0, "Hz"),
    ParameterSpec("gain_db", "增益", 0.0, -15.0, 15.0, 0.1, "dB"),
    ParameterSpec("q", "Q 值", 1.4, 0.1, 20.0, 0.1),
)
DEFAULT_EQ_BANDS = tuple((frequency, 0.0, 1.4) for frequency in EQ_FREQUENCIES)
EQ_BANDS_SPEC = ParameterSpec(
    "bands", "EQ 频段", DEFAULT_EQ_BANDS, 0.0, 0.0,
    kind="table",
    labels=tuple("Band {:02d}".format(index + 1) for index in range(len(EQ_FREQUENCIES))),
    columns=EQ_BAND_COLUMNS,
)


def peaking_sos(sample_rate, frequency, gain_db, q=1.4):
    w0 = 2.0 * np.pi * float(frequency) / float(sample_rate)
    alpha = np.sin(w0) / (2.0 * float(q))
    a = 10.0 ** (float(gain_db) / 40.0)
    cos_w0 = np.cos(w0)
    b0 = 1.0 + alpha * a
    b1 = -2.0 * cos_w0
    b2 = 1.0 - alpha * a
    a0 = 1.0 + alpha / a
    a1 = -2.0 * cos_w0
    a2 = 1.0 - alpha / a
    return np.array([[b0 / a0, b1 / a0, b2 / a0,
                      1.0, a1 / a0, a2 / a0]], dtype=np.float64)


def build_eq_sos_bands(sample_rate, bands):
    bands = EQ_BANDS_SPEC.coerce(bands)
    rows = []
    nyquist = sample_rate / 2.0
    for band in bands:
        frequency = band["frequency"]
        if abs(band["gain_db"]) >= 0.01 and frequency < nyquist * 0.98:
            rows.append(peaking_sos(
                sample_rate, frequency, band["gain_db"], band["q"]
            ))
    return np.vstack(rows) if rows else np.empty((0, 6), dtype=np.float64)


def build_eq_sos(sample_rate, gains, q=1.4):
    gains = np.asarray(gains, dtype=np.float32)
    if gains.shape != (len(EQ_FREQUENCIES),):
        raise ValueError("EQ 增益必须正好包含 16 段")
    bands = [
        (frequency, gain, q)
        for frequency, gain in zip(EQ_FREQUENCIES, gains)
    ]
    return build_eq_sos_bands(sample_rate, bands)


def _apply_sos(data, sos):
    if not len(sos):
        return np.array(data, dtype=np.float32, copy=True)
    filtered = sosfilt(sos, np.asarray(data, dtype=np.float64), axis=0)
    return filtered.astype(np.float32)


def apply_eq_bands(data, sample_rate, bands):
    return _apply_sos(data, build_eq_sos_bands(sample_rate, bands))


def apply_equalizer(data, sample_rate, gains, q=1.4):
    return _apply_sos(data, build_eq_sos(sample_rate, gains, q))


def _response_from_sos(sample_rate, sos, points):
    nyquist = sample_rate / 2.0
    lower = min(20.0, nyquist * 0.5)
    upper = max(lower * 1.001, min(20000.0, nyquist * 0.98))
    frequencies = np.geomspace(lower, upper, points)
    if not len(sos):
        return frequencies, np.zeros_like(frequencies)
    _, response = sosfreqz(sos, worN=frequencies, fs=sample_rate)
    return frequencies, 20.0 * np.log10(np.maximum(np.abs(response), 1e-9))


def eq_bands_response(sample_rate, bands, points=2048):
    return _response_from_sos(
        sample_rate, build_eq_sos_bands(sample_rate, bands), points
    )


def eq_response(sample_rate, gains, points=2048, q=1.4):
    return _response_from_sos(sample_rate, build_eq_sos(sample_rate, gains, q), points)


def fit_bands_to_curve(sample_rate, frequencies, desired_db, bands, iterations=8):
    """按目标差值曲线最小二乘拟合各频段增益（每段频率与 Q 保持现状）。

    单段 dB 频响与增益近似线性，因此以 +1 dB 单位增益响应为基函数做线性
    最小二乘，再围绕当前解用真实滤波器频响迭代修正非线性误差，增益始终
    限制在参数规范允许的范围内。

    Args:
        sample_rate: 采样率。
        frequencies: 对数频率网格（Hz），应只包含有效频段
            （信号缺失区域，如 MP3 高切以上，调用方需先剔除）。
        desired_db: 期望的 EQ 频响（目标曲线 − 源平滑谱），与网格等长。
        bands: 当前 bands 参数（读取每段频率与 Q）。
        iterations: 非线性修正迭代次数。

    Returns:
        (bands, achieved_db)：拟合后的 bands 参数（dict 列表）与拟合得到
        的实际 EQ 频响（在输入网格上）。
    """
    bands = EQ_BANDS_SPEC.coerce(bands)
    frequencies = np.asarray(frequencies, dtype=np.float64)
    desired_db = np.asarray(desired_db, dtype=np.float64)
    nyquist = sample_rate / 2.0
    valid = (
        np.isfinite(desired_db) & np.isfinite(frequencies)
        & (frequencies >= 20.0) & (frequencies <= nyquist * 0.98)
    )
    fit_frequencies = frequencies[valid]
    fit_desired = desired_db[valid]
    if len(fit_frequencies) < len(bands):
        raise ValueError("可用于拟合的频点过少，请检查音源与采样率。")

    gain_spec = EQ_BAND_COLUMNS[1]
    basis_columns = []
    for band in bands:
        frequency = band["frequency"]
        if frequency < nyquist * 0.98:
            sos = peaking_sos(sample_rate, frequency, 1.0, band["q"])
            _, response = sosfreqz(sos, worN=fit_frequencies, fs=sample_rate)
            basis_columns.append(
                20.0 * np.log10(np.maximum(np.abs(response), 1e-9))
            )
        else:
            basis_columns.append(np.zeros_like(fit_frequencies))
    basis = np.stack(basis_columns, axis=1)

    def _achieved(gains):
        sos = build_eq_sos_bands(sample_rate, [
            (band["frequency"], gain, band["q"])
            for band, gain in zip(bands, gains)
        ])
        if not len(sos):
            return np.zeros_like(fit_frequencies)
        _, response = sosfreqz(sos, worN=fit_frequencies, fs=sample_rate)
        return 20.0 * np.log10(np.maximum(np.abs(response), 1e-9))

    gains = np.zeros(len(bands))
    for _ in range(max(1, int(iterations))):
        delta, _residual, _rank, _sv = np.linalg.lstsq(
            basis, fit_desired - _achieved(gains), rcond=None
        )
        if not np.all(np.isfinite(delta)):
            break
        gains = np.clip(gains + delta, gain_spec.minimum, gain_spec.maximum)
        if np.max(np.abs(delta)) < 0.01:
            break

    fitted = [
        {
            "frequency": band["frequency"],
            "gain_db": float(round(gain, 2)),
            "q": band["q"],
        }
        for band, gain in zip(bands, gains)
    ]
    return fitted, _achieved(gains)


class EqualizerAlgorithm(AudioAlgorithm):
    algorithm_id = "eq"
    display_name = "EQ 均衡器"
    parameters = (EQ_BANDS_SPEC,)

    def process(self, data, sample_rate, params):
        return apply_eq_bands(data, sample_rate, params["bands"])
