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
