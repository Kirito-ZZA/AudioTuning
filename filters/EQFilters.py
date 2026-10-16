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
    ParameterSpec("gain_db", "增益", 0.0, -12.0, 12.0, 0.1, "dB"),
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


class EqualizerAlgorithm(AudioAlgorithm):
    algorithm_id = "eq"
    display_name = "EQ 均衡器"
    parameters = (EQ_BANDS_SPEC,)

    def process(self, data, sample_rate, params):
        return apply_eq_bands(data, sample_rate, params["bands"])
