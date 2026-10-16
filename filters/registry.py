"""JSON-configured dynamic audio algorithm chain."""

import copy
import importlib
import json
import logging
import os
from pathlib import Path

import numpy as np

from audio_io import AudioError
from filters.base import AudioAlgorithm


class AlgorithmSlot:
    def __init__(self, algorithm, enabled=True, order=0, params=None):
        self.algorithm = algorithm
        self.enabled = bool(enabled)
        self.order = float(order)
        self.params = algorithm.default_parameters()
        for key, value in (params or {}).items():
            try:
                spec = algorithm.parameter_spec(key)
                self.params[key] = spec.coerce(value)
            except (KeyError, ValueError):
                continue

    @property
    def algorithm_id(self):
        return self.algorithm.algorithm_id

    @property
    def display_name(self):
        return self.algorithm.display_name


class AlgorithmChain:
    def __init__(self, config_path=None, logger=None):
        self.config_path = os.path.abspath(config_path) if config_path else ""
        self.logger = logger or logging.getLogger(__name__)
        self.slots = []
        self.load_errors = []

    def load(self, config_path=None):
        if config_path:
            self.config_path = os.path.abspath(config_path)
        if not self.config_path:
            raise AudioError("未指定算法链配置文件。")
        try:
            with open(self.config_path, "r", encoding="utf-8") as handle:
                content = json.load(handle)
            entries = content["algorithms"]
            if not isinstance(entries, list):
                raise TypeError("algorithms 必须是列表")
        except Exception as exc:
            raise AudioError("算法配置读取失败：{}".format(exc)) from exc

        slots = []
        errors = []
        identifiers = set()
        for index, entry in enumerate(entries):
            try:
                module = importlib.import_module(entry["module"])
                algorithm_class = getattr(module, entry["class"])
                if not issubclass(algorithm_class, AudioAlgorithm):
                    raise TypeError("算法类必须继承 AudioAlgorithm")
                algorithm = algorithm_class()
                if not algorithm.algorithm_id or algorithm.algorithm_id in identifiers:
                    raise ValueError("算法 ID 为空或重复")
                enabled = entry.get("enabled", True)
                if not isinstance(enabled, bool):
                    raise TypeError("enabled 必须是布尔值")
                params = self._validated_params(algorithm, entry.get("params", {}), errors)
                slot = AlgorithmSlot(
                    algorithm,
                    enabled=enabled,
                    order=entry.get("order", (index + 1) * 10),
                    params=params,
                )
                slots.append(slot)
                identifiers.add(algorithm.algorithm_id)
            except Exception as exc:
                message = "算法配置第 {} 项加载失败：{}".format(index + 1, exc)
                self.logger.exception(message)
                errors.append(message)
        self.slots = sorted(slots, key=lambda item: item.order)
        self.load_errors = errors
        return errors

    def _validated_params(self, algorithm, configured, errors):
        if not isinstance(configured, dict):
            errors.append("{} 的 params 不是字典，已使用默认参数".format(algorithm.display_name))
            return algorithm.default_parameters()
        params = algorithm.default_parameters()
        for key, value in configured.items():
            try:
                params[key] = algorithm.parameter_spec(key).coerce(value)
            except (KeyError, ValueError) as exc:
                message = "{} 参数 {} 无效，已使用默认值：{}".format(
                    algorithm.display_name, key, exc
                )
                self.logger.warning(message)
                errors.append(message)
        return params

    def snapshot(self):
        return tuple(
            (slot.algorithm, copy.deepcopy(slot.params))
            for slot in self.slots
            if slot.enabled
        )

    def process(self, data, sample_rate, snapshot=None):
        return self.process_with_errors(data, sample_rate, snapshot)[0]

    def process_with_errors(self, data, sample_rate, snapshot=None):
        result = np.array(data, dtype=np.float32, copy=True)
        errors = []
        operations = snapshot if snapshot is not None else self.snapshot()
        for algorithm, params in operations:
            try:
                output = algorithm.process(result, int(sample_rate), copy.deepcopy(params))
                output = np.asarray(output, dtype=np.float32)
                if output.shape != result.shape:
                    raise AudioError(
                        "{} 改变了音频数据形状：{} -> {}".format(
                            algorithm.display_name, result.shape, output.shape
                        )
                    )
                if not np.isfinite(output).all():
                    raise AudioError("{} 输出了 NaN 或 Inf".format(algorithm.display_name))
                result = output
            except Exception as exc:
                message = "算法 {} 处理失败，已跳过：{}".format(algorithm.display_name, exc)
                self.logger.exception(message)
                errors.append(message)
        return result, errors

    def get_slot(self, algorithm_id):
        for slot in self.slots:
            if slot.algorithm_id == algorithm_id:
                return slot
        raise KeyError("未找到算法：{}".format(algorithm_id))

    def set_enabled(self, algorithm_id, enabled):
        self.get_slot(algorithm_id).enabled = bool(enabled)

    def set_parameter(self, algorithm_id, key, value):
        slot = self.get_slot(algorithm_id)
        slot.params[key] = slot.algorithm.parameter_spec(key).coerce(value)

    def reset(self):
        for slot in self.slots:
            slot.params = slot.algorithm.default_parameters()

    def save(self, config_path=None):
        target = Path(config_path or self.config_path)
        if not str(target):
            raise AudioError("未指定算法配置保存路径。")
        entries = []
        for slot in self.slots:
            algorithm = slot.algorithm
            entries.append({
                "module": algorithm.__class__.__module__,
                "class": algorithm.__class__.__name__,
                "order": slot.order,
                "enabled": slot.enabled,
                "params": slot.params,
            })
        temporary = target.with_suffix(target.suffix + ".tmp")
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(temporary, "w", encoding="utf-8") as handle:
                json.dump({"version": 1, "algorithms": entries}, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
            os.replace(str(temporary), str(target))
        except Exception as exc:
            try:
                if temporary.exists():
                    temporary.unlink()
            except OSError:
                pass
            raise AudioError("算法配置保存失败：{}".format(exc)) from exc
