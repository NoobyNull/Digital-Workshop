# New Preferences Tabs - UI Mockup

## Current Tab Structure (6 tabs)
```
┌─────────────────────────────────────────────────────────┐
│ Window & Layout │ Theming │ Thumbnail │ Performance │ Files │ Advanced │
└─────────────────────────────────────────────────────────┘
```

## Proposed Tab Structure (8 tabs)
```
┌──────────────────────────────────────────────────────────────────────────┐
│ Window & Layout │ Theming │ 3D Viewer │ Thumbnail │ Performance │ Debug │ Files │ Advanced │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 📐 Tab 1: Window & Layout (EXPANDED)

### Current Content
- Reset Window Layout button

### New Content to Add
```
┌─ Window Dimensions ─────────────────────────────────────┐
│ Default window width:        [1200    ] px              │
│ Default window height:       [800     ] px              │
│ Minimum window width:        [800     ] px              │
│ Minimum window height:       [600     ] px              │
│                                                          │
│ ☐ Maximize window on startup                           │
│ ☐ Remember window size on exit                         │
│ ☐ Remember dock positions                             │
│                                                          │
│ [Reset to Defaults]                                    │
└──────────────────────────────────────────────────────────┘

┌─ Dock Widget Defaults ──────────────────────────────────┐
│ Library panel default width:  [300    ] px              │
│ Metadata panel default width: [350    ] px              │
│ Viewer panel default height:  [600    ] px              │
└──────────────────────────────────────────────────────────┘
```

---

## 🎨 Tab 2: 3D Viewer (NEW)

```
┌─ Grid Settings ─────────────────────────────────────────┐
│ ☑ Show grid                                             │
│ Grid color:        [████████] (Color picker)           │
│ Grid size:         [████░░░░] 10.0 units              │
│ Grid spacing:      [████░░░░] 1.0 units               │
└──────────────────────────────────────────────────────────┘

┌─ Ground Plane ──────────────────────────────────────────┐
│ ☑ Show ground plane                                     │
│ Ground color:      [████████] (Color picker)           │
│ Ground offset:     [████░░░░] 0.5 units               │
└──────────────────────────────────────────────────────────┘

┌─ Camera & Interaction ──────────────────────────────────┐
│ Mouse sensitivity: [████░░░░] 1.0x                     │
│ Zoom speed:        [████░░░░] 1.0x                     │
│ Pan speed:         [████░░░░] 1.0x                     │
│ FPS limit:         [Unlimited ▼]                       │
│ Interactor style:  [Trackball ▼]                       │
│ ☑ Auto-fit on model load                              │
└──────────────────────────────────────────────────────────┘

┌─ Lighting (Advanced) ───────────────────────────────────┐
│ Default light position:                                 │
│   X: [100  ]  Y: [100  ]  Z: [100  ]                  │
│ Default light color:   [████████] (Color picker)       │
│ Default intensity:     [████░░░░] 0.8                 │
│ Cone angle:            [████░░░░] 30°                 │
│ ☑ Enable fill light                                    │
│ Fill light intensity:  [██░░░░░░] 0.3                 │
└──────────────────────────────────────────────────────────┘

┌─ Rendering ─────────────────────────────────────────────┐
│ ☑ Show model edges                                      │
│ ☐ Wireframe mode                                        │
│ ☑ Ambient occlusion                                     │
│ Specular highlights:   [████░░░░] 0.8                 │
└──────────────────────────────────────────────────────────┘
```

---

## 🐛 Tab 3: Debug (NEW)

```
┌─ Logging ───────────────────────────────────────────────┐
│ Log level:         [DEBUG ▼]                            │
│ ☑ Enable file logging                                   │
│ Log retention:     [30 ▼] days                         │
│ Log location:      [C:\Users\...\AppData\...]          │
│ [Open Log Folder]  [Clear Logs]                        │
└──────────────────────────────────────────────────────────┘

┌─ Feature Flags (⚠️ Restart Required) ──────────────────┐
│ ☑ Hardware acceleration                                 │
│ ☑ High DPI support                                      │
│ ☑ Performance monitoring                                │
│                                                          │
│ ⚠️ Changes require application restart                 │
└──────────────────────────────────────────────────────────┘

┌─ Performance Thresholds ────────────────────────────────┐
│ FPS warning threshold:    [30 ▼] FPS                   │
│ Memory warning threshold: [████░░░░] 80%               │
│ Cache eviction threshold: [████░░░░] 90%               │
└──────────────────────────────────────────────────────────┘

┌─ System Information ────────────────────────────────────┐
│ System RAM:        127.7 GB                             │
│ Available RAM:     79.1 GB                              │
│ CPU Cores:         24                                   │
│ GPU:               NVIDIA GeForce RTX 3090              │
│ GPU VRAM:          32 GB                                │
│ Performance Level: Ultra                                │
└──────────────────────────────────────────────────────────┘
```

---

## 📊 Tab 4: Performance (EXPANDED)

### Current Content
- Memory allocation (auto/manual)
- System info display

### New Content to Add
```
┌─ Cache Settings ────────────────────────────────────────┐
│ Model cache size:  [████░░░░] 1024 MB                 │
│ ☑ Enable compression                                    │
│ ☑ Auto-cleanup on exit                                │
└──────────────────────────────────────────────────────────┘

┌─ Thumbnail Generation ──────────────────────────────────┐
│ Thumbnail quality: [████░░░░] High                     │
│ Thumbnail size:    [████░░░░] 256x256 px              │
│ ☑ Generate in background                              │
│ Max concurrent:    [4 ▼] thumbnails                   │
└──────────────────────────────────────────────────────────┘
```

---

## 🎯 Implementation Priority

### Phase 1 (Week 1-2): High Priority
- ✅ Window & Layout (expand)
- ✅ 3D Viewer (new)

### Phase 2 (Week 2-3): Medium Priority
- ✅ Debug (new)
- ✅ Performance (expand)

### Phase 3 (Week 3-4): Polish
- ✅ Validation & error handling
- ✅ Settings persistence
- ✅ Testing & refinement

---

## 🔄 Settings Flow

```
User Changes Setting
        ↓
UI Control Updated
        ↓
Save to QSettings
        ↓
Update ApplicationConfig
        ↓
Component Reads Config
        ↓
Visual Change Applied
```

---

## 💾 Example: Grid Color Setting

```python
# UI: User picks color via color picker
color = QColorDialog.getColor()

# Save to QSettings
settings = QSettings()
settings.setValue("viewer/grid_color", color.name())

# Load in VTK Scene Manager
grid_color = settings.value("viewer/grid_color", "#CCCCCC")

# Apply to grid actor
grid_actor.GetProperty().SetColor(
    int(grid_color[1:3], 16) / 255.0,
    int(grid_color[3:5], 16) / 255.0,
    int(grid_color[5:7], 16) / 255.0
)
```


