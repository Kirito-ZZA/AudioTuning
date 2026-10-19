"""Audio processing, playback and comparison pages."""

import os
import tempfile

import numpy as np
import pyqtgraph as pg
from PyQt5.QtCore import Qt, QTimer, QUrl
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFileDialog,
    QFormLayout, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QHeaderView,
    QLabel, QMessageBox, QScrollArea, QSizePolicy, QSpinBox, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

import config as settings
import theme
from audio_analysis import (
    available_targets, calculate_spectrum, plot_samples, smoothed_response,
    target_response,
)
from audio_engine import AudioError, PCMFormat, eq_bands_response, save_wav
from filters.EQFilters import fit_bands_to_curve


# 曲线颜色为业务约定，不随主题切换
ORIGINAL_COLOR = "#00ae00"
PROCESSED_COLOR = "#197ccc"
TARGET_COLOR = "#eb6100"


def _style_plot(plot):
    """绘图区跟随全局主题；只改底色、坐标轴和文字，不动曲线颜色。"""
    plot.setBackground(theme.color("plot_bg"))
    for axis_name in ("left", "bottom"):
        axis = plot.getAxis(axis_name)
        axis.setPen(pg.mkPen(theme.color("plot_axis")))
        axis.setTextPen(pg.mkPen(theme.color("plot_text")))


def _plot_label_color():
    return theme.color("plot_label")


class PCMFormatDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("原始 PCM 格式")
        layout = QFormLayout(self)
        self.sample_rate = QSpinBox()
        self.sample_rate.setRange(1, 768000)
        self.sample_rate.setValue(48000)
        self.channels = QSpinBox()
        self.channels.setRange(1, 64)
        self.bit_depth = QComboBox()
        for value in (8, 16, 24, 32):
            self.bit_depth.addItem("{} 位".format(value), value)
        self.bit_depth.setCurrentIndex(1)
        self.byte_order = QComboBox()
        self.byte_order.addItem("小端（little-endian）", "little")
        self.byte_order.addItem("大端（big-endian）", "big")
        self.encoding = QComboBox()
        self.encoding.addItem("有符号整数", "signed")
        self.encoding.addItem("无符号整数", "unsigned")
        self.encoding.addItem("32 位浮点", "float")
        layout.addRow("采样率（Hz）", self.sample_rate)
        layout.addRow("声道数", self.channels)
        layout.addRow("位深", self.bit_depth)
        layout.addRow("字节序", self.byte_order)
        layout.addRow("编码", self.encoding)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("确定")
        buttons.button(QDialogButtonBox.Cancel).setText("取消")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        self.bit_depth.currentIndexChanged.connect(self._format_changed)
        self.encoding.currentIndexChanged.connect(self._encoding_changed)

    def _format_changed(self):
        is_8bit = self.bit_depth.currentData() == 8
        self.byte_order.setEnabled(not is_8bit)
        if is_8bit:
            self.byte_order.setCurrentIndex(0)
        if self.bit_depth.currentData() != 32 and self.encoding.currentData() == "float":
            self.encoding.setCurrentIndex(0)

    def _encoding_changed(self):
        if self.encoding.currentData() == "float":
            self.bit_depth.setCurrentIndex(3)

    def pcm_format(self):
        return PCMFormat(
            sample_rate=self.sample_rate.value(),
            channels=self.channels.value(),
            bit_depth=self.bit_depth.currentData(),
            byte_order=self.byte_order.currentData(),
            signed=self.encoding.currentData() != "unsigned",
            floating=self.encoding.currentData() == "float",
        )

    def accept(self):
        try:
            self.pcm_format().validate()
        except AudioError as exc:
            QMessageBox.warning(self, "PCM 参数无效", str(exc))
            return
        super().accept()


