"""First-run dialog for local AI (Ollama) configuration.

This dialog runs once on first launch (unless skipped) and lets the user
opt into using a local Ollama vision model for image descriptions. It
probes the best available GPU device, recommends a small vision model
under the user's constraints, and persists the choice into QSettings so
that the AI Description service can pick it up.
"""

from __future__ import annotations

from typing import Optional
import subprocess

from PySide6.QtCore import Qt, QSettings
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QCheckBox,
    QMessageBox,
    QWidget,
)

from src.core.gpu_acceleration import GPUAccelerator, GPUBackend, GPUDevice
from src.core.logging_config import get_logger


logger = get_logger(__name__)


class AIFirstRunDialog(QDialog):
    """Minimal first-run wizard for local AI via Ollama CLI."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("AI Setup")
        self.setModal(True)

        layout = QVBoxLayout(self)

        intro = QLabel(
            "Digital Workshop can use a local Ollama model for image analysis.\n"
            "This keeps data on your machine and avoids external network calls."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        device = self._detect_best_device()
        gpu_label = QLabel(self._format_device_description(device))
        gpu_label.setWordWrap(True)
        layout.addWidget(gpu_label)

        self._use_local_checkbox = QCheckBox(
            "Use local AI (Ollama CLI) for image descriptions"
        )
        self._use_local_checkbox.setChecked(True)
        layout.addWidget(self._use_local_checkbox)

        self._startup_checkbox = QCheckBox(
            "Enable local AI provider by default on startup"
        )
        self._startup_checkbox.setChecked(True)
        layout.addWidget(self._startup_checkbox)

        self._recommended_model = self._select_recommended_model(device)
        recommended = QLabel(
            f"Recommended model: {self._recommended_model or 'none (CPU only)'}"
        )
        recommended.setWordWrap(True)
        layout.addWidget(recommended)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        skip_button = QPushButton("Skip")
        continue_button = QPushButton("Continue")
        buttons.addWidget(skip_button)
        buttons.addWidget(continue_button)
        layout.addLayout(buttons)

        skip_button.clicked.connect(self._on_skip)
        continue_button.clicked.connect(lambda: self._on_continue(device))

    # ------------------------------------------------------------------
    # Hardware probing and model selection
    # ------------------------------------------------------------------
    def _detect_best_device(self) -> Optional[GPUDevice]:
        """Return the best detected GPU device, or ``None`` if unavailable."""

        try:
            accelerator = GPUAccelerator()
            return accelerator.active_device
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Failed to detect GPU devices for AI setup: %s", exc)
            return None

    def _format_device_description(self, device: Optional[GPUDevice]) -> str:
        if not device or not device.is_available:
            return (
                "No dedicated GPU detected. Local models will run on CPU; "
                "smaller models are recommended."
            )

        return (
            f"Detected GPU: {device.name} ({device.backend.value}), "
            f"approx. {device.memory_gb:.1f} GB VRAM."
        )

    def _select_recommended_model(self, device: Optional[GPUDevice]) -> str:
        """Select a small vision model under the user's VRAM constraints.

        - Prefer < 4 GB models whenever possible.
        - Allow models up to ~8 GB only when CUDA VRAM is >= 16 GB.

        We only select between known vision-capable models that are exposed
        through the Ollama provider in this application.
        """

        if device and device.backend == GPUBackend.CUDA and device.memory_gb >= 16.0:
            # On high-memory CUDA GPUs we can use a slightly heavier model.
            return "bakllava"

        # For CPU, OpenCL, or smaller GPUs prefer the smallest vision model.
        return "moondream"

    # ------------------------------------------------------------------
    # Button handlers
    # ------------------------------------------------------------------
    def _on_skip(self) -> None:
        """Skip local AI configuration and mark first-run as done."""

        self._mark_first_run_completed()
        self._update_ai_settings(use_local=False, run_on_startup=False, model=None)
        self.accept()

    def _on_continue(self, device: Optional[GPUDevice]) -> None:  # noqa: ARG002
        """Apply the user's choices and configure local AI if requested."""

        use_local = self._use_local_checkbox.isChecked()
        run_on_startup = self._startup_checkbox.isChecked()
        model = self._recommended_model if use_local else None

        if use_local and model:
            if not self._ensure_model_available(model):
                QMessageBox.warning(
                    self,
                    "Ollama not available",
                    (
                        "Ollama CLI or the recommended model could not be used. "
                        "You can configure AI providers later in the AI settings dialog."
                    ),
                )
                use_local = False
                run_on_startup = False
                model = None

        self._mark_first_run_completed()
        self._update_ai_settings(
            use_local=use_local, run_on_startup=run_on_startup, model=model
        )
        self.accept()

    # ------------------------------------------------------------------
    # Ollama model handling
    # ------------------------------------------------------------------
    def _ensure_model_available(self, model: str) -> bool:
        """Ensure the given Ollama model exists locally, pulling if needed."""

        try:
            list_result = subprocess.run(
                ["ollama", "list"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
                check=False,
            )
        except (OSError, ValueError) as exc:
            logger.warning("Ollama CLI does not appear to be available: %s", exc)
            return False

        if list_result.returncode != 0:
            logger.warning("Failed to list Ollama models: %s", list_result.stderr.strip())
            return False

        installed = any(model in line for line in list_result.stdout.splitlines())
        if installed:
            return True

        reply = QMessageBox.question(
            self,
            "Download model",
            (
                f"The recommended model '{model}' is not installed.\n\n"
                f"Download it now with 'ollama pull {model}'? This may take several "
                "minutes and download a few gigabytes."
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if reply != QMessageBox.Yes:
            return False

        try:
            pull_result = subprocess.run(
                ["ollama", "pull", model],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=600,
                check=False,
            )
        except (OSError, ValueError) as exc:  # pragma: no cover - defensive
            logger.error("Failed to download Ollama model %s: %s", model, exc)
            QMessageBox.critical(
                self,
                "Download failed",
                f"Could not download model '{model}'. Check Ollama installation and try again.",
            )
            return False

        if pull_result.returncode != 0:
            logger.error("Ollama pull failed for %s: %s", model, pull_result.stderr.strip())
            QMessageBox.critical(
                self,
                "Download failed",
                f"Ollama reported an error downloading model '{model}'.",
            )
            return False

        logger.info("Successfully downloaded Ollama model %s", model)
        return True

    # ------------------------------------------------------------------
    # Settings helpers
    # ------------------------------------------------------------------
    def _mark_first_run_completed(self) -> None:
        settings = QSettings()
        settings.setValue("ai_description/settings/first_run_completed", True)

    def _update_ai_settings(
        self, use_local: bool, run_on_startup: bool, model: Optional[str]
    ) -> None:
        settings = QSettings()

        # Settings block used by AIDescriptionService
        settings.setValue("ai_description/settings/use_local_ai", use_local)
        settings.setValue(
            "ai_description/settings/run_local_ai_on_startup", run_on_startup
        )

        # Provider-specific configuration for Ollama
        provider_group = "ai_description/providers/ollama"
        settings.setValue(f"{provider_group}/enabled", use_local)
        if model:
            settings.setValue(f"{provider_group}/model", model)

        if use_local:
            settings.setValue("ai_description/settings/default_provider", "ollama")


def run_ai_first_launch_setup(parent: Optional[QWidget] = None) -> None:
    """Run the first-launch AI setup dialog if it has not been completed."""

    settings = QSettings()
    first_run_done = settings.value(
        "ai_description/settings/first_run_completed", False, type=bool
    )
    if first_run_done:
        return

    dialog = AIFirstRunDialog(parent)
    dialog.setWindowModality(Qt.ApplicationModal)
    dialog.exec()

