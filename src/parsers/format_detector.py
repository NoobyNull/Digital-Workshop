"""
Format detection utility for 3D-MM application.

This module provides automatic detection of 3D model file formats based on
file extension and content analysis.
"""

import zipfile
from pathlib import Path
from typing import Optional, Tuple
import struct

from .base_parser import ModelFormat
from core.logging_config import get_logger


class FormatDetector:
    """
    Utility class for detecting 3D model file formats.
    
    Features:
    - Detection based on file extension
    - Content-based detection for ambiguous files
    - Support for STL, OBJ, 3MF, and STEP formats
    - Comprehensive error handling
    """
    
    def __init__(self):
        """Initialize the format detector."""
        self.logger = get_logger(__name__)
        
        # Mapping of file extensions to formats
        self.extension_map = {
            '.stl': ModelFormat.STL,
            '.obj': ModelFormat.OBJ,
            '.3mf': ModelFormat.THREE_MF,
            '.step': ModelFormat.STEP,
            '.stp': ModelFormat.STEP,
        }
    
    def detect_format(self, file_path: Path) -> ModelFormat:
        """
        Detect the format of a 3D model file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Detected model format
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If format cannot be determined
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # First try detection by extension
        format_by_extension = self._detect_by_extension(file_path)
        
        if format_by_extension != ModelFormat.UNKNOWN:
            # Verify with content analysis for certain formats
            if format_by_extension == ModelFormat.STL:
                verified_format = self._verify_stl_format(file_path)
                if verified_format != ModelFormat.UNKNOWN:
                    return verified_format
            elif format_by_extension == ModelFormat.OBJ:
                if self._verify_obj_format(file_path):
                    return ModelFormat.OBJ
            elif format_by_extension == ModelFormat.THREE_MF:
                if self._verify_3mf_format(file_path):
                    return ModelFormat.THREE_MF
            elif format_by_extension == ModelFormat.STEP:
                if self._verify_step_format(file_path):
                    return ModelFormat.STEP
            
            return format_by_extension
        
        # If extension detection fails, try content-based detection
        return self._detect_by_content(file_path)
    
    def _detect_by_extension(self, file_path: Path) -> ModelFormat:
        """
        Detect format based on file extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Detected model format
        """
        extension = file_path.suffix.lower()
        return self.extension_map.get(extension, ModelFormat.UNKNOWN)
    
    def _verify_stl_format(self, file_path: Path) -> ModelFormat:
        """
        Verify STL format and detect if it's binary or ASCII.
        
        Args:
            file_path: Path to the file
            
        Returns:
            STL format type or UNKNOWN if invalid
        """
        try:
            with open(file_path, 'rb') as file:
                # Read first 80 bytes (header)
                header = file.read(80)
                
                # Check if header contains ASCII indicators
                header_text = header.decode('utf-8', errors='ignore').lower()
                if 'solid' in header_text and header_text.count('\x00') < 5:
                    # Likely ASCII, but verify by checking for "facet normal" keyword
                    file.seek(0)
                    first_line = file.readline().decode('utf-8', errors='ignore').strip()
                    if first_line.lower().startswith('solid'):
                        return ModelFormat.STL
                
                # Check if it's valid binary by attempting to read triangle count
                file.seek(80)
                count_bytes = file.read(4)
                if len(count_bytes) == 4:
                    triangle_count = struct.unpack('<I', count_bytes)[0]
                    
                    # Verify file size matches expected binary format size
                    file.seek(0, 2)  # Seek to end
                    file_size = file.tell()
                    expected_size = 80 + 4 + (triangle_count * 50)
                    
                    if file_size == expected_size:
                        return ModelFormat.STL
                
                return ModelFormat.UNKNOWN
                
        except Exception as e:
            self.logger.warning(f"Error verifying STL format: {str(e)}")
            return ModelFormat.UNKNOWN
    
    def _verify_obj_format(self, file_path: Path) -> bool:
        """
        Verify OBJ format by checking content.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if valid OBJ format, False otherwise
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                # Check for at least one vertex or face
                content = file.read(1000).lower()
                return 'v ' in content or 'f ' in content
                
        except Exception as e:
            self.logger.warning(f"Error verifying OBJ format: {str(e)}")
            return False
    
    def _verify_3mf_format(self, file_path: Path) -> bool:
        """
        Verify 3MF format by checking content.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if valid 3MF format, False otherwise
        """
        try:
            # Check if it's a valid ZIP file
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                # Check for required 3MF files
                if '3D/3dmodel.model' not in zip_file.namelist():
                    return False
                
                # Check if we can read the model file
                with zip_file.open('3D/3dmodel.model') as model_file:
                    content = model_file.read(1000).decode('utf-8')
                    return '<?xml' in content.lower() and 'model' in content.lower()
                    
        except Exception as e:
            self.logger.warning(f"Error verifying 3MF format: {str(e)}")
            return False
    
    def _verify_step_format(self, file_path: Path) -> bool:
        """
        Verify STEP format by checking content.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if valid STEP format, False otherwise
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                # Check for STEP header
                content = file.read(2000).upper()
                return 'ISO-10303-21' in content and 'DATA;' in content
                
        except Exception as e:
            self.logger.warning(f"Error verifying STEP format: {str(e)}")
            return False
    
    def _detect_by_content(self, file_path: Path) -> ModelFormat:
        """
        Detect format by analyzing file content.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Detected model format
        """
        try:
            # Try STL first
            stl_format = self._verify_stl_format(file_path)
            if stl_format != ModelFormat.UNKNOWN:
                return stl_format
            
            # Try OBJ
            if self._verify_obj_format(file_path):
                return ModelFormat.OBJ
            
            # Try 3MF
            if self._verify_3mf_format(file_path):
                return ModelFormat.THREE_MF
            
            # Try STEP
            if self._verify_step_format(file_path):
                return ModelFormat.STEP
            
            return ModelFormat.UNKNOWN
            
        except Exception as e:
            self.logger.error(f"Error detecting format by content: {str(e)}")
            return ModelFormat.UNKNOWN
    
    def is_supported_format(self, file_path: Path) -> bool:
        """
        Check if a file format is supported.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if format is supported, False otherwise
        """
        try:
            format_type = self.detect_format(file_path)
            return format_type != ModelFormat.UNKNOWN
        except:
            return False
    
    def get_supported_extensions(self) -> list:
        """
        Get list of supported file extensions.
        
        Returns:
            List of supported file extensions
        """
        return list(self.extension_map.keys())
    
    def validate_file(self, file_path: Path) -> Tuple[bool, str]:
        """
        Validate a 3D model file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if not file_path.exists():
                return False, "File does not exist"
            
            if file_path.stat().st_size == 0:
                return False, "File is empty"
            
            format_type = self.detect_format(file_path)
            
            if format_type == ModelFormat.UNKNOWN:
                return False, "Unsupported or unknown file format"
            
            return True, ""
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"