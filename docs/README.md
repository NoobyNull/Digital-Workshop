# 3D-MM (3D Model Manager) Documentation

## Overview

3D-MM is a Windows desktop application for organizing and viewing 3D model collections. It's designed for hobbyists who need to manage large collections of 3D models with ease.

## Table of Contents

- [Installation](#installation)
- [Running the Application](#running-the-application)
- [User Guide](#user-guide)
- [Developer Documentation](#developer-documentation)
- [API Reference](#api-reference)
- [Troubleshooting](#troubleshooting)

## Installation

### System Requirements

**Minimum:**
- OS: Windows 7 SP1 (64-bit)
- CPU: Intel Core i3-3220 (Ivy Bridge) or equivalent
- GPU: Intel HD Graphics 4000 or equivalent
- RAM: 4GB
- Storage: 100MB free space

**Recommended:**
- OS: Windows 10/11 (64-bit)
- CPU: Intel Core i5-3470 or equivalent
- GPU: NVIDIA GeForce GTX 1050 or equivalent
- RAM: 8GB
- Storage: 500MB free space (SSD recommended)

### Installation Steps

1. Download the latest installer from the releases page
2. Run the installer executable
3. Follow the installation wizard
4. Launch 3D-MM from the Start menu

## Running the Application

For detailed instructions on running the 3D-MM application in both development and production modes, see the [Running Guide](RUNNING_GUIDE.md).

### Quick Start

**Easiest Method (Recommended):**
```bash
# Run the quick start script (handles everything automatically)
python run.py
```

**From Source Code (Development):**
```bash
# Install dependencies
pip install -r requirements.txt

# Fix circular imports (if needed)
python fix_circular_imports.py

# Run the application
python src/main.py
```

**From Built Package (Production):**
1. Download and run the installer
2. Launch from Start menu

## User Guide

### Getting Started

- [First Time Setup](user-guide/setup.md)
- [Importing Models](user-guide/importing.md)
- [Viewing Models](user-guide/viewing.md)
- [Organizing Collections](user-guide/organizing.md)
- [Editing Metadata](user-guide/metadata.md)

### Advanced Features

- [Search and Filter](user-guide/search.md)
- [Batch Operations](user-guide/batch.md)
- [Custom Tags](user-guide/tags.md)

## Developer Documentation

### Architecture

- [Project Structure](developer/architecture.md)
- [Core Components](developer/components.md)
- [Database Schema](developer/database.md)
- [Plugin System](developer/plugins.md)

### Development Guide

- [Setting Up Development Environment](developer/setup.md)
- [Coding Standards](developer/standards.md)
- [Testing](developer/testing.md)
- [Building and Packaging](developer/building.md)

## API Reference

### Core Modules

- [Model Manager](api/model-manager.md)
- [Database Manager](api/database-manager.md)
- [Search Engine](api/search-engine.md)
- [3D Viewer](api/viewer.md)

### Parsers

- [STL Parser](api/parsers/stl.md)
- [OBJ Parser](api/parsers/obj.md)
- [3MF Parser](api/parsers/3mf.md)
- [STEP Parser](api/parsers/step.md)

## Troubleshooting

### Common Issues

- [Installation Problems](troubleshooting/installation.md)
- [Performance Issues](troubleshooting/performance.md)
- [Model Loading Errors](troubleshooting/loading.md)
- [Graphics Issues](troubleshooting/graphics.md)

### FAQ

- [Frequently Asked Questions](troubleshooting/faq.md)