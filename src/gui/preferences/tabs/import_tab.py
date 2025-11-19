"""Tab for configuring import concurrency and workflow settings."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QFormLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from src.core.services.import_settings import ImportSettings


class ImportSettingsTab(QWidget):
    """Preferences tab exposing import concurrency controls."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._settings = ImportSettings()
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        header = QLabel("Import Workflow")
        header.setStyleSheet("font-weight: bold; font-size: 13pt;")
        layout.addWidget(header)

        desc = QLabel(
            "Tune how many files are prepared and thumbnailed at once. "
            "Use modest values when working from network drives or limited GPUs."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        form = QFormLayout()
        self.prep_workers_spin = QSpinBox()
        self.prep_workers_spin.setRange(1, 16)
        self.prep_workers_spin.setSuffix(" workers")
        form.addRow("Concurrent file preparation:", self.prep_workers_spin)

        self.thumbnail_workers_spin = QSpinBox()
        self.thumbnail_workers_spin.setRange(1, 8)
        self.thumbnail_workers_spin.setSuffix(" workers")
        form.addRow("Concurrent thumbnail renders:", self.thumbnail_workers_spin)

        self.queue_limit_spin = QSpinBox()
        self.queue_limit_spin.setRange(2, 64)
        self.queue_limit_spin.setSuffix(" files")
        form.addRow("Prepared queue depth:", self.queue_limit_spin)

        layout.addLayout(form)

        hint = QLabel(
            "Tip: if you see stalls or GPU overload, lower these values. "
            "Fast SSD systems can safely run more workers."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.auto_button = QPushButton("Restore Suggested Values")
        self.auto_button.clicked.connect(self._on_restore_suggested)
        layout.addWidget(self.auto_button)

        layout.addStretch(1)

    def _load_settings(self) -> None:
        data = self._settings.get_concurrency()
        self.prep_workers_spin.setValue(data.prep_workers)
        self.thumbnail_workers_spin.setValue(data.thumbnail_workers)
        self.queue_limit_spin.setValue(data.queue_limit)

    def save_settings(self) -> None:
        self._settings.set_concurrency(
            self.prep_workers_spin.value(),
            self.thumbnail_workers_spin.value(),
            self.queue_limit_spin.value(),
        )

    def reset_to_defaults(self) -> None:
        self._settings.reset_defaults()
        self._load_settings()

    def _on_restore_suggested(self) -> None:
        self.reset_to_defaults()
