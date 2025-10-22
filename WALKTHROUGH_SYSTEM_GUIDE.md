# 3D-MM Walkthrough & Tutorial System

## Overview

The walkthrough system provides new users with guided introduction to 3D-MM features through:
- **Welcome message** on first launch
- **Startup tips dialog** with quick start guide
- **Contextual help widgets** throughout the UI
- **Tutorial tips** organized by category

## Components

### 1. `src/gui/walkthrough.py`
Core walkthrough management system with 13 tutorial tips organized by category.

**Key Classes:**
- `TutorialTip`: Data class for individual tips (title, content, category, emoji)
- `WalkthroughManager`: Central manager for all tips and welcome messages
- `WalkthroughDialog`: Dialog for displaying tips with navigation

**Features:**
- 13 pre-written tips covering all major features
- Tips organized in 5 categories:
  - `getting_started`: Initial setup and basics
  - `3d_viewer`: 3D viewing and interaction
  - `library`: Model browsing and organization
  - `metadata`: Editing model information
  - `advanced`: Performance and customization

### 2. `src/gui/startup_tips.py`
Startup experience and contextual help system.

**Key Classes:**
- `StartupTipsDialog`: Welcome dialog shown on first launch
- `ContextualHelpWidget`: Reusable help widget for UI integration

**Features:**
- Shows 3 random tips on startup
- "Don't show again" checkbox
- "View All Tips" button for full tutorial
- Persistent user preference storage

### 3. Integration in `src/gui/main_window.py`
Main window integration for automatic startup tips display.

**Implementation:**
- `showEvent()`: Triggers tips on first window show
- `_show_startup_tips()`: Displays dialog if enabled
- Respects user preference for future launches

## Tutorial Tips Content

### Getting Started (2 tips)
1. **Welcome to 3D-MM!** - Overview and initial setup
2. **Drag & Drop Models** - Quick file loading method

### 3D Viewer (4 tips)
1. **Rotate Your Model** - Camera controls
2. **Lighting Control** - Adjusting lights and persistence
3. **Material & Appearance** - Materials, grid, reset view
4. **Save Your View** - Screenshot functionality

### Model Library (3 tips)
1. **Search Your Models** - Quick search across metadata
2. **Organize with Categories** - Category system
3. **Thumbnail Settings** - Customizing thumbnail generation

### Metadata (2 tips)
1. **Edit Model Metadata** - Adding descriptions and tags
2. **Star Ratings** - Rating system for organization

### Advanced (2 tips)
1. **Performance Settings** - Memory optimization
2. **Theme Customization** - 19 Material Design themes
3. **System Reset** - Complete reset functionality

## Usage Examples

### Show a Random Tip
```python
from src.gui.walkthrough import WalkthroughDialog

dialog = WalkthroughDialog(parent_widget)
dialog.exec()
```

### Get Tips by Category
```python
from src.gui.walkthrough import WalkthroughManager

tips = WalkthroughManager.get_tips_by_category("3d_viewer")
for tip in tips:
    print(f"{tip.icon_emoji} {tip.title}: {tip.content}")
```

### Show Startup Tips
```python
from src.gui.startup_tips import StartupTipsDialog

if StartupTipsDialog.should_show_on_startup():
    dialog = StartupTipsDialog(parent_widget)
    dialog.exec()
    if not dialog.should_show_again():
        StartupTipsDialog.save_preference(False)
```

### Add Contextual Help to UI
```python
from src.gui.startup_tips import ContextualHelpWidget

help_widget = ContextualHelpWidget(
    title="Model Library",
    content="Drag and drop 3D models here to load them quickly.",
    parent=parent_widget
)
layout.addWidget(help_widget)
```

## Tip Structure

Each tip follows a consistent format:

```python
TutorialTip(
    title="Feature Name",
    content="2-4 sentence explanation of the feature and how to use it.",
    category="category_name",
    icon_emoji="🎯"
)
```

**Guidelines for Content:**
- Keep content to 2-4 sentences maximum
- Focus on practical usage, not technical details
- Include keyboard shortcuts or UI elements when relevant
- Use friendly, encouraging tone
- Provide actionable steps

## Adding New Tips

To add a new tip:

1. Open `src/gui/walkthrough.py`
2. Add to the `TIPS` list in `WalkthroughManager`:

```python
TutorialTip(
    title="Your Feature",
    content="Your 2-4 sentence description.",
    category="category_name",
    icon_emoji="🎯"
)
```

3. Choose appropriate category or create new one
4. Test with `WalkthroughDialog`

## User Preferences

Startup tips preference is stored in QSettings:
- **Key**: `show_startup_tips`
- **Default**: `True` (show on first run)
- **Type**: Boolean

Users can disable via checkbox in `StartupTipsDialog`.

## Future Enhancements

Potential improvements:
- Video tutorials for complex features
- Interactive step-by-step walkthroughs
- Context-sensitive help based on current UI
- Keyboard shortcut reference
- Feature discovery notifications
- Tip scheduling (show different tips over time)

## Testing

To test the walkthrough system:

```bash
# Run application normally
python src/main.py

# Startup tips should appear on first launch
# Click "View All Tips" to see full tutorial
# Check "Don't show again" to disable for future launches
```

To reset and see tips again:
- Delete QSettings or manually set `show_startup_tips` to `True`
- Or use Preferences > Advanced > Complete System Reset


