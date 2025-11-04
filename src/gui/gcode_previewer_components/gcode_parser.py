"""G-code Parser - Parse and extract toolpath data from G-code files."""

import os
import re
import mmap
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
    is_tool_change: bool = False  # M06 tool change
    is_spindle_on: bool = False  # M03/M04 spindle on
    is_spindle_off: bool = False  # M05 spindle off
    tool_number: Optional[int] = None  # Tool number for tool changes
    line_number: int = 0
    raw_command: str = ""

    def get_move_type_name(self) -> str:
        """Get human-readable move type name."""
        if self.is_tool_change:
            return (
                f"Tool Change (T{self.tool_number})"
                if self.tool_number
                else "Tool Change"
            )
        elif self.is_spindle_on:
            return "Spindle On"
        elif self.is_spindle_off:
            return "Spindle Off"
        elif self.is_rapid:
            return "Rapid Move"
        elif self.is_cutting:
            return "Cutting Move"
        elif self.is_arc:
            return "Arc Move"
        return "Unknown"


class GcodeParser:
    """Parse G-code files and extract toolpath information."""

    def __init__(self):
        """Initialize the parser."""
        self.moves: List[GcodeMove] = []
        self.current_position = (0.0, 0.0, 0.0)
        self.current_feed_rate = 0.0
        self.current_spindle_speed = 0.0
        self.current_g_code = 1  # Default to G01 (cutting move)
        self.bounds = {
            "min_x": float("inf"),
            "max_x": float("-inf"),
            "min_y": float("inf"),
            "max_y": float("-inf"),
            "min_z": float("inf"),
            "max_z": float("-inf"),
        }

    def parse_file(
        self, filepath: str, sample_mode: bool = True, sample_size: int = 100
    ) -> List[GcodeMove]:
        """
        Parse a G-code file using true streaming.

        Args:
            filepath: Path to G-code file
            sample_mode: If True, sample large files (first N + last N lines)
            sample_size: Number of lines to sample from start and end (default 100)

        Returns:
            List of parsed moves
        """
        try:
            # Validate file exists and is readable
            if not os.path.exists(filepath):
                raise ValueError(f"File not found: {filepath}")

            file_size = os.path.getsize(filepath)
            if file_size == 0:
                raise ValueError("File is empty")

            # Validate content first
            is_valid, error_msg = self.validate_file_content(filepath)
            if not is_valid:
                raise ValueError(f"Invalid G-code file: {error_msg}")

            # For small files, read normally
            if file_size < 1024 * 1024:  # < 1MB
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                return self.parse_lines(lines)

            # For large files, use streaming
            if sample_mode:
                return self._parse_file_sampled(filepath, sample_size)
            else:
                return self._parse_file_streaming(filepath)

        except Exception as e:
            raise ValueError(f"Failed to parse G-code file: {e}")

    def _parse_file_streaming(self, filepath: str) -> List[GcodeMove]:
        """Parse file line by line without loading entire file into memory."""
        self.moves = []
        self.current_position = (0.0, 0.0, 0.0)
        self.current_g_code = 1

        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()

                if not line or line.startswith(";") or line.startswith("%"):
                    continue

                if ";" in line:
                    line = line.split(";")[0].strip()

                move = self._parse_line(line, line_num)
                if move:
                    self.moves.append(move)
                    self._update_bounds(move)

        return self.moves

    def _parse_file_sampled(self, filepath: str, sample_size: int) -> List[GcodeMove]:
        """Parse file with intelligent sampling - first N and last N lines."""
        with open(filepath, "r+b") as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mmapped_file:
                # Count total lines efficiently
                total_lines = sum(1 for _ in iter(mmapped_file.readline, b""))

                if total_lines <= sample_size * 4:
                    # File is small enough, parse all lines
                    mmapped_file.seek(0)
                    lines = [
                        line.decode("utf-8", errors="ignore") for line in mmapped_file
                    ]
                    return self.parse_lines(lines)

                # Sample first N lines
                mmapped_file.seek(0)
                first_lines = [
                    mmapped_file.readline().decode("utf-8", errors="ignore")
                    for _ in range(sample_size)
                ]

                # Find position of last N lines
                mmapped_file.seek(0, 2)  # Seek to end
                file_size = mmapped_file.tell()

                # Estimate line size and seek to approximate position
                avg_line_size = file_size // total_lines
                seek_pos = max(0, file_size - (sample_size * avg_line_size * 2))
                mmapped_file.seek(seek_pos)

                # Skip partial line
                mmapped_file.readline()

                # Read last N lines
                last_lines = [
                    mmapped_file.readline().decode("utf-8", errors="ignore")
                    for _ in range(sample_size)
                ]

                return self.parse_lines(first_lines + last_lines)

    def validate_file_content(self, filepath: str) -> Tuple[bool, str]:
        """
        Validate file contains G-code content before parsing.

        Args:
            filepath: Path to file

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Read first 1KB to check content
            with open(filepath, "rb") as f:
                header = f.read(1024)

            # Check for binary content (likely not G-code)
            if b"\x00" in header:
                return False, "File appears to be binary, not text G-code"

            # Try to decode as text
            try:
                text_header = header.decode("utf-8", errors="strict")
            except UnicodeDecodeError:
                try:
                    text_header = header.decode("latin-1")
                except:
                    return False, "File encoding not supported"

            # Look for G-code markers in first 1KB
            gcode_markers = ["G0", "G1", "G2", "G3", "M0", "M3", "M5", "M6"]
            has_gcode = any(marker in text_header.upper() for marker in gcode_markers)

            if not has_gcode:
                return False, "File does not appear to contain G-code"

            return True, ""

        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def parse_lines(self, lines: List[str]) -> List[GcodeMove]:
        """Parse G-code lines and extract moves."""
        self.moves = []
        self.current_position = (0.0, 0.0, 0.0)
        self.current_g_code = 1  # Reset to G01

        for line_num, line in enumerate(lines, 1):
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith(";") or line.startswith("%"):
                continue

            # Remove inline comments
            if ";" in line:
                line = line.split(";")[0].strip()

            move = self._parse_line(line, line_num)
            if move:
                self.moves.append(move)
                self._update_bounds(move)

        return self.moves

    def _parse_line(self, line: str, line_num: int) -> Optional[GcodeMove]:
        """Parse a single G-code line."""
        move = GcodeMove(line_number=line_num, raw_command=line)

        # Check for M-codes (tool changes, spindle control, etc.)
        m_match = re.search(r"M(\d+)", line, re.IGNORECASE)
        if m_match:
            m_code = int(m_match.group(1))
            if m_code == 6:  # Tool change
                move.is_tool_change = True
                # Extract tool number if present
                t_match = re.search(r"T(\d+)", line, re.IGNORECASE)
                if t_match:
                    move.tool_number = int(t_match.group(1))
                # Tool changes don't have coordinates, just return the move
                return move
            if m_code in (3, 4):  # Spindle on (M03 CW, M04 CCW)
                move.is_spindle_on = True
                # Extract spindle speed if present
                s_match = re.search(r"S([-+]?\d*\.?\d+)", line, re.IGNORECASE)
                if s_match:
                    self.current_spindle_speed = float(s_match.group(1))
                move.spindle_speed = self.current_spindle_speed
                return move
            if m_code == 5:  # Spindle off
                move.is_spindle_off = True
                return move

        # Extract G-code command
        g_match = re.search(r"G(\d+)", line, re.IGNORECASE)
        if g_match:
            g_code = int(g_match.group(1))
            self.current_g_code = g_code  # Update current G-code
        else:
            # No G-code in this line, use the current G-code (modal command)
            g_code = self.current_g_code
            # If line has no coordinates and no G-code, skip it
            if not re.search(r"[XYZ]", line, re.IGNORECASE):
                return None

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
        x_match = re.search(r"X([-+]?\d*\.?\d+)", line, re.IGNORECASE)
        y_match = re.search(r"Y([-+]?\d*\.?\d+)", line, re.IGNORECASE)
        z_match = re.search(r"Z([-+]?\d*\.?\d+)", line, re.IGNORECASE)

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
        f_match = re.search(r"F([-+]?\d*\.?\d+)", line, re.IGNORECASE)
        if f_match:
            self.current_feed_rate = float(f_match.group(1))
        move.feed_rate = self.current_feed_rate

        s_match = re.search(r"S([-+]?\d*\.?\d+)", line, re.IGNORECASE)
        if s_match:
            self.current_spindle_speed = float(s_match.group(1))
        move.spindle_speed = self.current_spindle_speed

        # Update current position
        self.current_position = (move.x, move.y, move.z)

        return move

    def _update_bounds(self, move: GcodeMove) -> None:
        """Update bounding box with move coordinates."""
        if move.x is not None:
            self.bounds["min_x"] = min(self.bounds["min_x"], move.x)
            self.bounds["max_x"] = max(self.bounds["max_x"], move.x)

        if move.y is not None:
            self.bounds["min_y"] = min(self.bounds["min_y"], move.y)
            self.bounds["max_y"] = max(self.bounds["max_y"], move.y)

        if move.z is not None:
            self.bounds["min_z"] = min(self.bounds["min_z"], move.z)
            self.bounds["max_z"] = max(self.bounds["max_z"], move.z)

    def get_bounds(self) -> Dict[str, float]:
        """Get bounding box of the toolpath."""
        return self.bounds

    def get_statistics(self) -> Dict[str, any]:
        """Get statistics about the G-code."""
        rapid_moves = sum(1 for m in self.moves if m.is_rapid)
        cutting_moves = sum(1 for m in self.moves if m.is_cutting)
        arc_moves = sum(1 for m in self.moves if m.is_arc)
        tool_changes = sum(1 for m in self.moves if m.is_tool_change)
        spindle_on = sum(1 for m in self.moves if m.is_spindle_on)
        spindle_off = sum(1 for m in self.moves if m.is_spindle_off)

        return {
            "total_moves": len(self.moves),
            "rapid_moves": rapid_moves,
            "cutting_moves": cutting_moves,
            "arc_moves": arc_moves,
            "tool_changes": tool_changes,
            "spindle_on": spindle_on,
            "spindle_off": spindle_off,
            "bounds": self.bounds,
        }

    def get_file_line_count(self, filepath: str) -> int:
        """Get total line count in G-code file without parsing."""
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                return sum(1 for _ in f)
        except Exception:
            return 0
