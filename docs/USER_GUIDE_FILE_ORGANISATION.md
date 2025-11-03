# User Guide: File Organisation and Project Manager

## Getting Started

### First Run Setup

When you launch Digital Workshop for the first time, you'll see the **First Run Setup** dialog:

1. **Welcome Message**: Explains the purpose of Digital Workshop
2. **Storage Location**: Choose where to store your projects and files
   - Default: User's data directory
   - Custom: Click "Browse..." to select a different location
3. **Finish Setup**: Click to complete setup

**Note**: You can change the storage location later in Preferences.

---

## Project Manager

The **Project Manager** dock widget is located on the left side of the main window.

### Creating a New Project

1. Click **"New Project"** button
2. Enter a project name
3. Click **OK**

Your new project appears in the project list.

### Importing a Library

The import feature lets you organize existing model files into a project:

1. Click **"Import Library"** button
2. Select the folder containing your models
3. Enter a project name
4. Review the **Import Preview**:
   - Number of files to import
   - Number of blocked files (if any)
   - Total storage size
5. Click **"Yes"** to proceed or **"No"** to cancel

**What happens during import**:
- Digital Workshop analyzes your folder structure
- Detects and organizes files by type
- Blocks potentially harmful files (executables, scripts, etc.)
- Creates a project with all your files
- Tags the project as "Imported" for easy identification

### Opening a Project

1. Select a project from the list
2. Double-click or click **"Open"** button
3. The project opens and is ready to use

### Deleting a Project

1. Select a project from the list
2. Click **"Delete"** button
3. Confirm the deletion

**Note**: Deleting a project removes it from Digital Workshop but does NOT delete the original files.

---

## Supported File Types

### 3D Models
- STL (.stl)
- OBJ (.obj)
- 3MF (.3mf)
- STEP (.step, .stp)
- IGES (.iges, .igs)

### Documents
- PDF (.pdf)
- Text (.txt, .md)
- Word (.doc, .docx)
- Excel (.xls, .xlsx)

### Images
- PNG (.png)
- JPEG (.jpg, .jpeg)
- BMP (.bmp)
- GIF (.gif)

### Data Files
- JSON (.json)
- CSV (.csv)
- XML (.xml)
- YAML (.yaml, .yml)

---

## Blocked File Types

For security reasons, the following file types are blocked:

- **Executables**: .exe, .com, .bat, .cmd
- **Scripts**: .ps1, .sh, .py, .js
- **System Files**: .sys, .dll, .ini, .inf
- **Other**: .zip, .rar, .7z (archives)

If you try to import a folder with blocked files, they will be skipped and listed in the import preview.

---

## Import Preview

Before importing, you'll see a preview showing:

- **Files to Import**: Number of files that will be imported
- **Blocked Files**: Number of files that will be skipped
- **Total Size**: Total storage space needed
- **Recommendations**: Suggestions for the import

Review this information carefully before proceeding.

---

## Project Organization

### Imported Projects

Projects created through the import feature are marked with **[Imported]** in the project list.

These projects:
- Preserve your original folder structure
- Link to files in their original location
- Can be easily identified and managed

### Regular Projects

Projects created manually:
- Start empty
- Can have files added individually
- Useful for organizing new work

---

## Tips and Best Practices

### Organizing Your Files

1. **Use Descriptive Names**: Name your projects clearly
2. **Group by Type**: Keep similar models together
3. **Use Subfolders**: Organize files within projects
4. **Add Metadata**: Use the Properties panel to add descriptions

### Importing Libraries

1. **Backup First**: Keep a backup of your original files
2. **Review Preview**: Always check the import preview
3. **Start Small**: Test with a small folder first
4. **Check Results**: Verify all files imported correctly

### Managing Projects

1. **Regular Cleanup**: Delete unused projects
2. **Archive Old Projects**: Move old projects to archive
3. **Document Changes**: Add notes to project metadata
4. **Backup Projects**: Regularly backup your project data

---

## Troubleshooting

### Import Failed

**Problem**: Import shows "No files to import"

**Solution**:
- Check that the folder contains supported file types
- Verify the folder path is correct
- Ensure you have read permissions

### Files Not Appearing

**Problem**: Files don't appear after import

**Solution**:
- Refresh the project list (click "Refresh")
- Check the import preview for blocked files
- Verify files are in a supported format

### Storage Location Issues

**Problem**: Can't change storage location

**Solution**:
- Ensure you have write permissions to the new location
- Check that the path is valid
- Try a different location

### Duplicate Project Error

**Problem**: Can't create project with existing name

**Solution**:
- Use a different project name
- Delete the existing project first
- Check for similar names (case-insensitive)

---

## Keyboard Shortcuts

- **Ctrl+N**: New Project
- **Ctrl+I**: Import Library
- **Ctrl+O**: Open Project
- **Delete**: Delete Project
- **F5**: Refresh Project List

---

## Getting Help

- Check the **Developer Guide** for technical details
- Review **Preferences** for configuration options
- Check **Status Bar** for operation feedback
- Use **Help Menu** for additional resources

---

## Next Steps

1. Create your first project
2. Import an existing library
3. Explore the project properties
4. Add metadata to your projects
5. Organize your model files

Enjoy using Digital Workshop!


