import numpy as np

from audio_analysis import (
    available_targets, calculate_spectrum, normalize_at_1k, smoothed_response,
    target_response,
)


def test_spectrum_smoothing_and_normalization_use_matching_grid():
    sample_rate = 48000
    time = np.arange(sample_rate, dtype=np.float64) / sample_rate
    mono = (0.2 * np.sin(2 * np.pi * 1000 * time)).astype(np.float32)
    stereo = np.column_stack((mono, mono * 0.5))

    frequencies, magnitudes = calculate_spectrum(stereo, sample_rate)
    smooth_x, smooth_y = smoothed_response(stereo, sample_rate)

    assert len(frequencies) == len(magnitudes) > 100
    assert len(smooth_x) == len(smooth_y) == 512
    assert np.isfinite(smooth_y).all()
    assert abs(normalize_at_1k(smooth_x, smooth_y)[np.argmin(np.abs(smooth_x - 1000))]) < 0.2


def test_builtin_harman_targets_are_normalized_at_1k():
    targets = available_targets()
    assert len(targets) == 2
    frequencies = np.array([20.0, 100.0, 1000.0, 10000.0, 20000.0])
    for target_name, label in targets:
        assert "Harman" in label
        values = target_response(target_name, frequencies)
        assert values.shape == frequencies.shape
        assert np.isfinite(values).all()
        assert abs(values[2]) < 1e-9
