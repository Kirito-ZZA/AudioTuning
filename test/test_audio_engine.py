import numpy as np

from audio_engine import (
    EQ_FREQUENCIES, apply_equalizer, eq_response, load_audio, save_wav,
)


def test_sixteen_band_equalizer_and_wav_roundtrip(tmp_path):
    sample_rate = 48000
    time = np.arange(sample_rate, dtype=np.float64) / sample_rate
    mono = 0.2 * np.sin(2 * np.pi * 1000 * time)
    source = np.column_stack((mono, mono * 0.8)).astype(np.float32)
    gains = np.zeros(len(EQ_FREQUENCIES), dtype=np.float32)
    gains[8] = 12.0

    processed = apply_equalizer(source, sample_rate, gains)
    frequencies, response = eq_response(sample_rate, gains)
    gain_at_1k = response[np.argmin(np.abs(frequencies - 1000))]

    assert len(EQ_FREQUENCIES) == 16
    assert processed.shape == source.shape
    assert np.isfinite(processed).all()
    assert gain_at_1k > 10.5

    output = tmp_path / "processed.wav"
    save_wav(str(output), sample_rate, processed)
    loaded_rate, loaded = load_audio(str(output))
    assert loaded_rate == sample_rate
    assert loaded.shape == source.shape

