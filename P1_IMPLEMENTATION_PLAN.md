# P1 Critical Implementation Plan

**Scope**: Priority 1 Critical items only  
**Date**: 2025-10-18  
**Status**: Plan Ready for Review

---

## 🎯 OVERVIEW

Three P1 Critical items to implement:

| Item | Effort | Impact | Complexity |
|------|--------|--------|-----------|
| **P1.1: Memory Allocation + Manual Override** | 3-4h | High | High |
| **P1.2: Rename Thumbnails Tab** | 30m | Low | Low |
| **P1.3: Layout Edit Mode Documentation** | 1-2h | Medium | Medium |
| **TOTAL** | **4.5-6.5h** | - | - |

---

## 📋 P1.1: MEMORY ALLOCATION WITH MANUAL OVERRIDE

### Problem
- Current: Fixed thresholds (1GB, 1.5GB, 2GB, 3GB)
- Required: 50% of available resources + minimum floor
- New: Manual override capability

### Solution Architecture

```
User Settings (QSettings)
    ↓
ApplicationConfig (manual_memory_override_mb, use_manual_override)
    ↓
PerformanceMonitor.detect_system_capabilities()
    ↓
Returns: max_memory_mb (respects manual override if set)
```

### Files to Modify

**1. src/core/application_config.py**
- Add: `use_manual_memory_override: bool = False`
- Add: `manual_memory_override_mb: Optional[int] = None`
- Add: `min_memory_specification_mb: int = 512`
- Add: `max_memory_cap_mb: int = 4096`

**2. src/core/performance_monitor.py**
- Modify: `detect_system_capabilities()` method
- Change calculation from fixed thresholds to:
  ```python
  available_mb = total_memory_gb * 1024 / 2
  min_spec = config.min_memory_specification_mb
  max_cap = config.max_memory_cap_mb
  
  if config.use_manual_memory_override and config.manual_memory_override_mb:
      max_memory_mb = config.manual_memory_override_mb
  else:
      max_memory_mb = max(available_mb, min_spec)
      max_memory_mb = min(max_memory_mb, max_cap)
  ```

**3. src/gui/preferences.py**
- Add: `PerformanceSettingsTab` class (~80 lines)
  - Toggle: "Auto" vs "Manual"
  - Slider: 512MB - 4GB (manual mode)
  - Display: System memory, recommended value
  - Display: Current usage (if available)
- Modify: `PreferencesDialog.__init__()` to add tab
- Modify: `_save_and_notify()` to save performance settings

### New UI Tab: PerformanceSettingsTab

```
┌─────────────────────────────────────┐
│ Performance Settings                │
├─────────────────────────────────────┤
│                                     │
│ Memory Management                   │
│ ┌─────────────────────────────────┐ │
│ │ ○ Auto (Recommended)            │ │
│ │   Uses 50% of available memory  │ │
│ │   Minimum: 512 MB               │ │
│ │   Maximum: 4 GB                 │ │
│ │                                 │ │
│ │ ○ Manual Override               │ │
│ │   Memory Limit: [====●====] MB  │ │
│ │   512 MB ←────────→ 4096 MB     │ │
│ │                                 │ │
│ │ System Information:             │ │
│ │ • Total Memory: 16 GB           │ │
│ │ • Recommended: 8 GB (50%)       │ │
│ │ • Current Limit: 8 GB           │ │
│ │                                 │ │
│ └─────────────────────────────────┘ │
│                                     │
└─────────────────────────────────────┘
```

### Implementation Steps

1. **Update ApplicationConfig** (15 min)
   - Add 4 new fields
   - Add getter method for effective memory limit

2. **Update PerformanceMonitor** (45 min)
   - Modify calculation logic
   - Add config integration
   - Test with different hardware profiles

3. **Create PerformanceSettingsTab** (90 min)
   - Create UI layout
   - Add toggle logic
   - Add slider logic
   - Add display updates
   - Connect to save/load

4. **Integrate into PreferencesDialog** (30 min)
   - Add tab to dialog
   - Add save/load logic
   - Test persistence

---

## 📋 P1.2: RENAME THUMBNAILS TAB

### Problem
- Current name: "Thumbnails"
- Better name: "Image Preferences"
- Reflects broader scope (background + material)

### Files to Modify

**1. src/gui/preferences.py**
- Rename: `ThumbnailSettingsTab` → `ImagePreferencesTab`
- Update: Tab name in PreferencesDialog (line 67)
- Update: Any internal references

### Implementation Steps

1. **Rename class** (5 min)
   - Find/replace ThumbnailSettingsTab → ImagePreferencesTab

2. **Update tab registration** (5 min)
   - Update PreferencesDialog.__init__()

