import numpy as np
import pytest

from audio_io import AudioError, PCMFormat, load_audio, load_pcm


def test_signed_24bit_pcm_roundtrip_values(tmp_path):
    path = tmp_path / "stereo_24.pcm"
    values = np.array([
        [-8388608, 8388607],
        [0, -1],
        [1, 4194304],
    ], dtype=np.int32)
    packed = (values & 0xFFFFFF).astype(np.uint32)
    raw = np.stack((
        packed & 0xFF,
        (packed >> 8) & 0xFF,
        (packed >> 16) & 0xFF,
    ), axis=-1).astype(np.uint8)
    raw.tofile(str(path))

    sample_rate, loaded = load_pcm(
        path, PCMFormat(48000, channels=2, bit_depth=24, byte_order="little")
    )

    assert sample_rate == 48000
    assert loaded.shape == values.shape
    assert np.allclose(loaded, values.astype(np.float64) / (1 << 23), atol=1e-7)


def test_big_endian_unsigned_pcm_and_float_pcm(tmp_path):
    unsigned_path = tmp_path / "unsigned.pcm"
    np.array([0, 32768, 65535], dtype=">u2").tofile(str(unsigned_path))
    _, unsigned = load_pcm(
        unsigned_path,
        PCMFormat(16000, channels=1, bit_depth=16, byte_order="big", signed=False),
    )
    assert np.allclose(unsigned, [-1.0, 0.0, 32767.0 / 32768.0])

    float_path = tmp_path / "float.pcm"
    np.array([-0.5, 0.25, 0.75], dtype=">f4").tofile(str(float_path))
    _, floating = load_pcm(
        float_path,
        PCMFormat(16000, channels=1, bit_depth=32, byte_order="big", floating=True),
    )
    assert np.allclose(floating, [-0.5, 0.25, 0.75])


def test_pcm_requires_format_and_rejects_partial_frame(tmp_path):
    path = tmp_path / "broken.pcm"
    path.write_bytes(b"\x00\x01\x02")
    with pytest.raises(AudioError, match="必须明确"):
        load_audio(path)
    with pytest.raises(AudioError, match="完整采样帧"):
        load_pcm(path, PCMFormat(48000, channels=2, bit_depth=16))
    with pytest.raises(AudioError, match="浮点 PCM"):
        PCMFormat(bit_depth=16, floating=True).validate()
