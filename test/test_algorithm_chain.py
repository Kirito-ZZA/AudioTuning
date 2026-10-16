import json

import numpy as np
import pytest

from filters.act import ACTAlgorithm
from filters.registry import AlgorithmChain


def test_default_chain_order_enable_and_parameter_validation():
    chain = AlgorithmChain("conf/algorithms.json")
    assert chain.load() == []
    assert [slot.algorithm_id for slot in chain.slots] == ["gain", "eq", "act"]
    source = np.full((1000, 2), 0.1, dtype=np.float32)

    chain.set_parameter("gain", "gain_db", 6.0)
    amplified = chain.process(source, 48000)
    assert amplified.shape == source.shape
    assert np.allclose(amplified, source * (10.0 ** (6.0 / 20.0)), rtol=1e-5)

    chain.set_enabled("gain", False)
    assert np.array_equal(chain.process(source, 48000), source)
    with pytest.raises(ValueError, match="必须在"):
        chain.set_parameter("gain", "gain_db", 100.0)
    with pytest.raises(ValueError, match="16"):
        chain.set_parameter("eq", "bands", [0.0] * 4)


def test_dynamic_configuration_skips_broken_plugin_and_saves(tmp_path):
    config_path = tmp_path / "algorithms.json"
    config_path.write_text(json.dumps({
        "algorithms": [
            {
                "module": "filters.gain_filter",
                "class": "GainAlgorithm",
                "order": 20,
                "enabled": True,
                "params": {"gain_db": -3.0},
            },
            {
                "module": "filters.does_not_exist",
                "class": "MissingAlgorithm",
                "order": 10,
            },
        ]
    }), encoding="utf-8")
    chain = AlgorithmChain(str(config_path))
    errors = chain.load()

    assert len(errors) == 1
    assert [slot.algorithm_id for slot in chain.slots] == ["gain"]
    assert chain.get_slot("gain").params["gain_db"] == -3.0
    chain.set_parameter("gain", "gain_db", -6.0)
    chain.save()
    saved = json.loads(config_path.read_text(encoding="utf-8"))
    assert saved["algorithms"][0]["params"]["gain_db"] == -6.0


def test_act_compresses_loud_signal_and_preserves_quiet_signal():
    sample_rate = 16000
    time = np.arange(sample_rate, dtype=np.float64) / sample_rate
    algorithm = ACTAlgorithm()
    params = algorithm.default_parameters()
    params.update({
        "threshold_db": -20.0,
        "ratio": 4.0,
        "knee_db": 0.0,
        "attack_ms": 1.0,
        "release_ms": 20.0,
        "ceiling_db": -1.0,
    })
    loud = (0.8 * np.sin(2 * np.pi * 1000 * time)).astype(np.float32)
    compressed = algorithm.process(loud, sample_rate, params)

    assert compressed.shape == loud.shape
    assert np.isfinite(compressed).all()
    assert np.sqrt(np.mean(compressed[8000:] ** 2)) < np.sqrt(np.mean(loud[8000:] ** 2)) * 0.7
    assert np.max(np.abs(compressed)) <= 10.0 ** (-1.0 / 20.0) + 1e-6

    quiet = (0.05 * np.sin(2 * np.pi * 1000 * time)).astype(np.float32)
    quiet_params = dict(params, threshold_db=-12.0, ceiling_db=0.0)
    assert np.allclose(algorithm.process(quiet, sample_rate, quiet_params), quiet, atol=1e-6)

    stereo = np.column_stack((loud, loud * 0.5))
    assert algorithm.process(stereo, sample_rate, params).shape == stereo.shape
