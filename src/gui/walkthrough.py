"""
Application walkthrough and tutorial system.

Provides welcome messages, startup tips, and contextual help for new users.
"""

from dataclasses import dataclass
from typing import List, Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QCheckBox, QScrollArea, QWidget, QFrame
)
from PySide6.QtGui import QFont, QPixmap


@dataclass
class TutorialTip:
    """A single tutorial tip or hint."""
    title: str
    content: str  # 2-4 sentence description
    category: str  # "getting_started", "3d_viewer", "library", "metadata", "advanced"
    icon_emoji: str = "💡"


class WalkthroughManager:
    """Manages application walkthrough and tutorial content."""
    
    TIPS = [
        # Getting Started
        TutorialTip(
            title="Welcome to Digital Workshop!",
            content="Digital Workshop is your personal 3D model organizer. Start by adding a folder containing your 3D models in the Files tab. The app will automatically scan and catalog all supported formats (STL, OBJ, 3MF, STEP).",
            category="getting_started",
            icon_emoji="👋"
        ),
        TutorialTip(
            title="Drag & Drop Models",
            content="You can drag and drop 3D model files directly into the Model Library panel. The app will automatically load them and generate thumbnails for quick preview.",
            category="getting_started",
            icon_emoji="🎯"
        ),
        
        # 3D Viewer
        TutorialTip(
            title="Rotate Your Model",
            content="Click and drag in the 3D viewer to rotate your model. Use the mouse wheel to zoom in/out. Right-click and drag to pan the view. The grid helps with orientation.",
            category="3d_viewer",
            icon_emoji="🔄"
        ),
        TutorialTip(
            title="Lighting Control",
            content="Click the 'Lighting' button to adjust light position, color, and intensity. These settings persist across sessions, so your preferred lighting is always remembered.",
            category="3d_viewer",
            icon_emoji="💡"
        ),
        TutorialTip(
            title="Material & Appearance",
            content="Use the 'Material' button to apply wood textures and materials to your models. The 'Grid' toggle shows/hides the reference grid. 'Reset View' returns to the default camera angle.",
            category="3d_viewer",
            icon_emoji="🎨"
        ),
        TutorialTip(
            title="Save Your View",
            content="Click the camera icon to save the current 3D view as a screenshot. This is useful for creating reference images or sharing your models with others.",
            category="3d_viewer",
            icon_emoji="📸"
        ),
        
        # Model Library
        TutorialTip(
            title="Search Your Models",
            content="Use the search bar in the Model Library to quickly find models by name, category, or tags. Search is instant and searches across all metadata fields.",
            category="library",
            icon_emoji="🔍"
        ),
        TutorialTip(
            title="Organize with Categories",
            content="Assign categories to your models (e.g., 'Miniatures', 'Terrain', 'Props'). This helps organize large collections and makes searching more efficient.",
            category="library",
            icon_emoji="📁"
        ),
        TutorialTip(
            title="Thumbnail Settings",
            content="Customize how thumbnails are generated in Preferences > Thumbnail Settings. Choose background images and materials to match your workflow.",
            category="library",
            icon_emoji="🖼️"
        ),
        
        # Metadata
        TutorialTip(
            title="Edit Model Metadata",
            content="Click on a model and use the Metadata Editor to add descriptions, tags, and ratings. This information is saved to the database and helps with organization.",
            category="metadata",
            icon_emoji="📝"
        ),
        TutorialTip(
            title="Star Ratings",
            content="Use the star rating system to mark your favorite models or rate quality. This is useful for quick filtering and finding your best models.",
            category="metadata",
            icon_emoji="⭐"
        ),
        
        # Advanced
        TutorialTip(
            title="Performance Settings",
            content="If the app feels slow, check Preferences > Performance. You can manually limit memory usage or let the app auto-calculate based on your system.",
            category="advanced",
            icon_emoji="⚙️"
        ),
        TutorialTip(
            title="Theme Customization",
            content="Customize the app appearance in Preferences > Theming. Choose between Dark, Light, or Auto (system) mode with 19 different Material Design color variants.",
            category="advanced",
            icon_emoji="🎨"
        ),
        TutorialTip(
            title="System Reset",
            content="In Preferences > Advanced, you can perform a complete system reset. This clears all settings, cache, and database. Use with caution!",
            category="advanced",
            icon_emoji="🔄"
        ),
    ]
    
    @classmethod
    def get_welcome_message(cls) -> str:
        """Get the welcome message for first-time users."""
        return (
            "Welcome to Digital Workshop - Your Personal Digital Workshop!\n\n"
            "Quick Start:\n"
            "1. Add a folder with your 3D models (Files tab)\n"
            "2. Browse and select models in the Library\n"
            "3. View in 3D, edit metadata, and organize\n\n"
            "💡 Tip: Check the Help menu for tutorials and tips!"
        )
    
    @classmethod
    def get_tips_by_category(cls, category: str) -> List[TutorialTip]:
        """Get all tips for a specific category."""
        return [tip for tip in cls.TIPS if tip.category == category]
    
    @classmethod
    def get_random_tip(cls) -> TutorialTip:
        """Get a random tip for the startup message."""
        import random
        return random.choice(cls.TIPS)


class WalkthroughDialog(QDialog):
    """Dialog for displaying walkthrough and tutorial content."""

    def __init__(self, parent=None, tip: Optional[TutorialTip] = None):
        super().__init__(parent)
        self.setWindowTitle("Digital Workshop Tutorial")
        self.setMinimumWidth(500)
        self.setMinimumHeight(300)
        self.setModal(True)

        self.tip = tip or WalkthroughManager.get_random_tip()
        self.main_layout = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the dialog UI."""
        # Clear existing layout if present
        if self.main_layout is not None:
            while self.main_layout.count():
                child = self.main_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        else:
            self.main_layout = QVBoxLayout(self)
            self.main_layout.setContentsMargins(20, 20, 20, 20)
            self.main_layout.setSpacing(15)

        layout = self.main_layout
        
        # Header with emoji and title
        header_layout = QHBoxLayout()
        emoji_label = QLabel(self.tip.icon_emoji)
        emoji_label.setFont(QFont("Arial", 32))
        header_layout.addWidget(emoji_label)
        
        title_label = QLabel(self.tip.title)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Content
        content_label = QLabel(self.tip.content)
        content_label.setWordWrap(True)
        content_label.setFont(QFont("Arial", 10))
        layout.addWidget(content_label)
        
        # Category badge
        category_label = QLabel(f"Category: {self.tip.category.replace('_', ' ').title()}")
        category_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(category_label)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        next_btn = QPushButton("Next Tip")
        next_btn.clicked.connect(self._show_next_tip)
        button_layout.addWidget(next_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        # Don't show again checkbox
        self.dont_show_checkbox = QCheckBox("Don't show tips on startup")
        layout.addWidget(self.dont_show_checkbox)
    
    def _show_next_tip(self) -> None:
        """Show the next random tip."""
        self.tip = WalkthroughManager.get_random_tip()
        self._setup_ui()
    
    def should_show_again(self) -> bool:
        """Check if tips should be shown on startup."""
        return not self.dont_show_checkbox.isChecked()

