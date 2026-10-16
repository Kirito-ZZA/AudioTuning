"""Base classes and parameter validation for audio algorithm plugins."""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ParameterSpec:
    key: str
    label: str
    default: object
    minimum: float
    maximum: float
    step: float = 1.0
    unit: str = ""
    kind: str = "float"
    labels: tuple = ()
    columns: tuple = ()

    def default_value(self):
        if self.kind == "table":
            return self.coerce(self.default)
        if self.kind == "float_list":
            return [float(value) for value in self.default]
        if self.kind == "int":
            return int(self.default)
        return float(self.default)

    def coerce(self, value):
        if self.kind == "table":
            return self._coerce_table(value)
        if self.kind == "float_list":
            try:
                values = list(value)
            except TypeError as exc:
                raise ValueError("{} 必须是数值列表".format(self.label)) from exc
            if self.labels and len(values) != len(self.labels):
                raise ValueError("{} 必须包含 {} 项".format(self.label, len(self.labels)))
            return [self._coerce_number(item, float) for item in values]
        if self.kind == "int":
            return self._coerce_number(value, int)
        return self._coerce_number(value, float)

    def _coerce_table(self, value):
        if not self.columns:
            raise ValueError("{} 缺少表格列定义".format(self.label))
        try:
            rows = list(value)
        except TypeError as exc:
            raise ValueError("{} 必须是表格行列表".format(self.label)) from exc
        if self.labels and len(rows) != len(self.labels):
            raise ValueError("{} 必须包含 {} 行".format(self.label, len(self.labels)))
        normalized = []
        for row_index, row in enumerate(rows):
            normalized_row = {}
            for column in self.columns:
                try:
                    if isinstance(row, dict):
                        cell = row[column.key]
                    else:
                        values = list(row)
                        if len(values) != len(self.columns):
                            raise ValueError("列数不匹配")
                        cell = values[self.columns.index(column)]
                    normalized_row[column.key] = column.coerce(cell)
                except (KeyError, TypeError, ValueError) as exc:
                    raise ValueError(
                        "{} 第 {} 行 {} 无效：{}".format(
                            self.label, row_index + 1, column.label, exc
                        )
                    ) from exc
            normalized.append(normalized_row)
        return normalized

    def _coerce_number(self, value, converter):
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("{} 必须是数值".format(self.label)) from exc
        if not np.isfinite(number):
            raise ValueError("{} 必须是有限数值".format(self.label))
        if number < self.minimum or number > self.maximum:
            raise ValueError(
                "{} 必须在 {} 到 {} 之间".format(self.label, self.minimum, self.maximum)
            )
        if converter is int and number != int(number):
            raise ValueError("{} 必须是整数".format(self.label))
        return converter(number)


class AudioAlgorithm:
    algorithm_id = ""
    display_name = ""
    parameters = ()

    @classmethod
    def default_parameters(cls):
        return {spec.key: spec.default_value() for spec in cls.parameters}

    @classmethod
    def parameter_spec(cls, key):
        for spec in cls.parameters:
            if spec.key == key:
                return spec
        raise KeyError("算法 {} 不存在参数 {}".format(cls.display_name, key))

    def process(self, data, sample_rate, params):
        raise NotImplementedError