3. **Update documentation** (20 min)
   - Update any docstrings
   - Update comments

---

## 📋 P1.3: LAYOUT EDIT MODE DOCUMENTATION

### Problem
- Layout Edit Mode exists but is undocumented
- No menu access
- No keyboard shortcut
- No status indicator

### Solution

**1. Add Menu Item**
- Location: View menu (or Edit menu)
- Label: "Layout Edit Mode"
- Shortcut: Ctrl+Shift+L
- Type: Checkable toggle
- Shows current state

**2. Add Status Bar Indicator**
- Location: Status bar (right side)
- Shows: "Layout Edit Mode: ON" or "Layout Edit Mode: OFF"
- Updates when mode changes

**3. Update Help**
- Add section: "Customizing Layout"
- Document: How to enable/disable
- Document: What you can do in edit mode

### Files to Modify

**1. src/gui/main_window.py**
- Modify: `_setup_menu_bar()` or `_setup_view_menu()`
- Add: Layout Edit Mode action
- Add: Keyboard shortcut
- Connect: To existing `_set_layout_edit_mode()` method

**2. src/gui/main_window.py** (status bar)
- Add: Status bar label for layout mode
- Update: When mode changes

**3. documentation/HELP.md** (or similar)
- Add: Section about Layout Edit Mode
- Add: Keyboard shortcut reference

### Implementation Steps

1. **Add View menu item** (30 min)
   - Create action
   - Add shortcut
   - Connect to handler
   - Update handler to update status

2. **Add status bar indicator** (30 min)
   - Create label
   - Update on mode change
   - Style appropriately

3. **Update help documentation** (30 min)
   - Add section
   - Add screenshots/examples
   - Add to keyboard shortcuts reference

---

## 🔄 IMPLEMENTATION ORDER

### Phase 1: Independent Items (Can do in parallel)
- **P1.2**: Rename Thumbnails Tab (30 min)
- **P1.3**: Layout Edit Mode Documentation (1-2 hours)

### Phase 2: Dependent Item (After Phase 1)
- **P1.1**: Memory Allocation (3-4 hours)
  - Depends on: Nothing, but most complex

### Recommended Sequence
1. Start P1.2 (quick win)
2. Start P1.3 (medium effort)
3. Complete P1.1 (most complex)

---

## 📊 TESTING APPROACH

### P1.1 Testing
- [ ] Test auto calculation with 4GB system
- [ ] Test auto calculation with 8GB system
- [ ] Test auto calculation with 16GB system
- [ ] Test manual override (set to 1GB, verify it's used)
- [ ] Test persistence (set override, restart app)
- [ ] Test UI updates when toggling auto/manual
- [ ] Test slider bounds (512MB - 4GB)

### P1.2 Testing
- [ ] Verify tab name changed
- [ ] Verify functionality still works
- [ ] Verify settings still save/load

### P1.3 Testing
- [ ] Test menu item appears
- [ ] Test keyboard shortcut works
- [ ] Test status bar updates
- [ ] Test mode persists across restart

---

## 📈 TIMELINE

| Task | Effort | Start | End |
|------|--------|-------|-----|
| P1.2 Rename | 30m | Day 1 | Day 1 |
| P1.3 Layout Mode | 1-2h | Day 1 | Day 1 |
| P1.1 Memory | 3-4h | Day 1-2 | Day 2 |
| Testing | 1-2h | Day 2 | Day 2 |
| **TOTAL** | **5.5-7.5h** | - | - |

---

## ✅ DELIVERABLES

1. ✅ Modified ApplicationConfig with memory override fields
2. ✅ Updated PerformanceMonitor with 50% calculation
3. ✅ New PerformanceSettingsTab in Preferences
4. ✅ Renamed ImagePreferencesTab
5. ✅ Layout Edit Mode menu item + shortcut
6. ✅ Status bar indicator for layout mode
7. ✅ Updated help documentation
8. ✅ All tests passing
9. ✅ Settings persist across restarts

---

## 🎯 SUCCESS CRITERIA

- ✅ Memory defaults to 50% of available (with 512MB floor)
- ✅ Users can manually override memory limit
- ✅ Manual override persists across restarts
- ✅ Layout Edit Mode accessible via menu + keyboard shortcut
- ✅ Status bar shows current layout mode
- ✅ Thumbnails tab renamed to Image Preferences
- ✅ All existing functionality preserved
- ✅ No breaking changes

---

## 📝 NOTES

- All changes stay within P1 Critical scope
- No P2 or P3 items included
- Modular approach allows parallel work
- Backward compatible (existing settings still work)
- User-friendly with clear UI indicators

---

**Status**: ✅ **PLAN READY FOR IMPLEMENTATION**

Ready to proceed? Confirm and I'll begin implementation.

