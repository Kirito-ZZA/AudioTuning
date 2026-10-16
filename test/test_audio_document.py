import json
import time

import numpy as np
from PyQt5.QtCore import QCoreApplication

from audio_engine import AudioDocument
from audio_io import load_audio, save_wav


def _make_source(path, sample_rate=16000):
    time_axis = np.arange(sample_rate // 4, dtype=np.float64) / sample_rate
    mono = (0.2 * np.sin(2 * np.pi * 1000 * time_axis)).astype(np.float32)
    source = np.column_stack((mono, mono * 0.5))
    save_wav(str(path), sample_rate, source)
    return source


def test_document_keeps_original_and_exports_both_versions(tmp_path):
    source_path = tmp_path / "source.wav"
    source = _make_source(source_path)
    document = AudioDocument("conf/algorithms.json")
    document.load(str(source_path))
    original = document.original.copy()
    document.set_parameter("gain", "gain_db", -6.0, process_async=False)
    document.set_gains([0.0] * 16)

    assert not document.original.flags.writeable
    assert np.allclose(document.original, original, atol=1e-6)
    assert not np.allclose(document.processed, document.original, atol=1e-3)

    original_path = tmp_path / "original.wav"
    processed_path = tmp_path / "processed.wav"
    document.save(str(original_path), "original")
    document.save(str(processed_path), "processed")
    original_rate, original_export = load_audio(original_path)
    processed_rate, processed_export = load_audio(processed_path)
    assert original_rate == processed_rate == 16000
    assert original_export.shape == processed_export.shape == source.shape
    assert np.allclose(original_export, original, atol=2e-4)
    document.shutdown()


def test_async_processing_discards_stale_parameter_result(tmp_path, monkeypatch):
    module_dir = tmp_path / "plugins"
    module_dir.mkdir()
    (module_dir / "slow_gain.py").write_text(
        "import time\n"
        "import numpy as np\n"
        "from filters.base import AudioAlgorithm, ParameterSpec\n"
        "class SlowGainAlgorithm(AudioAlgorithm):\n"
        "    algorithm_id = 'slow_gain'\n"
        "    display_name = 'Slow gain'\n"
        "    parameters = (ParameterSpec('gain', 'Gain', 1.0, 0.0, 4.0, 1.0),)\n"
        "    def process(self, data, sample_rate, params):\n"
        "        time.sleep(0.12)\n"
        "        return (np.asarray(data) * params['gain']).astype(np.float32)\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(module_dir))
    config_path = tmp_path / "algorithms.json"
    config_path.write_text(json.dumps({"algorithms": [{
        "module": "slow_gain",
        "class": "SlowGainAlgorithm",
        "order": 10,
        "enabled": True,
        "params": {"gain": 1.0},
    }]}), encoding="utf-8")

    app = QCoreApplication.instance() or QCoreApplication([])
    source_path = tmp_path / "source.wav"
    source = _make_source(source_path)
    document = AudioDocument(str(config_path))
    document.load(str(source_path))
    document.set_parameter("slow_gain", "gain", 2.0)
    document.set_parameter("slow_gain", "gain", 3.0)

    deadline = time.time() + 5.0
    while document.processing and time.time() < deadline:
        app.processEvents()
        time.sleep(0.005)
    app.processEvents()

    assert not document.processing
    expected = np.clip(source, -1.0, 1.0) * 3.0
    assert np.allclose(document.processed, expected, atol=2e-4)
    document.shutdown()
