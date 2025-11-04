# Digital Workshop - Troubleshooting & FAQ

## 🆘 Troubleshooting Guide

### Installation Issues

#### Problem: Installation Fails
**Symptoms**: Installation stops or shows error

**Solutions**:
1. Check disk space (need ~2GB)
2. Verify Python version (3.8-3.12)
3. Run as administrator
4. Check antivirus settings
5. Review installation logs

**Log Location**: `AppData\Local\DigitalWorkshop\logs\`

#### Problem: Module Installation Incomplete
**Symptoms**: Some modules missing after install

**Solutions**:
1. Run installer again
2. Use Patch mode to update
3. Check internet connection
4. Verify file permissions
5. Contact support

#### Problem: Database Initialization Fails
**Symptoms**: "Database error" on startup

**Solutions**:
1. Delete corrupted database
2. Reinstall application
3. Check disk space
4. Verify file permissions
5. Check antivirus

---

### Application Issues

#### Problem: Application Won't Start
**Symptoms**: Application crashes on launch

**Solutions**:
1. Check Python installation
2. Verify dependencies installed
3. Check system requirements
4. Review error logs
5. Try clean install

**Check Requirements**:
```bash
python --version  # Should be 3.8-3.12
pip list | grep -E "PySide6|VTK|OpenCV|NumPy"
```

#### Problem: Slow Performance
**Symptoms**: Application runs slowly

**Solutions**:
1. Close unused projects
2. Clear thumbnail cache
3. Reduce model complexity
4. Check system resources
5. Update graphics drivers

**Clear Cache**:
```
AppData\Local\DigitalWorkshop\cache\
```

#### Problem: Memory Usage High
**Symptoms**: Application uses excessive memory

**Solutions**:
1. Close large projects
2. Reduce viewport resolution
3. Disable thumbnails
4. Restart application
5. Check for memory leaks

---

### File & Project Issues

#### Problem: Model Won't Import
**Symptoms**: Import fails or model doesn't appear

**Solutions**:
1. Verify file format (STL, OBJ, STEP, 3MF, PLY)
2. Check file integrity
3. Verify file size < 500MB
4. Try different format
5. Check error message

**Supported Formats**:
- STL (Stereolithography)
- OBJ (Wavefront)
- STEP/STP (CAD)
- 3MF (3D Manufacturing)
- PLY (Polygon)

#### Problem: DWW Export Fails
**Symptoms**: Export stops or creates invalid file

**Solutions**:
1. Verify project data
2. Check disk space
3. Confirm file permissions
4. Try different location
5. Review error logs

#### Problem: DWW Import Fails
**Symptoms**: "Invalid DWW file" error

**Solutions**:
1. Verify file integrity
2. Check file not corrupted
3. Verify DWW format
4. Try re-exporting
5. Check file permissions

---

### Database Issues

#### Problem: Database Corruption
**Symptoms**: "Database error" messages

**Solutions**:
1. Restore from backup
2. Delete corrupted database
3. Reinstall application
4. Check disk health
5. Contact support

**Backup Location**:
```
AppData\Local\DigitalWorkshop\backups\
```

#### Problem: Data Loss
**Symptoms**: Projects or files missing

**Solutions**:
1. Check backup folder
2. Restore from backup
3. Check recycle bin
4. Use file recovery tool
5. Contact support

---

### GUI Issues

#### Problem: UI Elements Not Displaying
**Symptoms**: Buttons, menus, or panels missing

**Solutions**:
1. Restart application
2. Reset window layout
3. Check display settings
4. Update graphics drivers
5. Try different theme

#### Problem: Dialogs Not Responding
**Symptoms**: Dialog frozen or unresponsive

**Solutions**:
1. Wait for operation to complete
2. Check system resources
3. Restart application
4. Check for background processes
5. Review error logs

---

### Export/Import Issues

#### Problem: Export Takes Too Long
**Symptoms**: Export operation hangs

**Solutions**:
1. Check project size
2. Verify disk space
3. Check system resources
4. Try smaller project
5. Restart application

#### Problem: Import Takes Too Long
**Symptoms**: Import operation hangs

**Solutions**:
1. Check file size
2. Verify file integrity
3. Check system resources
4. Try different file
5. Restart application

---

## ❓ Frequently Asked Questions

### Installation & Setup

**Q: What are the system requirements?**
A: Python 3.8-3.12 (64-bit), 2GB disk space, 4GB RAM minimum

**Q: How long does installation take?**
A: Full Install: ~15 min, Patch: ~5 min, Reinstall: ~10 min

**Q: Can I install on multiple computers?**
A: Yes, each installation is independent

**Q: How do I uninstall?**
A: Use Clean Install mode or Windows Add/Remove Programs

**Q: Can I update without losing data?**
A: Yes, use Patch mode to preserve data

---

### Features & Usage

**Q: What file formats are supported?**
A: STL, OBJ, STEP, 3MF, PLY for models; NC, GCODE for G-code

**Q: Can I import multiple files at once?**
A: Yes, use batch import feature

**Q: How do I export a project?**
A: Use "Export as DWW" to create portable project file

**Q: Can I share projects with others?**
A: Yes, export as DWW and share the file

**Q: How do I backup my projects?**
A: Automatic backups created; manual backup via File menu

---

### Performance & Optimization

**Q: Why is the application slow?**
A: Check system resources, close unused projects, clear cache

**Q: How large can projects be?**
A: Limited by available disk space and RAM

**Q: Can I work with multiple projects?**
A: Yes, open multiple projects simultaneously

**Q: How do I improve performance?**
A: Reduce model complexity, close unused projects, update drivers

---

### Data & Security

**Q: Is my data secure?**
A: Yes, file validation, checksums, and backups protect data

**Q: What file types are blocked?**
A: EXE, SYS, INI, INF, COM, BAT, PS1, DLL, MSI

**Q: How are backups created?**
A: Automatic before operations, manual via File menu

**Q: Can I recover deleted projects?**
A: Yes, restore from backup or recycle bin

**Q: How do I verify file integrity?**
A: DWW files include SHA256 hash verification

---

### Troubleshooting

**Q: Where are error logs?**
A: `AppData\Local\DigitalWorkshop\logs\`

**Q: How do I clear the cache?**
A: Delete `AppData\Local\DigitalWorkshop\cache\`

**Q: How do I reset settings?**
A: Delete `AppData\Local\DigitalWorkshop\config\`

**Q: How do I reinstall?**
A: Use Clean Install mode then Full Install

**Q: Where do I get support?**
A: Check documentation or contact support

---

### Advanced Questions

**Q: Can I customize the UI?**
A: Yes, via Preferences menu

**Q: Can I use custom file formats?**
A: No, only supported formats

**Q: Can I automate tasks?**
A: Limited automation available

**Q: Can I extend functionality?**
A: Yes, via plugin system (if available)

**Q: Can I use command-line interface?**
A: Limited CLI available

---

## 🔧 Advanced Troubleshooting

### Enable Debug Logging
1. Open config file: `AppData\Local\DigitalWorkshop\config\config.json`
2. Set `"debug": true`
3. Restart application
4. Check logs for detailed information

### Check System Requirements
```bash
python --version
pip list
wmic os get osarchitecture
```

### Verify Installation
```bash
python -m pytest tests/ -v
```

### Clear All Data
```bash
# Backup first!
rmdir /s AppData\Local\DigitalWorkshop
```

---

## 📞 Getting Help

### Documentation
- **Installation**: MODULAR_INSTALLER_START_HERE.md
- **Features**: FEATURES_GUIDE.md
- **Development**: DEVELOPER_GUIDE.md
- **Architecture**: SYSTEM_ARCHITECTURE.md

### Support Resources
- Check error logs
- Review documentation
- Search FAQ
- Contact support team

### Reporting Issues
Include:
- Error message
- Steps to reproduce
- System information
- Log files
- Screenshots

---

## 🐛 Known Issues

### Issue 1: Slow Thumbnail Generation
**Status**: Known  
**Workaround**: Disable thumbnails in preferences  
**Fix**: Planned for next release

### Issue 2: Large File Import Timeout
**Status**: Known  
**Workaround**: Split large files  
**Fix**: Planned for next release

### Issue 3: Memory Leak on Long Sessions
**Status**: Known  
**Workaround**: Restart periodically  
**Fix**: Planned for next release

---

## ✅ Troubleshooting Checklist

Before contacting support:
- [ ] Checked system requirements
- [ ] Reviewed error logs
- [ ] Tried restarting application
- [ ] Cleared cache
- [ ] Verified file integrity
- [ ] Checked disk space
- [ ] Updated drivers
- [ ] Tried clean install

---

**Last Updated**: November 4, 2025  
**Status**: ✅ Current

