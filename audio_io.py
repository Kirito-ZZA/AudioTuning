"""Audio file I/O and PCM conversion without GUI dependencies."""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.io import wavfile


class AudioError(RuntimeError):
    pass


@dataclass(frozen=True)
class PCMFormat:
    sample_rate: int = 48000
    channels: int = 1
    bit_depth: int = 16
    byte_order: str = "little"
    signed: bool = True
    floating: bool = False

    def validate(self):
        if not 1 <= int(self.sample_rate) <= 768000:
            raise AudioError("PCM 采样率必须在 1 到 768000 Hz 之间。")
        if not 1 <= int(self.channels) <= 64:
            raise AudioError("PCM 声道数必须在 1 到 64 之间。")
        if self.bit_depth not in (8, 16, 24, 32):
            raise AudioError("PCM 位深仅支持 8、16、24、32 位。")
        if self.byte_order not in ("little", "big"):
            raise AudioError("PCM 字节序仅支持 little 或 big。")
        if self.floating and self.bit_depth != 32:
            raise AudioError("浮点 PCM 当前仅支持 32 位格式。")
        if self.bit_depth == 8 and self.byte_order != "little":
            raise AudioError("8 位 PCM 不区分字节序，请选择 little。")
        return self

    @property
    def frame_width(self):
        return self.channels * self.bit_depth // 8


def pcm_to_float(data, bit_depth=None):
    data = np.asarray(data)
    if np.issubdtype(data.dtype, np.floating):
        return np.clip(data.astype(np.float32), -1.0, 1.0)

    bits = int(bit_depth or data.dtype.itemsize * 8)
    scale = float(1 << (bits - 1))
    if np.issubdtype(data.dtype, np.unsignedinteger):
        converted = (data.astype(np.float64) - scale) / scale
    elif np.issubdtype(data.dtype, np.signedinteger):
        converted = data.astype(np.float64) / scale
    else:
        raise AudioError("不支持的 PCM 数据格式：{}".format(data.dtype))
    return np.clip(converted.astype(np.float32), -1.0, 1.0)


def float_to_pcm16(data):
    safe = np.nan_to_num(data, nan=0.0, posinf=1.0, neginf=-1.0)
    return np.round(np.clip(safe, -1.0, 1.0) * 32767.0).astype(np.int16)


def _read_pcm24(path, pcm_format):
    raw = np.fromfile(str(path), dtype=np.uint8)
    if raw.size % pcm_format.frame_width:
        raise AudioError("PCM 文件大小不是完整采样帧的整数倍，请检查位深和声道数。")
    frames = raw.reshape((-1, pcm_format.channels, 3)).astype(np.uint32)
    if pcm_format.byte_order == "little":
        values = frames[..., 0] | (frames[..., 1] << 8) | (frames[..., 2] << 16)
    else:
        values = frames[..., 2] | (frames[..., 1] << 8) | (frames[..., 0] << 16)
    if pcm_format.signed:
        values = (values ^ np.uint32(0x800000)).astype(np.int64) - 0x800000
        scale = float(1 << 23)
        normalized = values.astype(np.float64) / scale
    else:
        normalized = (values.astype(np.float64) - float(1 << 23)) / float(1 << 23)
    mono_shape = normalized.reshape(-1, pcm_format.channels)
    if pcm_format.channels == 1:
        return mono_shape[:, 0].astype(np.float32)
    return np.clip(mono_shape.astype(np.float32), -1.0, 1.0)


def load_pcm(path, pcm_format):
    pcm_format.validate()
    path = Path(path)
    try:
        if pcm_format.bit_depth == 24 and not pcm_format.floating:
            return pcm_format.sample_rate, _read_pcm24(path, pcm_format)

        kind = "f" if pcm_format.floating else ("i" if pcm_format.signed else "u")
        width = pcm_format.bit_depth // 8
        if width == 1:
            dtype = np.dtype("{}{}".format(kind, width))
        else:
            endian = "<" if pcm_format.byte_order == "little" else ">"
            dtype = np.dtype("{}{}{}".format(endian, kind, width))
        data = np.fromfile(str(path), dtype=dtype)
        if data.size % pcm_format.channels:
            raise AudioError("PCM 文件大小不是完整采样帧的整数倍，请检查位深和声道数。")
        if pcm_format.channels > 1:
            data = data.reshape((-1, pcm_format.channels))
        return pcm_format.sample_rate, pcm_to_float(data, pcm_format.bit_depth)
    except AudioError:
        raise
    except Exception as exc:
        raise AudioError("PCM 文件读取失败：{}".format(exc)) from exc


def load_audio(path, pcm_format=None):
    """Return (sample_rate, float32 samples), preserving the channel count."""
    suffix = Path(path).suffix.lower()
    if suffix == ".wav":
        try:
            sample_rate, data = wavfile.read(path)
            return int(sample_rate), pcm_to_float(data)
        except Exception as exc:
            raise AudioError("WAV 文件读取失败：{}".format(exc)) from exc

    if suffix in (".pcm", ".raw"):
        if pcm_format is None:
            raise AudioError("读取原始 PCM 前必须明确采样率、声道数、位深和编码格式。")
        return load_pcm(path, pcm_format)

    try:
        from pydub import AudioSegment

        segment = AudioSegment.from_file(path)
        raw = np.asarray(segment.get_array_of_samples())
        if segment.channels > 1:
            raw = raw.reshape((-1, segment.channels))
        scale = float(1 << (8 * segment.sample_width - 1))
        data = np.clip(raw.astype(np.float64) / scale, -1.0, 1.0)
        return int(segment.frame_rate), data.astype(np.float32)
    except ImportError as exc:
        raise AudioError("读取非 WAV/PCM 文件需要安装 pydub，并配置 ffmpeg。") from exc
    except Exception as exc:
        raise AudioError("音频解码失败，请检查格式或 ffmpeg 配置：{}".format(exc)) from exc


def save_wav(path, sample_rate, data):
    if int(sample_rate) <= 0:
        raise AudioError("保存音频时采样率必须大于 0。")
    try:
        wavfile.write(path, int(sample_rate), float_to_pcm16(data))
    except Exception as exc:
        raise AudioError("音频保存失败：{}".format(exc)) from exc
