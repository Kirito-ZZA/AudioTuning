import os

from PyQt5.QtWidgets import QFrame, QStackedWidget, QVBoxLayout

import config as settings
from audio_engine import AudioDocument
from audio_widgets import (
    AudioProcessingPage, HarmanComparisonPage, SpectrumComparisonPage, WaveformPage,
)
from tabBar import TabBar


class Center(QFrame):
    """Central page host and shared audio-document owner."""

    def __init__(self, config=None, parent=None, logger=None):
        super().__init__(parent)
        self.config, self.parent, self.logger = config, parent, logger
        self.app_eventCenter = settings.app_event
        self.tabBar = TabBar(self.config, self, self.logger)

        algorithm_config = os.path.join(settings.basepath, "conf", "algorithms.json")
        self.document = AudioDocument(algorithm_config, parent=self, logger=self.logger)
        self.audioPage = AudioProcessingPage(self.document, self)
        self.waveformPage = WaveformPage(self.document, self)
        self.spectrumPage = SpectrumComparisonPage(self.document, self)
        self.harmanPage = HarmanComparisonPage(self.document, self)

        self.plotStackedWidget = QStackedWidget()
        for page in (
            self.audioPage, self.waveformPage, self.spectrumPage, self.harmanPage,
        ):
            self.plotStackedWidget.addWidget(page)
        self._layout()

        self.tabBar.tab_change.connect(self.plot_sw)
        self.app_eventCenter.plot_auto_range.connect(self.auto_range_event)
        self.app_eventCenter.file_open.connect(self.open_audio)
        self.app_eventCenter.save_file.connect(self.save_audio)
        self.app_eventCenter.audio_control.connect(self.audioPage.control)

    def _layout(self):
        layout = QVBoxLayout()
        layout.addWidget(self.tabBar)
        layout.addWidget(self.plotStackedWidget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

    def auto_range_event(self):
        current = self.plotStackedWidget.currentWidget()
        for name in ("wave_plot", "response_plot", "spectrum_plot", "target_plot"):
            plot = getattr(current, name, None)
            if plot is not None:
                plot.enableAutoRange()

    def plot_sw(self, tab_index):
        if 0 <= tab_index < self.plotStackedWidget.count():
            self.plotStackedWidget.setCurrentIndex(tab_index)

    def open_audio(self):
        self.audioPage.open_audio()

    def save_audio(self, source="processed"):
        self.audioPage.save_audio(source)

    def shutdown(self):
        self.audioPage.shutdown()
        self.document.shutdown()
