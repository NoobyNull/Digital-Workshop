"""G-code Parser - Parse and extract toolpath data from G-code files."""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class GcodeMove:
    """Represents a single G-code move command."""
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None
    feed_rate: Optional[float] = None
    spindle_speed: Optional[float] = None
    is_rapid: bool = False  # G00 rapid move
    is_cutting: bool = False  # G01 linear cut
    is_arc: bool = False  # G02/G03 arc
    line_number: int = 0
    raw_command: str = ""


class GcodeParser:
    """Parse G-code files and extract toolpath information."""

    def __init__(self):
        """Initialize the parser."""
        self.moves: List[GcodeMove] = []
        self.current_position = (0.0, 0.0, 0.0)
        self.current_feed_rate = 0.0
        self.current_spindle_speed = 0.0
        self.bounds = {
            'min_x': float('inf'), 'max_x': float('-inf'),
            'min_y': float('inf'), 'max_y': float('-inf'),
            'min_z': float('inf'), 'max_z': float('-inf'),
        }

    def parse_file(self, filepath: str) -> List[GcodeMove]:
        """Parse a G-code file and return list of moves."""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            return self.parse_lines(lines)
        except Exception as e:
            raise ValueError(f"Failed to parse G-code file: {e}")

    def parse_lines(self, lines: List[str]) -> List[GcodeMove]:
        """Parse G-code lines and extract moves."""
        self.moves = []
        self.current_position = (0.0, 0.0, 0.0)

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith(';') or line.startswith('%'):
                continue
            
            # Remove inline comments
            if ';' in line:
                line = line.split(';')[0].strip()
            
            move = self._parse_line(line, line_num)
            if move:
                self.moves.append(move)
                self._update_bounds(move)

        return self.moves

    def _parse_line(self, line: str, line_num: int) -> Optional[GcodeMove]:
        """Parse a single G-code line."""
        move = GcodeMove(line_number=line_num, raw_command=line)
        
        # Extract G-code command
        g_match = re.search(r'G(\d+)', line, re.IGNORECASE)
        if not g_match:
            return None
        
        g_code = int(g_match.group(1))
        
        # Determine move type
        if g_code == 0:
            move.is_rapid = True
        elif g_code == 1:
            move.is_cutting = True
        elif g_code in (2, 3):
            move.is_arc = True
        else:
            return None
        
        # Extract coordinates
        x_match = re.search(r'X([-+]?\d*\.?\d+)', line, re.IGNORECASE)
        y_match = re.search(r'Y([-+]?\d*\.?\d+)', line, re.IGNORECASE)
        z_match = re.search(r'Z([-+]?\d*\.?\d+)', line, re.IGNORECASE)
        
        if x_match:
            move.x = float(x_match.group(1))
        else:
            move.x = self.current_position[0]
        
        if y_match:
            move.y = float(y_match.group(1))
        else:
            move.y = self.current_position[1]
        
        if z_match:
            move.z = float(z_match.group(1))
        else:
            move.z = self.current_position[2]
        
        # Extract feed rate and spindle speed
        f_match = re.search(r'F([-+]?\d*\.?\d+)', line, re.IGNORECASE)
        if f_match:
            self.current_feed_rate = float(f_match.group(1))
        move.feed_rate = self.current_feed_rate
        
        s_match = re.search(r'S([-+]?\d*\.?\d+)', line, re.IGNORECASE)
        if s_match:
            self.current_spindle_speed = float(s_match.group(1))
        move.spindle_speed = self.current_spindle_speed
        
        # Update current position
        self.current_position = (move.x, move.y, move.z)
        
        return move

    def _update_bounds(self, move: GcodeMove) -> None:
        """Update bounding box with move coordinates."""
        if move.x is not None:
            self.bounds['min_x'] = min(self.bounds['min_x'], move.x)
            self.bounds['max_x'] = max(self.bounds['max_x'], move.x)
        
        if move.y is not None:
            self.bounds['min_y'] = min(self.bounds['min_y'], move.y)
            self.bounds['max_y'] = max(self.bounds['max_y'], move.y)
        
        if move.z is not None:
            self.bounds['min_z'] = min(self.bounds['min_z'], move.z)
            self.bounds['max_z'] = max(self.bounds['max_z'], move.z)

    def get_bounds(self) -> Dict[str, float]:
        """Get bounding box of the toolpath."""
        return self.bounds

    def get_statistics(self) -> Dict[str, any]:
        """Get statistics about the G-code."""
        rapid_moves = sum(1 for m in self.moves if m.is_rapid)
        cutting_moves = sum(1 for m in self.moves if m.is_cutting)
        arc_moves = sum(1 for m in self.moves if m.is_arc)
        
        return {
            'total_moves': len(self.moves),
            'rapid_moves': rapid_moves,
            'cutting_moves': cutting_moves,
            'arc_moves': arc_moves,
            'bounds': self.bounds,
        }

