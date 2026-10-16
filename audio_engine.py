"""Shared audio document, algorithm execution and compatibility exports."""

import logging
import os

import numpy as np
from PyQt5.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot

from audio_io import AudioError, PCMFormat, load_audio, save_wav
from filters.EQFilters import (
    EQ_FREQUENCIES, apply_eq_bands, apply_equalizer, build_eq_sos,
    build_eq_sos_bands, eq_bands_response, eq_response, peaking_sos,
)
from filters.registry import AlgorithmChain


class _WorkerSignals(QObject):
    succeeded = pyqtSignal(object)
    failed = pyqtSignal(str)


class _FunctionWorker(QRunnable):
    def __init__(self, function):
        super().__init__()
        self.function = function
        self.signals = _WorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
            self.signals.succeeded.emit(self.function())
        except Exception as exc:
            self.signals.failed.emit(str(exc))


class AudioDocument(QObject):
    """Single source of truth for audio data and the configured algorithm chain."""

    audio_changed = pyqtSignal()
    source_changed = pyqtSignal(str)
    busy_changed = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)
    warning_occurred = pyqtSignal(str)
    chain_changed = pyqtSignal()

    def __init__(self, config_path=None, parent=None, logger=None):
        super().__init__(parent)
        self.logger = logger or logging.getLogger(__name__)
        self.path = ""
        self.sample_rate = 0
        self.original = None
        self.processed = None
        self._busy_count = 0
        self._source_revision = 0
        self._process_revision = 0
        self._processing = False
        self._process_pending = False
        self._jobs = {}
        self._thread_pool = QThreadPool(self)
        self._thread_pool.setMaxThreadCount(2)

        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), "conf", "algorithms.json"
            )
        self.chain = AlgorithmChain(config_path, self.logger)
        try:
            self.chain.load()
        except AudioError as exc:
            self.chain.load_errors = [str(exc)]
            self.logger.exception(str(exc))

    @property
    def loaded(self):
        return self.original is not None

    @property
    def processing(self):
        return self._processing or self._process_pending

    @property
    def duration(self):
        if not self.loaded or not self.sample_rate:
            return 0.0
        return len(self.original) / float(self.sample_rate)

    @property
    def gains(self):
        try:
            bands = self.chain.get_slot("eq").params["bands"]
            return np.asarray([band["gain_db"] for band in bands], dtype=np.float32)
        except KeyError:
            return np.zeros(len(EQ_FREQUENCIES), dtype=np.float32)

    def _change_busy(self, delta):
        previous = self._busy_count
        self._busy_count = max(0, self._busy_count + delta)
        if previous == 0 and self._busy_count > 0:
            self.busy_changed.emit(True)
        elif previous > 0 and self._busy_count == 0:
            self.busy_changed.emit(False)

    def _start_job(self, kind, function, revision):
        worker = _FunctionWorker(function)
        signals = worker.signals
        self._jobs[signals] = (worker, kind, revision)
        signals.succeeded.connect(self._job_succeeded)
        signals.failed.connect(self._job_failed)
        self._change_busy(1)
        self._thread_pool.start(worker)

    @pyqtSlot(object)
    def _job_succeeded(self, result):
        job = self._jobs.pop(self.sender(), None)
        if job is None:
            return
        _, kind, revision = job
        try:
            if kind == "load":
                self._load_succeeded(revision, result)
            elif kind == "process":
                self._process_succeeded(revision, result)
        finally:
            self._change_busy(-1)

    @pyqtSlot(str)
    def _job_failed(self, message):
        job = self._jobs.pop(self.sender(), None)
        if job is None:
            return
        _, kind, revision = job
        try:
            if kind == "load" and revision == self._source_revision:
                self.error_occurred.emit(message)
            elif kind == "process":
                self._processing = False
                if revision == self._source_revision:
                    self.error_occurred.emit(message)
                self._start_pending_process()
        finally:
            self._change_busy(-1)

    @staticmethod
    def _validate_loaded_data(sample_rate, data):
        if int(sample_rate) <= 0 or data is None or not len(data):
            raise AudioError("音频文件中没有可处理的采样数据。")
        if data.ndim not in (1, 2):
            raise AudioError("音频数据必须是单声道或二维多声道数组。")

    def _set_source(self, path, sample_rate, data):
        self._validate_loaded_data(sample_rate, data)
        self.path = os.path.abspath(path)
        self.sample_rate = int(sample_rate)
        self.original = np.array(data, dtype=np.float32, copy=True)
        self.original.flags.writeable = False
        self.processed = np.array(self.original, copy=True)
        self.source_changed.emit(self.path)
        self.audio_changed.emit()

    def load(self, path, pcm_format=None):
        """Synchronously load and process audio, primarily for non-GUI callers."""
        self._source_revision += 1
        self._process_revision += 1
        self._process_pending = False
        sample_rate, data = load_audio(path, pcm_format)
        self._set_source(path, sample_rate, data)
        self.process_sync()

    def load_async(self, path, pcm_format=None):
        self._source_revision += 1
        self._process_revision += 1
        self._process_pending = False
        revision = self._source_revision
        path = os.path.abspath(path)

        def load():
            sample_rate, data = load_audio(path, pcm_format)
            self._validate_loaded_data(sample_rate, data)
            return path, sample_rate, data

        self._start_job("load", load, revision)

    def _load_succeeded(self, revision, result):
        if revision != self._source_revision:
            return
        path, sample_rate, data = result
        self._set_source(path, sample_rate, data)
        self.request_process()

    def request_process(self):
        if not self.loaded:
            return
        self._process_revision += 1
        self._process_pending = True
        self._start_pending_process()

    def _start_pending_process(self):
        if self._processing or not self._process_pending or not self.loaded:
            return
        self._process_pending = False
        self._processing = True
        source_revision = self._source_revision
        process_revision = self._process_revision
        original = self.original
        sample_rate = self.sample_rate
        snapshot = self.chain.snapshot()

        def process():
            result, errors = self.chain.process_with_errors(
                original, sample_rate, snapshot
            )
            return source_revision, process_revision, result, errors

        self._start_job("process", process, source_revision)

    def _process_succeeded(self, source_revision, result):
        self._processing = False
        result_source, process_revision, processed, errors = result
        if (
            result_source == self._source_revision
            and process_revision == self._process_revision
        ):
            self.processed = processed
            self.audio_changed.emit()
            for message in errors:
                self.warning_occurred.emit(message)
        self._start_pending_process()

    def process_sync(self):
        if not self.loaded:
            raise AudioError("请先打开音频文件。")
        self._process_revision += 1
        self._process_pending = False
        processed, errors = self.chain.process_with_errors(
            self.original, self.sample_rate
        )
        self.processed = processed
        self.audio_changed.emit()
        for message in errors:
            self.warning_occurred.emit(message)

    def set_enabled(self, algorithm_id, enabled, process_async=True):
        self.chain.set_enabled(algorithm_id, enabled)
        self.chain_changed.emit()
        if self.loaded:
            self.request_process() if process_async else self.process_sync()

    def set_parameter(self, algorithm_id, key, value, process_async=True):
        try:
            self.chain.set_parameter(algorithm_id, key, value)
        except (KeyError, ValueError) as exc:
            raise AudioError(str(exc)) from exc
        self.chain_changed.emit()
        if self.loaded:
            self.request_process() if process_async else self.process_sync()

    def set_gains(self, gains):
        """Compatibility wrapper for the original synchronous EQ API."""
        gains = np.asarray(gains, dtype=np.float32)
        if gains.shape != (len(EQ_FREQUENCIES),):
            raise AudioError("EQ 增益必须正好包含 16 段")
        bands = [dict(band) for band in self.chain.get_slot("eq").params["bands"]]
        for band, gain in zip(bands, gains):
            band["gain_db"] = float(gain)
        self.set_parameter("eq", "bands", bands, process_async=False)

    def reset_algorithms(self, process_async=True):
        self.chain.reset()
        self.chain_changed.emit()
        if self.loaded:
            self.request_process() if process_async else self.process_sync()

    def reload_algorithms(self):
        errors = self.chain.load()
        self.chain_changed.emit()
        for message in errors:
            self.warning_occurred.emit(message)
        if self.loaded:
            self.request_process()
        return errors

    def save_algorithms(self):
        self.chain.save()

    def audio_data(self, source="processed"):
        if not self.loaded:
            raise AudioError("请先打开音频文件。")
        if source == "original":
            return self.original
        if source != "processed":
            raise AudioError("未知音频来源：{}".format(source))
        if self.processing:
            raise AudioError("算法正在处理，请等待最新结果完成后再操作。")
        return self.processed

    def save(self, path, source="processed"):
        save_wav(path, self.sample_rate, self.audio_data(source))

    def shutdown(self):
        self._source_revision += 1
        self._process_revision += 1
        self._process_pending = False
        self._thread_pool.clear()
        self._thread_pool.waitForDone(5000)
