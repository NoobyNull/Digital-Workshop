"""Ollama Vision Provider (CLI-only)

Implements vision analysis using the local ``ollama`` CLI, without
using any HTTP endpoints from the application. This satisfies the
requirement that local AI must not be exposed over HTTP by the app
itself while still benefiting from Ollama's model runtime.
"""

from __future__ import annotations

import os
import subprocess
from typing import Optional, Dict, Any, List

from .base_provider import BaseProvider


class OllamaProvider(BaseProvider):
    """Ollama provider that talks to the local runtime via CLI only.

    The provider shells out to ``ollama`` for all operations:

    * ``ollama --version`` and ``ollama list`` for capability checks
    * ``ollama run <model> <prompt>`` for actual vision analysis

    No HTTP calls are made from the application; any HTTP traffic is
    internal to the Ollama daemon itself.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "moondream",
        **kwargs: Any,
    ) -> None:
        # ``api_key`` is accepted for interface parity but unused.
        super().__init__(api_key=api_key, **kwargs)
        self.model = model or "moondream"
        self._ollama_available = self._check_ollama_available()

    # ------------------------------------------------------------------
    # Capability and configuration
    # ------------------------------------------------------------------
    def _check_ollama_available(self) -> bool:
        """Return True if the ``ollama`` CLI is available on PATH.

        We intentionally keep this check lightweight and avoid raising
        errors here; callers can inspect :meth:`is_configured`.
        """

        try:
            result = subprocess.run(
                ["ollama", "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5,
                check=False,
            )
        except FileNotFoundError:
            self.logger.warning("Ollama CLI not found on PATH")
            return False
        except OSError as exc:  # pragma: no cover - defensive
            self.logger.error("Error invoking Ollama CLI: %s", exc)
            return False

        if result.returncode != 0:
            self.logger.warning(
                "Ollama CLI returned non-zero exit code %s: %s",
                result.returncode,
                result.stderr.strip(),
            )
            return False

        return True

    def is_configured(self) -> bool:  # type: ignore[override]
        """Return True when the CLI is available and a model is set."""

        return bool(self._ollama_available and self.model)

    def list_available_models(self) -> List[str]:  # type: ignore[override]
        """Return a list of locally available vision-capable models.

        The list is derived from ``ollama list`` and filtered to known
        vision models (currently ``moondream``, ``bakllava``, ``llava``).
        If the CLI is not available or the command fails, a conservative
        static list is returned so the UI still has something to show.
        """

        if not self._ollama_available:
            return ["moondream", "bakllava"]

        try:
            result = subprocess.run(
                ["ollama", "list"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
                check=False,
            )
        except (FileNotFoundError, OSError) as exc:
            self.logger.error("Failed to list Ollama models: %s", exc)
            return ["moondream", "bakllava"]

        if result.returncode != 0:
            self.logger.warning(
                "`ollama list` failed with code %s: %s",
                result.returncode,
                result.stderr.strip(),
            )
            return ["moondream", "bakllava"]

        vision_models: List[str] = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line or line.lower().startswith("name"):
                continue
            parts = line.split()
            if not parts:
                continue
            name = parts[0]
            base_name = name.split(":", 1)[0]
            if base_name in {"moondream", "bakllava", "llava"}:
                vision_models.append(name)

        return vision_models or ["moondream", "bakllava"]


    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------
    def analyze_image(self, image_path: str, prompt: Optional[str] = None) -> Dict[str, Any]:  # type: ignore[override]
        """Analyze an image using the configured Ollama model.

        The image itself is referenced by absolute path in the prompt so
        that Ollama's vision models can load it directly on the local
        machine. The application never opens any HTTP endpoints.
        """

        if not self.is_configured():
            raise ValueError("Ollama CLI is not available or model is not configured")

        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")

        base_prompt = prompt or self.get_default_prompt()
        full_prompt = (
            f"{base_prompt.strip()}\n\n"
            f"The image to analyze is located at this path on disk:\n"
            f"{image_path}\n\n"
            "Use the visual content of the image together with the prompt "
            "to produce the JSON response."
        )

        self.logger.info("Running Ollama model '%s' for image analysis", self.model)
        self.logger.debug("Ollama prompt: %s", full_prompt)

        try:
            result = subprocess.run(
                ["ollama", "run", self.model, full_prompt],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=300,
                check=False,
            )
        except FileNotFoundError as exc:
            raise ValueError("Ollama CLI not found on PATH") from exc
        except OSError as exc:  # pragma: no cover - defensive
            raise RuntimeError(f"Failed to invoke Ollama CLI: {exc}") from exc

        if result.returncode != 0:
            error_text = result.stderr.strip() or result.stdout.strip()
            self.logger.error(
                "Ollama returned non-zero exit code %s: %s",
                result.returncode,
                error_text,
            )
            raise RuntimeError(f"Ollama error: {error_text}")

        raw_response = result.stdout.strip()
        self.logger.debug("Ollama raw response: %s", raw_response)

        return self.parse_response(raw_response)