class SelectAllDoubleSpinBox(QDoubleSpinBox):
    """聚焦时全选文本的数值框。

    点击后直接输入即整体替换，避免光标落在小数位导致数字被吞
    （例如想输入 10 时 0 落到小数位，数值不变）；关闭键盘跟踪，
    输入过程的中间值不触发参数应用，回车或失焦才提交。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setKeyboardTracking(False)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.selectAll()

    def mousePressEvent(self, event):
        # 鼠标点击会先移动光标，必须在点击处理之后再全选，
        # 否则快速输入时选区被光标覆盖、数字仍可能落入小数位。
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            self.selectAll()


class AudioProcessingPage(QFrame):
    def __init__(self, document, parent=None):
        super().__init__(parent)
        self.document = document
        self.preview_path = None
        self.preview_source = None
        self.player = QMediaPlayer(self)
        self.apply_timer = QTimer(self)
        self.apply_timer.setSingleShot(True)
        self.apply_timer.setInterval(220)
        self.apply_timer.timeout.connect(self._flush_parameters)
        self._pending_parameters = {}
        self._parameter_controls = []
        self._slot_groups = {}
        self._eq_table = None
        # 由 Center 注入：返回 (目标曲线 key, 显示名)，用于“目标曲线拟合”。
        self.fit_target_provider = None
        self._build_ui()
        self._rebuild_algorithm_controls()
        self.document.audio_changed.connect(self.refresh_audio)
        self.document.source_changed.connect(self._source_changed)
        self.document.busy_changed.connect(self._busy_changed)
        self.document.error_occurred.connect(self._show_error)
        self.document.warning_occurred.connect(self.status_label.setText)
        self.document.chain_changed.connect(self.refresh_response)
        self.player.stateChanged.connect(self._player_state_changed)
        self._emit_control_state()
        if self.document.chain.load_errors:
            self.status_label.setText(self.document.chain.load_errors[-1])

    def _build_ui(self):
        root = QVBoxLayout(self)
        self.file_label = QLabel("尚未打开音频文件；请使用 Header 的“文件 → 打开...”")
        self.file_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        root.addWidget(self.file_label)
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: %s;" % theme.color("text_dim"))
        root.addWidget(self.status_label)

        self.response_plot = pg.PlotWidget(title="当前 EQ 频率响应（ACT 为非线性动态处理）")
        _style_plot(self.response_plot)
        self.response_plot.setLabel("bottom", "频率", units="Hz", color=_plot_label_color())
        self.response_plot.setLabel("left", "增益", units="dB", color=_plot_label_color())
        self.response_plot.setLogMode(x=True, y=False)
        self.response_plot.showGrid(x=True, y=True, alpha=0.25)
        self.response_curve = self.response_plot.plot(pen=pg.mkPen(TARGET_COLOR, width=2))
        root.addWidget(self.response_plot, 1)

        self.algorithm_scroll = QScrollArea()
        self.algorithm_scroll.setWidgetResizable(True)
        root.addWidget(self.algorithm_scroll, 2)

    def _rebuild_algorithm_controls(self):
        self._pending_parameters.clear()
        self.apply_timer.stop()
        self._parameter_controls = []
        self._slot_groups = {}
        self._eq_table = None
        host = QWidget()
        layout = QHBoxLayout(host)
        table_column = QVBoxLayout()
        scalar_column = QVBoxLayout()
        layout.addLayout(table_column, 3)
        layout.addLayout(scalar_column, 2)

        for slot in self.document.chain.slots:
            group = QGroupBox(slot.display_name)
            group.setCheckable(True)
            group.setChecked(slot.enabled)
            group.toggled.connect(
                lambda checked, algorithm_id=slot.algorithm_id: self._enabled_changed(
                    algorithm_id, checked
                )
            )
            has_table = any(
                spec.kind in ("table", "float_list") for spec in slot.algorithm.parameters
            )
            group_layout = QVBoxLayout(group) if has_table else QGridLayout(group)
            scalar_index = 0
            for spec in slot.algorithm.parameters:
                if spec.kind == "table":
                    control = self._make_table_control(group_layout, slot, spec)
                elif spec.kind == "float_list":
                    control = self._make_list_control(group_layout, slot, spec)
                else:
                    control = self._make_scalar_control(
                        group_layout, slot, spec, scalar_index
                    )
                    scalar_index += 1
                self._parameter_controls.append((slot.algorithm_id, spec, control))
            if has_table:
                table_column.addWidget(group)
            else:
                scalar_column.addWidget(group)
            self._slot_groups[slot.algorithm_id] = group
        table_column.addStretch(1)
        scalar_column.addStretch(1)
        self.algorithm_scroll.setWidget(host)
        self.refresh_response()

    def _make_table_control(self, parent_layout, slot, spec):
        values = slot.params[spec.key]
        table = QTableWidget(len(values), len(spec.columns) + 1)
        table.setObjectName("EQBandTable" if slot.algorithm_id == "eq" else "ParameterTable")
        table.setHorizontalHeaderLabels(["频段"] + [column.label for column in spec.columns])
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(25)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setAlternatingRowColors(True)
        table.setMinimumHeight(430)
        table.setMinimumWidth(520)
        spins = []
        for row, row_values in enumerate(values):
            label = spec.labels[row] if row < len(spec.labels) else str(row + 1)
            item = QTableWidgetItem(label)
            item.setFlags(Qt.ItemIsEnabled)
            table.setItem(row, 0, item)
            row_spins = []
            for column_index, column in enumerate(spec.columns):
                spin = self._make_spin(column, row_values[column.key])
                spin.valueChanged.connect(
                    lambda value, algorithm_id=slot.algorithm_id, key=spec.key,
                           row_index=row, column_key=column.key:
                        self._table_value_changed(
                            algorithm_id, key, row_index, column_key, value
                        )
                )
                table.setCellWidget(row, column_index + 1, spin)
                row_spins.append(spin)
            spins.append(row_spins)
        parent_layout.addWidget(table)
        if slot.algorithm_id == "eq":
            self._eq_table = table
        return spins

    def _make_list_control(self, parent_layout, slot, spec):
        values = slot.params[spec.key]
        table = QTableWidget(len(values), 2)
        table.setHorizontalHeaderLabels(["项目", spec.label])
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        spins = []
        for row, value in enumerate(values):
            label = spec.labels[row] if row < len(spec.labels) else str(row + 1)
            table.setItem(row, 0, QTableWidgetItem(label))
            spin = self._make_spin(spec, value)
            spin.valueChanged.connect(
                lambda new_value, algorithm_id=slot.algorithm_id,
                       key=spec.key, row_index=row:
                    self._list_value_changed(algorithm_id, key, row_index, new_value)
            )
            table.setCellWidget(row, 1, spin)
            spins.append(spin)
        parent_layout.addWidget(table)
        return spins

    @staticmethod
    def _make_spin(spec, value):
        spin = SelectAllDoubleSpinBox()
        spin.setRange(spec.minimum, spec.maximum)
        spin.setSingleStep(spec.step)
        decimals = 0 if spec.step >= 1 else min(3, int(np.ceil(-np.log10(spec.step))))
        spin.setDecimals(decimals)
        spin.setSuffix(" {}".format(spec.unit) if spec.unit else "")
        spin.setValue(value)
        spin.setMaximumWidth(130)
        return spin

    def _make_scalar_control(self, parent_layout, slot, spec, index):
        spin = self._make_spin(spec, slot.params[spec.key])
        spin.valueChanged.connect(
            lambda value, algorithm_id=slot.algorithm_id, key=spec.key:
                self._scalar_value_changed(algorithm_id, key, value)
        )
        row, pair = divmod(index, 2)
        parent_layout.addWidget(QLabel(spec.label), row, pair * 2)
        parent_layout.addWidget(spin, row, pair * 2 + 1)
        return spin

    def _table_value_changed(self, algorithm_id, key, row, column, value):
        slot = self.document.chain.get_slot(algorithm_id)
        pending = [
            dict(item) for item in self._pending_parameters.get(
                (algorithm_id, key), slot.params[key]
            )
        ]
        pending[row][column] = value
        self._pending_parameters[(algorithm_id, key)] = pending
        self._schedule_apply()

    def _list_value_changed(self, algorithm_id, key, index, value):
        slot = self.document.chain.get_slot(algorithm_id)
        pending = list(self._pending_parameters.get((algorithm_id, key), slot.params[key]))
        pending[index] = value
        self._pending_parameters[(algorithm_id, key)] = pending
        self._schedule_apply()

    def _scalar_value_changed(self, algorithm_id, key, value):
        self._pending_parameters[(algorithm_id, key)] = value
        self._schedule_apply()

    def _schedule_apply(self):
        if self.document.loaded:
            self.apply_timer.start()
        else:
            self._flush_parameters()
        self._emit_control_state()

    def _flush_parameters(self):
        self.apply_timer.stop()
        pending = dict(self._pending_parameters)
        self._pending_parameters.clear()
        for (algorithm_id, key), value in pending.items():
            try:
                self.document.set_parameter(algorithm_id, key, value)
            except AudioError as exc:
                self.status_label.setText(str(exc))
        self._emit_control_state()

    def _enabled_changed(self, algorithm_id, enabled):
        self._flush_parameters()
        try:
            self.document.set_enabled(algorithm_id, enabled)
        except (AudioError, KeyError) as exc:
            self.status_label.setText(str(exc))
        self._emit_control_state()

    def _sync_algorithm_controls(self):
        for group in self._slot_groups.values():
            group.blockSignals(True)
        for slot in self.document.chain.slots:
            group = self._slot_groups.get(slot.algorithm_id)
            if group is not None:
                group.setChecked(slot.enabled)
        for algorithm_id, spec, control in self._parameter_controls:
            value = self.document.chain.get_slot(algorithm_id).params[spec.key]
            if spec.kind == "table":
                for row, row_spins in enumerate(control):
                    for column, spin in zip(spec.columns, row_spins):
                        spin.blockSignals(True)
                        spin.setValue(value[row][column.key])
                        spin.blockSignals(False)
            elif spec.kind == "float_list":
                for index, spin in enumerate(control):
                    spin.blockSignals(True)
                    spin.setValue(value[index])
                    spin.blockSignals(False)
            else:
                control.blockSignals(True)
                control.setValue(value)
                control.blockSignals(False)
        for group in self._slot_groups.values():
            group.blockSignals(False)
        self.refresh_response()

    def reset_algorithms(self):
        self._pending_parameters.clear()
        self.apply_timer.stop()
        self.document.reset_algorithms()
        self._sync_algorithm_controls()
        self.status_label.setText("算法参数已恢复默认值")

    def save_algorithms(self):
        self._flush_parameters()
        try:
            self.document.save_algorithms()
            self.status_label.setText("算法配置已保存：{}".format(self.document.chain.config_path))
        except AudioError as exc:
            self._show_error(str(exc))

    def reload_algorithms(self):
        self._pending_parameters.clear()
        self.apply_timer.stop()
        try:
            errors = self.document.reload_algorithms()
        except AudioError as exc:
            self._show_error(str(exc))
            return
        self._rebuild_algorithm_controls()
        self.status_label.setText("算法配置已重载" if not errors else errors[-1])

    def _fit_target_requested(self):
        if self.fit_target_provider is None:
            self.status_label.setText("目标曲线来源不可用，无法进行目标曲线拟合")
            return
        target_key, target_label = self.fit_target_provider()
        self.fit_to_target(target_key, target_label)

    def fit_to_target(self, target_key, target_label):
        """按当前音源平滑谱与所选目标曲线的差值自动拟合 16 段 EQ 增益。"""
        if not self.document.loaded:
            self.status_label.setText("请先打开音频文件，再进行目标曲线拟合")
            return
        try:
            slot = self.document.chain.get_slot("eq")
        except KeyError:
            self.status_label.setText("算法链中未找到 EQ 均衡器，无法拟合")
            return
        grid, before = smoothed_response(self.document.original, self.document.sample_rate)
        try:
            target = target_response(target_key, grid)
        except (OSError, ValueError) as exc:
            self.status_label.setText("目标曲线读取失败：{}".format(exc))
            return
        desired = target - before
        # 剔除信号能量过低的频段（如 MP3 高切以上），避免噪声差值被误拟合。
        valid = before > -45.0
        try:
            bands, achieved = fit_bands_to_curve(
                self.document.sample_rate, grid[valid], desired[valid],
                slot.params["bands"],
            )
        except ValueError as exc:
            self.status_label.setText(str(exc))
            return
        self._flush_parameters()
        try:
            self.document.set_parameter("eq", "bands", bands)
            if not slot.enabled:
                self.document.set_enabled("eq", True)
        except (AudioError, ValueError, KeyError) as exc:
            self.status_label.setText(str(exc))
            return
        self._sync_algorithm_controls()
        residual = desired[valid] - achieved
        rms = float(np.sqrt(np.mean(np.square(residual)))) if residual.size else 0.0
        fit_grid = grid[valid]
        self.status_label.setText(
            "已按「{}」完成 16 段增益拟合：{:.0f}–{:.0f} Hz 残差 RMS {:.1f} dB".format(
                target_label, fit_grid[0], fit_grid[-1], rms
            )
        )

    def control(self, action):
        actions = {
            "play_original": lambda: self.play("original"),
            "play_processed": lambda: self.play("processed"),
            "stop": self.stop,
            "reset": self.reset_algorithms,
            "save_config": self.save_algorithms,
            "reload_config": self.reload_algorithms,
            "fit_target": self._fit_target_requested,
        }
        if action in actions:
            actions[action]()
        elif self.document.logger:
            self.document.logger.warning("未知音频控制动作：%s", action)

    def open_audio(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "打开音频文件", "",
            "音频文件 (*.wav *.pcm *.raw *.mp3 *.flac *.ogg *.m4a *.aac);;"
            "WAV 文件 (*.wav);;原始 PCM (*.pcm *.raw);;所有文件 (*)",
        )
        if not path:
            return
        pcm_format = None
        if path.lower().endswith((".pcm", ".raw")):
            dialog = PCMFormatDialog(self)
            if dialog.exec_() != QDialog.Accepted:
                return
            pcm_format = dialog.pcm_format()
        self.load_path(path, pcm_format)

    def load_path(self, path, pcm_format=None):
        self._discard_preview()
        self.status_label.setText("正在读取音频：{}".format(os.path.basename(path)))
        self.document.load_async(path, pcm_format)

    def _source_changed(self, path):
        self._discard_preview()
        channels = 1 if self.document.original.ndim == 1 else self.document.original.shape[1]
        self.file_label.setText(
            "{}  |  {:.1f} s  |  {} Hz  |  {} 声道".format(
                os.path.basename(path), self.document.duration,
                self.document.sample_rate, channels,
            )
        )
        self.status_label.setText("音频已加载，正在生成处理结果")
        self._emit_control_state()

    def refresh_audio(self):
        if not self.document.loaded:
            return
        if self.preview_source == "processed":
            self._discard_preview()
        self.refresh_response()
        self.status_label.setText("处理结果已更新")
        self._emit_control_state()

    def refresh_response(self):
        if not self.document.sample_rate:
            self.response_curve.setData([], [])
            return
        try:
            slot = self.document.chain.get_slot("eq")
        except KeyError:
            self.response_curve.setData([], [])
            return
        x, y = eq_bands_response(self.document.sample_rate, slot.params["bands"])
        self.response_curve.setData(x, y)
        self.response_plot.setYRange(-14, 14)

    def _busy_changed(self, busy):
        if busy and self.document.processing:
            self.status_label.setText("正在应用最新算法参数")
        self._emit_control_state()

    def _emit_control_state(self):
        if settings.app_event is None:
            return
        states = {
            QMediaPlayer.StoppedState: "stopped",
            QMediaPlayer.PlayingState: "playing",
            QMediaPlayer.PausedState: "paused",
        }
        processed_ready = (
            self.document.loaded and not self.document.processing
            and not self.apply_timer.isActive()
        )
        settings.app_event.audio_controls_state.emit(
            self.document.loaded, processed_ready,
            states.get(self.player.state(), "stopped"), self.preview_source or "",
        )

    def _discard_preview(self):
        self.player.stop()
        self.player.setMedia(QMediaContent())
        if self.preview_path:
            try:
                os.remove(self.preview_path)
            except OSError:
                pass
        self.preview_path = None
        self.preview_source = None

    def play(self, source="processed"):
        if source == "processed":
            self._flush_parameters()
        if not self.document.loaded:
            return
        if self.preview_source == source:
            if self.player.state() == QMediaPlayer.PlayingState:
                self.player.pause()
                return
            if self.player.state() == QMediaPlayer.PausedState:
                self.player.play()
                return
        try:
            data = self.document.audio_data(source)
            self._discard_preview()
            handle, path = tempfile.mkstemp(prefix="audio_tuning_", suffix=".wav")
            os.close(handle)
            save_wav(path, self.document.sample_rate, data)
            self.preview_path = path
            self.preview_source = source
            self.player.setMedia(QMediaContent(QUrl.fromLocalFile(path)))
            self.player.play()
        except AudioError as exc:
            self.status_label.setText(str(exc))
            self._emit_control_state()

    def stop(self):
        self.player.stop()

    def _player_state_changed(self, _state):
        self._emit_control_state()

    def save_audio(self, source="processed"):
        if source == "processed":
            self._flush_parameters()
        if not self.document.loaded:
            QMessageBox.information(self, "提示", "请先打开音频文件。")
            return
        if source == "processed" and self.document.processing:
            self.status_label.setText("请等待最新处理结果完成后再保存")
            return
        suffix = "_original.wav" if source == "original" else "_processed.wav"
        default_name = os.path.splitext(self.document.path)[0] + suffix
        path, _ = QFileDialog.getSaveFileName(
            self, "保存音频", default_name, "WAV 文件 (*.wav)"
        )
        if path:
            self.save_path(path, source)

    def save_path(self, path, source="processed"):
        try:
            if not path.lower().endswith(".wav"):
                path += ".wav"
            self.document.save(path, source)
            self.status_label.setText("音频已保存：{}".format(path))
        except AudioError as exc:
            self._show_error(str(exc))

    def _show_error(self, message):
        self.status_label.setText(message)
        QMessageBox.critical(self, "音频操作失败", message)

    def shutdown(self):
        self.apply_timer.stop()
        self._discard_preview()

    def closeEvent(self, event):
        self.shutdown()
        super().closeEvent(event)


class WaveformPage(QFrame):
    def __init__(self, document, parent=None):
        super().__init__(parent)
        self.document = document
        root = QVBoxLayout(self)
        self.wave_plot = pg.PlotWidget(title="原始 / 处理后波形")
        _style_plot(self.wave_plot)
        self.wave_plot.setLabel("bottom", "时间", units="s", color=_plot_label_color())
        self.wave_plot.setLabel("left", "幅度", units="FS", color=_plot_label_color())
        self.wave_plot.showGrid(x=True, y=True, alpha=0.25)
        self.wave_plot.addLegend()
        self.original_curve = self.wave_plot.plot(
            pen=pg.mkPen(ORIGINAL_COLOR, width=1.2), name="原始"
        )
        self.processed_curve = self.wave_plot.plot(
            pen=pg.mkPen(PROCESSED_COLOR, width=1.2), name="处理后"
        )
        root.addWidget(self.wave_plot, 1)
        self.document.audio_changed.connect(self.refresh)

    def refresh(self, *_args):
        if not self.document.loaded:
            self.original_curve.setData([], [])
            self.processed_curve.setData([], [])
            return
        x, y = plot_samples(self.document.original, self.document.sample_rate)
        self.original_curve.setData(x, y)
        x, y = plot_samples(self.document.processed, self.document.sample_rate)
        self.processed_curve.setData(x, y)
        self.wave_plot.enableAutoRange()


class SpectrumComparisonPage(QFrame):
    def __init__(self, document, parent=None):
        super().__init__(parent)
        self.document = document
        root = QVBoxLayout(self)
        self.spectrum_plot = pg.PlotWidget(title="处理前后频响（FFT，dBFS）")
        _style_plot(self.spectrum_plot)
        self.spectrum_plot.setLabel("bottom", "频率", units="Hz", color=_plot_label_color())
        self.spectrum_plot.setLabel("left", "幅度", units="dBFS", color=_plot_label_color())
        self.spectrum_plot.setLogMode(x=True, y=False)
        self.spectrum_plot.showGrid(x=True, y=True, alpha=0.25)
        self.spectrum_plot.addLegend()
        self.before_curve = self.spectrum_plot.plot(
            pen=pg.mkPen(ORIGINAL_COLOR, width=1.2), name="原始"
        )
        self.after_curve = self.spectrum_plot.plot(
            pen=pg.mkPen(PROCESSED_COLOR, width=1.2), name="处理后"
        )
        root.addWidget(self.spectrum_plot, 1)
        self.empty_label = QLabel("请使用 Header 的“文件 → 打开...”加载音频")
        self.empty_label.setAlignment(Qt.AlignCenter)
        root.addWidget(self.empty_label)
        self.document.audio_changed.connect(self.refresh)

    def refresh(self, *_args):
        if not self.document.loaded:
            self.before_curve.setData([], [])
            self.after_curve.setData([], [])
            return
        before_x, before_y = calculate_spectrum(
            self.document.original, self.document.sample_rate
        )
        after_x, after_y = calculate_spectrum(
            self.document.processed, self.document.sample_rate
        )
        self.before_curve.setData(before_x, before_y)
        self.after_curve.setData(after_x, after_y)
        upper = min(20000.0, self.document.sample_rate / 2.0)
        lower = min(20.0, upper / 2.0)
        self.spectrum_plot.setXRange(
            np.log10(lower), np.log10(max(lower * 1.001, upper)), padding=0
        )
        self.spectrum_plot.setYRange(-120, 12, padding=0)
        self.empty_label.setText(os.path.basename(self.document.path))


class HarmanComparisonPage(QFrame):
    def __init__(self, document, parent=None):
        super().__init__(parent)
        self.document = document
        root = QVBoxLayout(self)
        controls = QHBoxLayout()
        title = QLabel("平滑频谱与哈曼目标参考（1/6 倍频程，1 kHz 归一化）")
        title.setAlignment(Qt.AlignCenter)
        self.target_combo = QComboBox()
        for key, label in available_targets():
            self.target_combo.addItem(label, key)
        controls.addWidget(title, 1)
        controls.addWidget(QLabel("目标曲线"))
        controls.addWidget(self.target_combo)
        root.addLayout(controls)

        self.target_plot = pg.PlotWidget(title="原始 / 处理后 / 哈曼目标")
        _style_plot(self.target_plot)
        self.target_plot.setLabel("bottom", "频率", units="Hz", color=_plot_label_color())
        self.target_plot.setLabel("left", "相对幅度", units="dB", color=_plot_label_color())
        self.target_plot.setLogMode(x=True, y=False)
        self.target_plot.showGrid(x=True, y=True, alpha=0.25)
        self.target_plot.addLegend()
        self.smoothed_before_curve = self.target_plot.plot(
            pen=pg.mkPen(ORIGINAL_COLOR, width=1.5), name="原始频谱"
        )
        self.smoothed_after_curve = self.target_plot.plot(
            pen=pg.mkPen(PROCESSED_COLOR, width=1.5), name="处理后频谱"
        )
        self.harman_curve = self.target_plot.plot(
            pen=pg.mkPen(TARGET_COLOR, width=2, style=Qt.DashLine), name="哈曼目标"
        )
        root.addWidget(self.target_plot, 1)
        self.empty_label = QLabel("音频频谱仅作目标参考，不等同于耳机测量频响")
        self.empty_label.setAlignment(Qt.AlignCenter)
        root.addWidget(self.empty_label)
        self.target_combo.currentIndexChanged.connect(self.refresh)
        self.document.audio_changed.connect(self.refresh)

    def current_target(self):
        """返回当前选中的目标曲线 (key, 显示名)，供目标曲线拟合使用。"""
        return self.target_combo.currentData(), self.target_combo.currentText()

    def refresh(self, *_args):
        if not self.document.loaded:
            for curve in (
                self.smoothed_before_curve, self.smoothed_after_curve, self.harman_curve,
            ):
                curve.setData([], [])
            return
        smooth_x, smooth_before = smoothed_response(
            self.document.original, self.document.sample_rate
        )
        _, smooth_after = smoothed_response(
            self.document.processed, self.document.sample_rate
        )
        self.smoothed_before_curve.setData(smooth_x, smooth_before)
        self.smoothed_after_curve.setData(smooth_x, smooth_after)
        try:
            target = target_response(self.target_combo.currentData(), smooth_x)
            self.harman_curve.setData(smooth_x, target)
        except (OSError, ValueError) as exc:
            self.harman_curve.setData([], [])
            self.empty_label.setText("目标曲线读取失败：{}".format(exc))
            return
        upper = min(20000.0, self.document.sample_rate / 2.0)
        lower = min(20.0, upper / 2.0)
        self.target_plot.setXRange(
            np.log10(lower), np.log10(max(lower * 1.001, upper)), padding=0
        )
        self.target_plot.setYRange(-25, 25, padding=0)
        self.empty_label.setText(
            "{} | 音频频谱仅作目标参考，不等同于耳机测量频响".format(
                os.path.basename(self.document.path)
            )
        )


EqualizerPage = AudioProcessingPage
