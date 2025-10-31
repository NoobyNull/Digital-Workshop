
# Candy-Cadence Deployment Guide

## Overview

This comprehensive deployment guide covers all aspects of deploying Candy-Cadence in various environments, from development to production. It includes detailed procedures for Windows deployment, system configuration, and distribution.

## Table of Contents

1. [Deployment Overview](#deployment-overview)
2. [System Requirements Verification](#system-requirements-verification)
3. [Development Deployment](#development-deployment)
4. [Production Deployment](#production-deployment)
5. [Windows Installer Creation](#windows-installer-creation)
6. [Configuration Management](#configuration-management)
7. [Performance Optimization](#performance-optimization)
8. [Security Considerations](#security-considerations)
9. [Distribution and Packaging](#distribution-and-packaging)
10. [Automated Deployment](#automated-deployment)
11. [Rollback Procedures](#rollback-procedures)

## Deployment Overview

### Deployment Architecture

Candy-Cadence uses a multi-tier deployment architecture:

- **Client Application**: Qt-based desktop GUI application
- **Local Database**: SQLite database for data persistence
- **File System**: Local file storage for 3D models and cache
- **Configuration**: JSON-based configuration files

### Deployment Types

| Type | Purpose | Target Users | Distribution |
|------|---------|--------------|--------------|
| Development | Testing and development | Developers | Source code + dependencies |
| Alpha | Early testing | Internal testers | Portable executable |
| Beta | Pre-release testing | Limited external users | Installer package |
| Production | End users | General public | Full installer with auto-update |

### Deployment Environment Matrix

| Environment | Database | Logging | Cache | Update Channel |
|-------------|----------|---------|--------|----------------|
| Development | SQLite (local) | DEBUG | Memory + Disk | Manual |
| Testing | SQLite (local) | INFO | Memory + Disk | Manual |
| Staging | SQLite (shared) | INFO | Memory + Disk | Beta channel |
| Production | SQLite (local) | WARNING | Memory + Disk | Release channel |

## System Requirements Verification

### Hardware Requirements Check

```python
import platform
import psutil
import subprocess
import sys
from pathlib import Path

class SystemVerifier:
    """Verify system meets deployment requirements."""
    
    def __init__(self):
        self.minimum_requirements = {
            'os': 'Windows 7 SP1',
            'architecture': 'x86_64',
            'cpu_cores': 2,
            'memory_gb': 4,
            'disk_gb': 1,
            'opengl_version': '3.3'
        }
        
        self.recommended_requirements = {
            'os': 'Windows 10',
            'architecture': 'x86_64',
            'cpu_cores': 4,
            'memory_gb': 8,
            'disk_gb': 5,
            'opengl_version': '4.5'
        }
    
    def verify_system(self):
        """Perform comprehensive system verification."""
        verification_result = {
            'timestamp': datetime.now().isoformat(),
            'meets_minimum': True,
            'meets_recommended': False,
            'issues': [],
            'warnings': [],
            'recommendations': [],
            'system_info': {}
        }
        
        # Verify OS
        os_info = self._verify_os()
        verification_result['system_info']['os'] = os_info
        
        # Verify CPU
        cpu_info = self._verify_cpu()
        verification_result['system_info']['cpu'] = cpu_info
        
        # Verify Memory
        memory_info = self._verify_memory()
        verification_result['system_info']['memory'] = memory_info
        
        # Verify Disk Space
        disk_info = self._verify_disk_space()
        verification_result['system_info']['disk'] = disk_info
        
        # Verify Graphics
        graphics_info = self._verify_graphics()
        verification_result['system_info']['graphics'] = graphics_info
        
        # Verify Python
        python_info = self._verify_python()
        verification_result['system_info']['python'] = python_info
        
        # Generate recommendations
        self._generate_recommendations(verification_result)
        
        return verification_result
    
    def _verify_os(self):
        """Verify operating system compatibility."""
        system_info = {
            'platform': platform.system(),
            'version': platform.version(),
            'architecture': platform.architecture()[0],
            'processor': platform.processor()
        }
        
        if system_info['platform'] != 'Windows':
            return {'compatible': False, 'error': 'Only Windows is supported'}
        
        # Check Windows version
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                               r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
            product_name = winreg.QueryValueEx(key, "ProductName")[0]
            winreg.CloseKey(key)
            
            system_info['product_name'] = product_name
            
            # Check if Windows 7 SP1 or newer
            if 'Windows 7' in product_name:
                if 'SP1' not in product_name:
                    return {'compatible': False, 'error': 'Windows 7 SP1 required'}
            elif 'Windows 8' not in product_info and 'Windows 10' not in product_info and 'Windows 11' not in product_info:
                return {'compatible': False, 'error': 'Windows 7 SP1 or newer required'}
            
            return {'compatible': True, 'info': system_info}
            
        except Exception as e:
            return {'compatible': False, 'error': f'Version check failed: {e}'}
    
    def _verify_cpu(self):
        """Verify CPU compatibility."""
        cpu_count = psutil.cpu_count(logical=False)
        cpu_count_logical = psutil.cpu_count(logical=True)
        
        return {
            'physical_cores': cpu_count,
            'logical_cores': cpu_count_logical,
            'compatible': cpu_count >= 2,
            'info': f"{cpu_count} physical cores, {cpu_count_logical} logical cores"
        }
    
    def _verify_memory(self):
        """Verify system memory."""
        memory = psutil.virtual_memory()
        memory_gb = memory.total / (1024**3)
        
        return {
            'total_gb': round(memory_gb, 1),
            'available_gb': round(memory.available / (1024**3), 1),
            'compatible': memory_gb >= 4,
            'recommended': memory_gb >= 8,
            'info': f"{round(memory_gb, 1)} GB total, {round(memory.available / (1024**3), 1)} GB available"
        }
    
    def _verify_disk_space(self):
        """Verify available disk space."""
        disk = psutil.disk_usage('.')
        free_gb = disk.free / (1024**3)
        total_gb = disk.total / (1024**3)
        
        return {
            'total_gb': round(total_gb, 1),
            'free_gb': round(free_gb, 1),
            'compatible': free_gb >= 1,
            'recommended': free_gb >= 5,
            'info': f"{round(free_gb, 1)} GB free of {round(total_gb, 1)} GB total"
        }
    
    def _verify_graphics(self):
        """Verify graphics capabilities."""
        try:
            # Check OpenGL support
            from OpenGL.GL import glGetString, GL_VERSION, GL_RENDERER
            
            import OpenGL.GL as gl
            version = glGetString(GL_VERSION)
            renderer = glGetString(GL_RENDERER)
            
            opengl_version = version.decode() if version else 'Unknown'
            gpu_renderer = renderer.decode() if renderer else 'Unknown'
            
            # Parse version to check if >= 3.3
            version_parts = opengl_version.split('.')
            major_version = int(version_parts[0]) if version_parts else 0
            minor_version = int(version_parts[1]) if len(version_parts) > 1 else 0
            
            compatible = major_version > 3 or (major_version == 3 and minor_version >= 3)
            
            return {
                'opengl_version': opengl_version,
                'gpu_renderer': gpu_renderer,
                'compatible': compatible,
                'info': f"OpenGL {opengl_version} - {gpu_renderer}"
            }
            
        except Exception as e:
            return {
                'compatible': False,
                'error': f'OpenGL verification failed: {e}',
                'info': 'Graphics drivers may need updating'
            }
    
    def _verify_python(self):
        """Verify Python environment."""
        version_info = sys.version_info
        
        return {
            'version': f"{version_info.major}.{version_info.minor}.{version_info.micro}",
            'compatible': version_info >= (3, 8) and version_info < (3, 13),
            'architecture': platform.architecture()[0],
            'info': f"Python {version_info.major}.{version_info.minor}.{version_info.micro}"
        }
    
    def _generate_recommendations(self, result):
        """Generate system recommendations."""
        if not result['system_info']['graphics']['compatible']:
            result['recommendations'].append("Update graphics drivers for better performance")
        
        if result['system_info']['memory']['total_gb'] < 8:
            result['recommendations'].append("Consider upgrading to 8GB+ RAM for optimal performance")
        
        if result['system_info']['cpu']['physical_cores'] < 4:
            result['recommendations'].append("Multi-core CPU recommended for large model processing")
        
        if result['system_info']['disk']['free_gb'] < 5:
            result['recommendations'].append("Consider freeing disk space or using SSD for better performance")

# Run system verification
if __name__ == "__main__":
    verifier = SystemVerifier()
    result = verifier.verify_system()
    
    print("Candy-Cadence System Verification")
    print("=" * 40)
    
    if result['meets_minimum']:
        print("✅ System meets minimum requirements")
    else:
        print("❌ System does not meet minimum requirements")
    
    if result['meets_recommended']:
        print("✅ System meets recommended requirements")
    else:
        print("⚠️ System does not meet recommended requirements")
    
    for issue in result['issues']:
        print(f"❌ {issue}")
    
    for warning in result['warnings']:
        print(f"⚠️ {warning}")
    
    for recommendation in result['recommendations']:
        print(f"💡 {recommendation}")
```

### Graphics Driver Detection

```python
def detect_graphics_drivers():
    """Detect and verify graphics drivers."""
    import subprocess
    import json
    
    def get_gpu_info():
        """Get GPU information using WMI."""
        try:
            result = subprocess.run([
                'wmic', 'path', 'win32_VideoController', 'get', 
                'Name,DriverVersion,DriverDate', '/format:csv'
            ], capture_output=True, text=True)
            
            gpus = []
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            
            for line in lines:
                if line.strip():
                    parts = line.split(',')
                    if len(parts) >= 3:
                        gpus.append({
                            'name': parts[1].strip(),
                            'version': parts[2].strip(),
                            'date': parts[3].strip()
                        })
            
            return gpus
        except Exception as e:
            return []
    
    def check_directx_support():
        """Check DirectX support level."""
        try:
            result = subprocess.run([
                'dxdiag', '/t', 'dxdiag_output.txt'
            ], capture_output=True, text=True)
            
            # Read the output file
            with open('dxdiag_output.txt', 'r') as f:
                content = f.read()
            
            # Clean up
            Path('dxdiag_output.txt').unlink(missing_ok=True)
            
            # Extract DirectX version
            import re
            match = re.search(r'DirectX Version:\s+(\S+)', content)
            if match:
                return match.group(1)
            
            return 'Unknown'
        except Exception as e:
            return 'Unknown'
    
    gpu_info = get_gpu_info()
    directx_version = check_directx_support()
    
    print("Graphics System Information:")
    print("=" * 30)
    
    for i, gpu in enumerate(gpu_info, 1):
        print(f"GPU {i}: {gpu['name']}")
        print(f"  Driver: {gpu['version']}")
        print(f"  Date: {gpu['date']}")
    
    print(f"DirectX Version: {directx_version}")
    
    # Recommendations
    print("\nGraphics Recommendations:")
    print("-