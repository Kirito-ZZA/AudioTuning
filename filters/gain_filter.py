"""Digital gain algorithm plugin."""

import numpy as np

from filters.base import AudioAlgorithm, ParameterSpec


class GainAlgorithm(AudioAlgorithm):
    algorithm_id = "gain"
    display_name = "GAIN 增益"
    parameters = (
        ParameterSpec("gain_db", "增益", 0.0, -24.0, 24.0, 0.1, "dB"),
    )

    def process(self, data, sample_rate, params):
        factor = 10.0 ** (float(params["gain_db"]) / 20.0)
        return (np.asarray(data, dtype=np.float64) * factor).astype(np.float32)
