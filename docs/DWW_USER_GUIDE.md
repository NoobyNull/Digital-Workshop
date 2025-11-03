# DWW Export/Import User Guide

## What is DWW?

DWW (Digital Wood Works) is Digital Workshop's native project format. It's a single file that contains your entire project - all models, G-code files, cut lists, cost sheets, and metadata - packaged together with integrity verification.

## Why Use DWW?

- **Portable**: Share entire projects as a single file
- **Safe**: Built-in integrity checking ensures files aren't corrupted
- **Complete**: Includes all project metadata and files
- **Compressed**: Smaller file size than individual files
- **Professional**: Industry-standard ZIP format

## Exporting a Project to DWW

### Step 1: Select Project
In the Project Manager panel on the left, click on the project you want to export.

### Step 2: Click Export Button
Click the **"Export as DWW"** button at the bottom of the Project Manager panel.

### Step 3: Choose Location
A file dialog will appear. Choose where you want to save the DWW file and give it a name (e.g., "MyProject.dww").

### Step 4: Wait for Export
The export process will:
1. Gather all project files
2. Create project metadata
3. Calculate integrity hashes
4. Package everything into a DWW file

You'll see a success message when complete.

## Importing a Project from DWW

### Quick Import

Click the **"Import DWW"** button in the Project Manager panel to import a DWW file.

The import process will:
1. Let you select a DWW file
2. Show project preview information
3. Verify file integrity automatically
4. Extract all files and thumbnails
5. Add the project to your library

### Detailed Instructions

For complete step-by-step instructions, see: **[DWW Import Guide](DWW_IMPORT_GUIDE.md)**

The import guide includes:
- Detailed workflow diagrams
- Error handling and troubleshooting
- Technical details about the import process
- API usage examples

## DWW File Contents

When you export a project to DWW, it contains:

```
MyProject.dww
├── manifest.json                    # Project info and file list
├── integrity.json                   # Security verification data
├── files/                           # All your project files
│   ├── model.stl
│   ├── gcode.nc
│   ├── cost_sheet.pdf
│   └── ...
├── thumbnails/                      # Model preview images
│   ├── model.stl.thumb.png
│   └── ...
└── metadata/                        # Detailed file information
    └── files_metadata.json          # File metadata and attributes
```

## Integrity Verification

DWW files include a cryptographic hash that verifies:
- No files were corrupted
- No files were added or removed
- The project hasn't been tampered with

This verification happens automatically when you import a DWW file.

## Sharing Projects

### Via Email
DWW files are perfect for email sharing:
1. Export your project to DWW
2. Attach the .dww file to an email
3. Recipient imports it into their Digital Workshop

### Via Cloud Storage
1. Export to DWW
2. Upload to Google Drive, Dropbox, OneDrive, etc.
3. Share the link with collaborators
4. They download and import into Digital Workshop

### Via USB Drive
1. Export to DWW
2. Copy the .dww file to USB drive
3. Give USB drive to colleague
4. They import the file

## Troubleshooting

### "Integrity verification failed"
The DWW file may be corrupted. Try:
- Re-downloading the file
- Checking your internet connection
- Asking the sender to re-export

### "File not found during export"
Some project files may have been moved or deleted. Try:
- Checking that all files still exist
- Re-importing the files into the project
- Exporting again

### "Import failed"
The DWW file may be invalid. Try:
- Verifying the file is actually a DWW file (.dww extension)
- Checking that the file wasn't corrupted during transfer
- Asking the sender to re-export

## Best Practices

1. **Regular Exports**: Export important projects regularly as backups
2. **Descriptive Names**: Use clear names like "ProjectName_v1.dww"
3. **Version Control**: Include version numbers in filenames
4. **Backup Location**: Keep exports in a safe location
5. **Verify After Import**: Check that all files imported correctly

## Technical Details

For detailed technical information about the DWW format, see:
- `docs/DWW_FORMAT_SPECIFICATION.md`

## Support

If you encounter issues with DWW export/import:
1. Check the application logs
2. Verify file permissions
3. Ensure sufficient disk space
4. Contact support with the error message

