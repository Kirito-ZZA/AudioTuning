"""ACT dynamics compressor and output limiter."""

import numpy as np

from filters.base import AudioAlgorithm, ParameterSpec


class ACTAlgorithm(AudioAlgorithm):
    algorithm_id = "act"
    display_name = "ACT 动态压缩/限制"
    parameters = (
        ParameterSpec("threshold_db", "压缩阈值", -18.0, -60.0, 0.0, 0.1, "dBFS"),
        ParameterSpec("ratio", "压缩比", 4.0, 1.0, 20.0, 0.1, ":1"),
        ParameterSpec("knee_db", "软拐点", 6.0, 0.0, 12.0, 0.1, "dB"),
        ParameterSpec("attack_ms", "启动时间", 10.0, 0.1, 100.0, 0.1, "ms"),
        ParameterSpec("release_ms", "释放时间", 100.0, 1.0, 1000.0, 1.0, "ms"),
        ParameterSpec("makeup_db", "补偿增益", 0.0, 0.0, 24.0, 0.1, "dB"),
        ParameterSpec("ceiling_db", "输出限制", -1.0, -12.0, 0.0, 0.1, "dBFS"),
    )

    def process(self, data, sample_rate, params):
        samples = np.asarray(data, dtype=np.float64)
        attack = np.exp(-1.0 / (sample_rate * float(params["attack_ms"]) / 1000.0))
        release = np.exp(-1.0 / (sample_rate * float(params["release_ms"]) / 1000.0))
        makeup = 10.0 ** (float(params["makeup_db"]) / 20.0)
        ceiling = 10.0 ** (float(params["ceiling_db"]) / 20.0)
        if samples.ndim == 1:
            return self._process_channel(
                samples, sample_rate, params, attack, release, makeup, ceiling
            ).astype(np.float32)
        channels = [
            self._process_channel(
                samples[:, index], sample_rate, params, attack, release, makeup, ceiling
            )
            for index in range(samples.shape[1])
        ]
        return np.column_stack(channels).astype(np.float32)

    @staticmethod
    def _process_channel(samples, sample_rate, params, attack, release, makeup, ceiling):
        level_db = 20.0 * np.log10(np.maximum(np.abs(samples), 1e-12))
        threshold = float(params["threshold_db"])
        ratio = float(params["ratio"])
        knee = float(params["knee_db"])
        over = level_db - threshold
        reduction_db = np.zeros_like(level_db)
        slope = 1.0 - 1.0 / ratio
        if knee > 0.0:
            above = over >= knee / 2.0
            within = np.abs(over) < knee / 2.0
            reduction_db[above] = -slope * over[above]
            reduction_db[within] = (
                -slope * (over[within] + knee / 2.0) ** 2 / (2.0 * knee)
            )
        else:
            active = over > 0.0
            reduction_db[active] = -slope * over[active]
        targets = 10.0 ** (reduction_db / 20.0)

        smoothed = np.empty_like(targets)
        current = 1.0
        for index in range(len(targets)):
            target = float(targets[index])
            coefficient = attack if target < current else release
            current = coefficient * current + (1.0 - coefficient) * target
            smoothed[index] = current
        processed = samples * smoothed * makeup
        return np.clip(processed, -ceiling, ceiling)
