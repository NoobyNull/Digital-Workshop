# P1 Critical Implementation - Quick Reference

**Total Effort**: 5.5-7.5 hours  
**Scope**: P1 Critical items only  
**Status**: Ready to implement

---

## 🎯 THREE P1 CRITICAL ITEMS

### P1.1: Memory Allocation with Manual Override (3-4 hours)

**What**: Fix memory calculation + add manual override capability

**Current**: Fixed thresholds (1GB, 1.5GB, 2GB, 3GB)  
**New**: 50% of available + minimum floor (512MB) + manual override

**Files to Modify**:
- `src/core/application_config.py` - Add override fields
- `src/core/performance_monitor.py` - Change calculation logic
- `src/gui/preferences.py` - Create PerformanceSettingsTab

**New UI**:
```
Performance Settings Tab
├─ Auto (Recommended) - Uses 50% of available
├─ Manual Override - Slider 512MB to 4GB
└─ System Info - Shows total, recommended, current
```

**Key Features**:
- ✅ Auto mode: 50% of available (min 512MB, max 4GB)
- ✅ Manual mode: User-adjustable slider
- ✅ Persists to QSettings
- ✅ Shows system info and recommendations

---

### P1.2: Rename Thumbnails Tab (30 minutes)

**What**: Rename "Thumbnails" → "Image Preferences"

**Why**: Better reflects scope (background + material selection)

**Files to Modify**:
- `src/gui/preferences.py` - Rename class and tab

**Changes**:
- Rename: `ThumbnailSettingsTab` → `ImagePreferencesTab`
- Update: Tab name in PreferencesDialog
- Update: Documentation

---

### P1.3: Layout Edit Mode Documentation (1-2 hours)

**What**: Make Layout Edit Mode discoverable and accessible

**Current**: Feature exists but is hidden

**Files to Modify**:
- `src/gui/main_window.py` - Add menu item + status indicator
- `documentation/HELP.md` - Add documentation

**New Features**:
- ✅ View menu item: "Layout Edit Mode"
- ✅ Keyboard shortcut: Ctrl+Shift+L
- ✅ Status bar indicator: Shows ON/OFF
- ✅ Help documentation: How to use

---

## 📋 IMPLEMENTATION SEQUENCE

### Option A: Sequential (Recommended)
1. **P1.2** (30 min) - Quick win, builds confidence
2. **P1.3** (1-2 hours) - Medium complexity
3. **P1.1** (3-4 hours) - Most complex, fresh mind

### Option B: Parallel
- Start P1.2 and P1.3 in parallel
- Then do P1.1

---

## 📊 FILES AFFECTED

| File | P1.1 | P1.2 | P1.3 | Changes |
|------|------|------|------|---------|
| `src/core/application_config.py` | ✅ | - | - | Add 4 fields |
| `src/core/performance_monitor.py` | ✅ | - | - | Modify calculation |
| `src/gui/preferences.py` | ✅ | ✅ | - | Add tab, rename class |
| `src/gui/main_window.py` | - | - | ✅ | Add menu, status bar |
| `documentation/HELP.md` | - | - | ✅ | Add section |

---

## 🧪 TESTING CHECKLIST

### P1.1 Testing
- [ ] Auto mode: 4GB system → 2GB limit
- [ ] Auto mode: 8GB system → 4GB limit
- [ ] Auto mode: 16GB system → 4GB limit (capped)
- [ ] Manual mode: Set to 1GB, verify used
- [ ] Manual mode: Slider works 512MB-4GB
- [ ] Persistence: Set override, restart app
- [ ] UI: Toggle auto/manual works

### P1.2 Testing
- [ ] Tab name changed
- [ ] Functionality preserved
- [ ] Settings save/load works

### P1.3 Testing
- [ ] Menu item appears in View menu
- [ ] Keyboard shortcut Ctrl+Shift+L works
- [ ] Status bar shows mode
- [ ] Mode persists across restart
- [ ] Help documentation visible

---

## 💾 PERSISTENCE

All settings persist via QSettings:
- `performance/use_manual_override` (bool)
- `performance/manual_memory_override_mb` (int)
- `ui/layout_edit_mode` (bool) - already exists

---

## 🎯 SUCCESS CRITERIA

✅ Memory defaults to 50% of available  
✅ Manual override works and persists  
✅ Layout Edit Mode accessible via menu + shortcut  
✅ Status bar shows layout mode  
✅ Thumbnails tab renamed  
✅ All existing functionality preserved  
✅ No breaking changes  

---

## 📝 NOTES

- All changes are P1 Critical only
- No P2 or P3 items included
- Backward compatible
- User-friendly with clear indicators
- Modular approach allows parallel work

---

## ✅ READY TO IMPLEMENT?

All three items are well-defined and ready to code.

**Proceed with implementation?** (Y/N)

