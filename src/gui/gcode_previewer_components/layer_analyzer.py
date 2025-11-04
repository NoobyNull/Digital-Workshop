"""Layer Analyzer - Detect and manage layers in G-code based on Z-height."""

from typing import List, Dict, Optional
from dataclasses import dataclass

from .gcode_parser import GcodeMove


@dataclass
class Layer:
    """Represents a single layer in the toolpath."""

    layer_number: int
    z_height: float
    start_move_index: int
    end_move_index: int
    move_count: int

    def __repr__(self) -> str:
        return f"Layer {self.layer_number} (Z={self.z_height:.2f}, moves={self.move_count})"


class LayerAnalyzer:
    """Analyzes G-code moves and detects layers based on Z-height changes."""

    def __init__(self, z_threshold: float = 0.1):
        """
        Initialize the layer analyzer.

        Args:
            z_threshold: Minimum Z-height change to consider a new layer
        """
        self.z_threshold = z_threshold
        self.layers: List[Layer] = []
        self.move_to_layer: Dict[int, int] = {}  # Maps move index to layer number

    def analyze(self, moves: List[GcodeMove]) -> List[Layer]:
        """
        Analyze moves and detect layers.

        Args:
            moves: List of G-code moves

        Returns:
            List of detected layers
        """
        self.layers = []
        self.move_to_layer = {}

        if not moves:
            return self.layers

        current_layer = 0
        current_z = moves[0].z if moves[0].z is not None else 0.0
        layer_start = 0

        for move_idx, move in enumerate(moves):
            if move.z is None:
                self.move_to_layer[move_idx] = current_layer
                continue

            # Check if Z-height changed significantly
            z_diff = abs(move.z - current_z)

            if z_diff > self.z_threshold:
                # End current layer
                if move_idx > layer_start:
                    layer = Layer(
                        layer_number=current_layer,
                        z_height=current_z,
                        start_move_index=layer_start,
                        end_move_index=move_idx - 1,
                        move_count=move_idx - layer_start,
                    )
                    self.layers.append(layer)

                # Start new layer
                current_layer += 1
                current_z = move.z
                layer_start = move_idx

            self.move_to_layer[move_idx] = current_layer

        # Add final layer
        if len(moves) > layer_start:
            layer = Layer(
                layer_number=current_layer,
                z_height=current_z,
                start_move_index=layer_start,
                end_move_index=len(moves) - 1,
                move_count=len(moves) - layer_start,
            )
            self.layers.append(layer)

        return self.layers

    def get_layers(self) -> List[Layer]:
        """Get all detected layers."""
        return self.layers

    def get_layer_for_move(self, move_index: int) -> Optional[int]:
        """Get the layer number for a specific move."""
        return self.move_to_layer.get(move_index)

    def get_layer_by_number(self, layer_number: int) -> Optional[Layer]:
        """Get a layer by its number."""
        for layer in self.layers:
            if layer.layer_number == layer_number:
                return layer
        return None

    def get_moves_for_layer(self, layer_number: int, moves: List[GcodeMove]) -> List[GcodeMove]:
        """Get all moves for a specific layer."""
        layer = self.get_layer_by_number(layer_number)
        if not layer:
            return []
        return moves[layer.start_move_index : layer.end_move_index + 1]

    def get_layer_statistics(self) -> Dict[str, any]:
        """Get statistics about detected layers."""
        if not self.layers:
            return {"total_layers": 0, "layers": []}

        layer_info = []
        for layer in self.layers:
            layer_info.append(
                {
                    "number": layer.layer_number,
                    "z_height": layer.z_height,
                    "move_count": layer.move_count,
                    "start_index": layer.start_move_index,
                    "end_index": layer.end_move_index,
                }
            )

        return {
            "total_layers": len(self.layers),
            "layers": layer_info,
            "min_z": min(l.z_height for l in self.layers),
            "max_z": max(l.z_height for l in self.layers),
        }
