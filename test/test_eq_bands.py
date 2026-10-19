import numpy as np
import pytest

from audio_engine import (
    EQ_FREQUENCIES, apply_eq_bands, build_eq_sos_bands, eq_bands_response,
)
from filters.EQFilters import EqualizerAlgorithm


def _bands():
    return [dict(row) for row in EqualizerAlgorithm.default_parameters()["bands"]]


def test_independent_band_frequency_gain_and_q():
    bands = _bands()
    bands[8].update(frequency=1200.0, gain_db=8.0, q=2.0)
    frequencies, response = eq_bands_response(48000, bands)
    assert len(bands) == len(EQ_FREQUENCIES) == 16
    assert response[np.argmin(np.abs(frequencies - 1200))] > 6.0

    narrow_bands = [dict(row) for row in bands]
    narrow_bands[8]["q"] = 6.0
    _, narrow_response = eq_bands_response(48000, narrow_bands)
    off_center = np.argmin(np.abs(frequencies - 1100))
    assert narrow_response[off_center] < response[off_center]

    source = np.zeros((1000, 2), dtype=np.float32)
    assert apply_eq_bands(source, 48000, bands).shape == source.shape


def test_bands_validate_rows_and_skip_above_nyquist():
    bands = _bands()
    bands[0].update(frequency=20000.0, gain_db=12.0)
    assert build_eq_sos_bands(16000, bands).shape == (0, 6)

    bands[3]["q"] = 0.0
    with pytest.raises(ValueError, match="Q 值"):
        eq_bands_response(48000, bands)
    with pytest.raises(ValueError, match="16 行"):
        eq_bands_response(48000, bands[:4])


def _fit_test_case():
    from filters.EQFilters import fit_bands_to_curve

    sample_rate = 48000
    grid = np.geomspace(20.0, 16000.0, 256)
    # 合成目标差值：低频架 +6 dB、3 kHz 峰 +5 dB、9 kHz 谷 -6 dB。
    desired = (
        6.0 / (1.0 + (grid / 150.0) ** 2)
        + 5.0 * np.exp(-0.5 * (np.log2(grid / 3000.0) / 0.35) ** 2)
        - 6.0 * np.exp(-0.5 * (np.log2(grid / 9000.0) / 0.45) ** 2)
    )
    bands = _bands()
    fitted, achieved = fit_bands_to_curve(sample_rate, grid, desired, bands)
    return fitted, desired, achieved


def test_fit_bands_to_curve_tracks_desired_response():
    fitted, desired, achieved = _fit_test_case()
    residual = achieved - desired
    assert np.sqrt(np.mean(residual ** 2)) < 1.0
    assert np.max(np.abs(residual)) < 2.5
    assert all(
        -15.0 <= band["gain_db"] <= 15.0 and band["frequency"] > 0
        for band in fitted
    )


def test_fit_bands_to_curve_clips_gains_to_spec_range():
    from filters.EQFilters import fit_bands_to_curve

    grid = np.geomspace(20.0, 16000.0, 256)
    fitted, achieved = fit_bands_to_curve(48000, grid, np.full_like(grid, 30.0), _bands())
    gains = [band["gain_db"] for band in fitted]
    # 超出能力的 30 dB 平坦目标下，增益必须全部限制在 ±15 dB 且确实触发上限。
    assert all(-15.0 <= gain <= 15.0 for gain in gains)
    assert max(gains) == 15.0
    # 叠加效应允许略超目标，但不应失控发散。
    assert achieved.max() < 35.0
