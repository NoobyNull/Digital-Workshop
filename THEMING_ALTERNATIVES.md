# Qt Theming Framework Alternatives to qt-material

## Overview
qt-material has compatibility issues on Python 3.12+ (import as `qt_material` not `qtmaterial`). Here are viable alternatives:

---

## 1. **QDarkStyleSheet** ⭐ RECOMMENDED
**Status:** Most mature, actively maintained  
**GitHub:** https://github.com/ColinDuquesnoy/QDarkStyleSheet  
**Stars:** 3k+

### Pros:
- ✅ Supports Qt4, Qt5, Qt6 (PyQt4, PyQt5, PyQt6, PySide, PySide2, PySide6)
- ✅ Works with Python 2 & 3 (though Python 2 support deprecated)
- ✅ Dark AND light themes included
- ✅ Theme framework (v3) with customizable palettes
- ✅ SCSS support for programmatic color access
- ✅ Extensive widget coverage
- ✅ Active maintenance (latest: v3.2.3, Nov 2023)
- ✅ MIT License

### Cons:
- Requires QtPy or direct Qt binding specification
- Slightly less "Material Design" aesthetic than qt-material

### Installation:
```bash
pip install qdarkstyle
```

### Usage:
```python
import qdarkstyle
from PySide6.QtWidgets import QApplication

app = QApplication(sys.argv)
app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyside6'))
```

---

## 2. **PyQtDarkTheme**
**GitHub:** https://github.com/5yutan5/PyQtDarkTheme  
**Status:** Active, modern

### Pros:
- ✅ Flat dark theme design
- ✅ Supports PySide2, PySide6, PyQt5, PyQt6
- ✅ Lightweight and simple
- ✅ MIT License
- ✅ Good for modern flat UI designs

### Cons:
- Primarily dark theme focused
- Smaller community than QDarkStyleSheet

### Installation:
```bash
pip install PyQtDarkTheme
```

### Usage:
```python
import darktheme
from PySide6.QtWidgets import QApplication

app = QApplication(sys.argv)
darktheme.apply_stylesheet(app)
```

---

## 3. **Qt Advanced Stylesheets (QTASS)**
**GitHub:** https://github.com/githubuser0xFFFF/Qt-Advanced-Stylesheets  
**Python Version:** qtass-pyside6

### Pros:
- ✅ Advanced theming with CSS-like syntax
- ✅ Professional appearance
- ✅ Comprehensive widget styling
- ✅ SVG icon support

### Cons:
- Less documentation than QDarkStyleSheet
- Smaller community

---

## 4. **PyDracula**
**GitHub:** https://github.com/Wanderson-Magalhaes/PyDracula  
**Status:** Modern GUI framework

### Pros:
- ✅ Modern, complete GUI framework
- ✅ PySide6/PyQt6 focused
- ✅ Beautiful dark theme
- ✅ Includes UI components

### Cons:
- More of a framework than just theming
- Steeper learning curve

---

## 5. **Built-in Qt Theming (Qt 6.5+)**
**Status:** Native to Qt

### Pros:
- ✅ No external dependencies
- ✅ System-aware theming
- ✅ Native look and feel

### Cons:
- Limited customization
- Requires Qt 6.5+
- Platform-dependent appearance

### Usage:
```python
import sys
sys.argv += ['-platform', 'windows:darkmode=2']
app = QApplication(sys.argv)
```

---

## Comparison Table

| Feature | QDarkStyleSheet | PyQtDarkTheme | QTASS | PyDracula | qt-material |
|---------|-----------------|---------------|-------|-----------|------------|
| **Python 3.12 Support** | ✅ | ✅ | ✅ | ✅ | ❌ (import issue) |
| **Dark Theme** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Light Theme** | ✅ | ❌ | ✅ | ❌ | ✅ |
| **Customizable** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Maintenance** | Active | Active | Active | Active | Stalled |
| **Community** | Large | Medium | Small | Medium | Large |
| **Ease of Use** | Easy | Very Easy | Medium | Medium | Easy |
| **Material Design** | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## Recommendation

**For your 3D-MM project:**

### Primary Choice: **QDarkStyleSheet**
- Most mature and stable
- Best Python 3.12 compatibility
- Extensive widget support
- Active maintenance
- Easy migration from qt-material

### Migration Path:
1. Replace `import qt_material` with `import qdarkstyle`
2. Update theme application code
3. Adjust color palette if needed
4. Test with existing VTK integration

### Secondary Choice: **PyQtDarkTheme**
- If you prefer simpler, flatter design
- Lighter weight
- Easier setup

---

## Migration Example

### Current (qt-material):
```python
import qt_material
app.setStyleSheet(qt_material.apply_stylesheet(app, theme='dark_teal'))
```

### New (QDarkStyleSheet):
```python
import qdarkstyle
app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyside6'))
```

---

## Notes
- All alternatives support PySide6 and PyQt6
- QDarkStyleSheet is the safest choice for long-term maintenance
- Consider your specific design requirements (Material vs. flat design)
- VTK integration should work with any stylesheet framework

