"""Animation Controller - Manages playback of G-code toolpath animation."""

from typing import List, Optional, Callable
from enum import Enum
from PySide6.QtCore import QTimer, Signal, QObject

from .gcode_parser import GcodeMove


class PlaybackState(Enum):
    """Playback state enumeration."""
    STOPPED = 0
    PLAYING = 1
    PAUSED = 2


class AnimationController(QObject):
    """Controls animation playback of G-code toolpath."""
    
    # Signals
    frame_changed = Signal(int)  # Emits current frame index
    state_changed = Signal(PlaybackState)  # Emits playback state
    speed_changed = Signal(float)  # Emits playback speed
    
    def __init__(self):
        """Initialize the animation controller."""
        super().__init__()
        
        self.moves: List[GcodeMove] = []
        self.current_frame = 0
        self.state = PlaybackState.STOPPED
        self.speed = 1.0  # 1.0 = normal speed
        
        # Timer for animation
        self.timer = QTimer()
        self.timer.timeout.connect(self._on_timer_tick)
        self.frame_interval = 50  # ms per frame
    
    def set_moves(self, moves: List[GcodeMove]) -> None:
        """Set the moves to animate."""
        self.moves = moves
        self.current_frame = 0
        self.state = PlaybackState.STOPPED
    
    def play(self) -> None:
        """Start playback."""
        if not self.moves:
            return
        
        self.state = PlaybackState.PLAYING
        self.state_changed.emit(self.state)
        
        # Calculate interval based on speed
        interval = int(self.frame_interval / self.speed)
        self.timer.start(interval)
    
    def pause(self) -> None:
        """Pause playback."""
        self.timer.stop()
        self.state = PlaybackState.PAUSED
        self.state_changed.emit(self.state)
    
    def stop(self) -> None:
        """Stop playback and reset to beginning."""
        self.timer.stop()
        self.current_frame = 0
        self.state = PlaybackState.STOPPED
        self.state_changed.emit(self.state)
        self.frame_changed.emit(self.current_frame)
    
    def set_frame(self, frame: int) -> None:
        """Jump to a specific frame."""
        self.current_frame = max(0, min(frame, len(self.moves) - 1))
        self.frame_changed.emit(self.current_frame)
    
    def set_speed(self, speed: float) -> None:
        """Set playback speed (1.0 = normal, 2.0 = 2x, 0.5 = half)."""
        self.speed = max(0.1, min(speed, 5.0))  # Clamp between 0.1x and 5x
        self.speed_changed.emit(self.speed)
        
        # Update timer interval if playing
        if self.state == PlaybackState.PLAYING:
            interval = int(self.frame_interval / self.speed)
            self.timer.setInterval(interval)
    
    def next_frame(self) -> None:
        """Advance to next frame."""
        if self.current_frame < len(self.moves) - 1:
            self.current_frame += 1
            self.frame_changed.emit(self.current_frame)
    
    def prev_frame(self) -> None:
        """Go to previous frame."""
        if self.current_frame > 0:
            self.current_frame -= 1
            self.frame_changed.emit(self.current_frame)
    
    def _on_timer_tick(self) -> None:
        """Handle timer tick for animation."""
        self.next_frame()
        
        # Stop at end
        if self.current_frame >= len(self.moves) - 1:
            self.stop()
    
    def get_current_move(self) -> Optional[GcodeMove]:
        """Get the current move being displayed."""
        if 0 <= self.current_frame < len(self.moves):
            return self.moves[self.current_frame]
        return None
    
    def get_moves_up_to_frame(self, frame: int) -> List[GcodeMove]:
        """Get all moves up to and including the specified frame."""
        return self.moves[:frame + 1]
    
    def get_total_frames(self) -> int:
        """Get total number of frames."""
        return len(self.moves)
    
    def get_state(self) -> PlaybackState:
        """Get current playback state."""
        return self.state
    
    def get_speed(self) -> float:
        """Get current playback speed."""
        return self.speed

