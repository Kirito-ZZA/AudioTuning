"""Waveform, spectrum and target-curve calculations without GUI dependencies."""

import os
from functools import lru_cache

import numpy as np


TARGET_CURVES = {
    "harman_over_ear_2018": ("Harman 头戴式 2018", "Harman over-ear 2018.csv"),
    "harman_in_ear_2019": ("Harman 入耳式 2019", "Harman in-ear 2019.csv"),
}


def plot_samples(data, sample_rate, limit=50000):
    if data is None or not len(data):
        return np.array([]), np.array([])
    mono = data.mean(axis=1) if data.ndim > 1 else data
    stride = max(1, int(np.ceil(len(mono) / float(limit))))
    values = mono[::stride]
    times = np.arange(len(values), dtype=np.float64) * stride / sample_rate
    return times, values


def calculate_spectrum(data, sample_rate, max_fft=262144):
    if data is None or len(data) < 16 or sample_rate <= 0:
        return np.array([]), np.array([])
    mono = data.mean(axis=1) if data.ndim > 1 else data
    size = min(len(mono), max_fft)
    size = 1 << int(np.floor(np.log2(size)))
    samples = np.asarray(mono[:size], dtype=np.float64)
    samples = samples - np.mean(samples)
    window = np.hanning(size)
    spectrum = np.fft.rfft(samples * window)
    magnitude = 2.0 * np.abs(spectrum) / max(np.sum(window), 1.0)
    frequencies = np.fft.rfftfreq(size, 1.0 / sample_rate)
    valid = frequencies >= min(20.0, sample_rate / 4.0)
    return frequencies[valid], 20.0 * np.log10(np.maximum(magnitude[valid], 1e-7))


def smooth_spectrum(frequencies, magnitudes_db, points=512, fraction=6):
    frequencies = np.asarray(frequencies, dtype=np.float64)
    magnitudes_db = np.asarray(magnitudes_db, dtype=np.float64)
    valid = (frequencies > 0.0) & np.isfinite(magnitudes_db)
    frequencies = frequencies[valid]
    magnitudes_db = magnitudes_db[valid]
    if len(frequencies) < 2 or fraction <= 0:
        return np.array([]), np.array([])

    lower = max(20.0, float(frequencies[0]))
    upper = min(20000.0, float(frequencies[-1]))
    if lower >= upper:
        return np.array([]), np.array([])
    grid = np.geomspace(lower, upper, points)
    power = 10.0 ** (magnitudes_db / 10.0)
    ratio = 2.0 ** (1.0 / (2.0 * fraction))
    left = np.searchsorted(frequencies, grid / ratio, side="left")
    right = np.searchsorted(frequencies, grid * ratio, side="right")
    smoothed_power = np.empty(len(grid), dtype=np.float64)
    fallback = 10.0 ** (magnitudes_db / 10.0)
    for index, (start, end) in enumerate(zip(left, right)):
        if end > start:
            smoothed_power[index] = np.mean(power[start:end])
        else:
            smoothed_power[index] = np.interp(
                np.log(grid[index]), np.log(frequencies), fallback
            )
    return grid, 10.0 * np.log10(np.maximum(smoothed_power, 1e-14))


def normalize_at_1k(frequencies, values_db):
    frequencies = np.asarray(frequencies, dtype=np.float64)
    values_db = np.asarray(values_db, dtype=np.float64)
    if not len(frequencies):
        return values_db.copy()
    reference = np.interp(np.log(1000.0), np.log(frequencies), values_db)
    return values_db - reference


def smoothed_response(data, sample_rate, points=512, fraction=6):
    frequencies, magnitudes = calculate_spectrum(data, sample_rate)
    frequencies, magnitudes = smooth_spectrum(
        frequencies, magnitudes, points=points, fraction=fraction
    )
    return frequencies, normalize_at_1k(frequencies, magnitudes)


def available_targets():
    return tuple((key, value[0]) for key, value in TARGET_CURVES.items())


@lru_cache(maxsize=8)
def _read_target(target_name, resource_root):
    if target_name not in TARGET_CURVES:
        raise ValueError("未知目标曲线：{}".format(target_name))
    path = os.path.join(resource_root, TARGET_CURVES[target_name][1])
    data = np.genfromtxt(path, delimiter=",", names=True, encoding="utf-8")
    if data.size < 2 or not {"frequency", "raw"}.issubset(data.dtype.names or ()):
        raise ValueError("目标曲线文件格式无效：{}".format(path))
    frequencies = np.asarray(data["frequency"], dtype=np.float64)
    values = np.asarray(data["raw"], dtype=np.float64)
    order = np.argsort(frequencies)
    return frequencies[order], values[order]


def target_response(target_name, frequencies, resource_root=None):
    if resource_root is None:
        resource_root = os.path.join(os.path.dirname(__file__), "resource", "targets")
    source_x, source_y = _read_target(target_name, os.path.abspath(resource_root))
    frequencies = np.asarray(frequencies, dtype=np.float64)
    values = np.interp(
        np.log(frequencies), np.log(source_x), source_y,
        left=source_y[0], right=source_y[-1],
    )
    reference = np.interp(np.log(1000.0), np.log(source_x), source_y)
    return values - reference
