"""
Enhanced Format Detection System for Candy-Cadence

This module provides intelligent format detection for 3D model files with confidence scoring,
magic number detection, and content analysis for improved accuracy.

Key Features:
- Magic number detection for binary formats
- Content analysis for text-based formats
- Confidence scoring for detection results
- Support for multiple detection strategies
- Performance optimization for large files
"""

import os
import re
import time
import hashlib
import struct
import struct
from pathlib import Path
import os
import re
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import threading
from dataclasses import dataclass

from src.core.interfaces.parser_interfaces import IFormatDetector, ModelFormat
from src.core.logging_config import get_logger


@dataclass
class DetectionResult:
    """Result of format detection with confidence score."""
    format: Optional[ModelFormat]
    confidence: float
    method: str
    details: Dict[str, Any]
    processing_time: float


class MagicNumberDetector:
    """Detector for binary formats using magic numbers."""
    
    # Magic numbers for various 3D formats
    MAGIC_NUMBERS = {
        ModelFormat.STL: [
            b'solid ',  # ASCII STL
            b'\x00\x00\x00\x00'  # Binary STL (80-byte header + triangle count)
        ],
        ModelFormat.THREE_MF: [
            b'PK\x03\x04',  # ZIP signature (3MF is a ZIP file)
        ],
        ModelFormat.PLY: [
            b'ply\n',  # PLY format starts with "ply"
        ]
    }
    
    @classmethod
    def detect_format(cls, file_path: Path, max_bytes: int = 1024) -> Optional[DetectionResult]:
        """
        Detect format using magic numbers.
        
        Args:
            file_path: Path to the file
            max_bytes: Maximum bytes to read for detection
            
        Returns:
            DetectionResult with format and confidence
        """
        try:
            with open(file_path, 'rb') as f:
                header = f.read(max_bytes)
            
            # Check each format's magic numbers
            for format_type, magic_numbers in cls.MAGIC_NUMBERS.items():
                for magic in magic_numbers:
                    if header.startswith(magic):
                        confidence = 0.95 if len(magic) > 4 else 0.85
                        return DetectionResult(
                            format=format_type,
                            confidence=confidence,
                            method="magic_number",
                            details={"magic": magic.hex(), "position": 0}
                        )
            
            # Special case for binary STL (check for 80-byte header + triangle count)
            if len(header) >= 84:
                # Check if it looks like binary STL
                try:
                    # Try to read as binary STL
                    triangle_count = int.from_bytes(header[80:84], byteorder='little')
                    if 0 < triangle_count < 100000000:  # Reasonable triangle count
                        return DetectionResult(
                            format=ModelFormat.STL,
                            confidence=0.90,
                            method="binary_stl_structure",
                            details={"triangle_count": triangle_count}
                        )
                except (ValueError, struct.error):
                    pass
            
            return None
            
        except Exception as e:
            return None


class ContentAnalyzer:
    """Analyzer for text-based formats using content patterns."""
    
    # Patterns for text-based format detection
    PATTERNS = {
        ModelFormat.OBJ: [
            r'^\s*v\s+[\d\.\-eE]+',  # Vertex definition
            r'^\s*f\s+[\d\/\s\-]+',  # Face definition
            r'^\s*vn\s+',  # Vertex normal
            r'^\s*vt\s+',  # Texture coordinate
        ],
        ModelFormat.STL: [
            r'^\s*solid\s+',  # ASCII STL solid keyword
            r'^\s*facet\s+',  # ASCII STL facet
            r'^\s*vertex\s+',  # ASCII STL vertex
        ],
        ModelFormat.STEP: [
            r'ISO-10303-21',  # STEP header
            r'^\s*DATA;',  # STEP data section
            r'^\s*#\d+\s*=',  # STEP entity
        ],
        ModelFormat.PLY: [
            r'^\s*ply\s*',  # PLY header
            r'^\s*format\s+',  # PLY format declaration
            r'^\s*element\s+',  # PLY element declaration
        ]
    }
    
    @classmethod
    def detect_format(cls, file_path: Path, max_lines: int = 1000) -> Optional[DetectionResult]:
        """
        Detect format using content analysis.
        
        Args:
            file_path: Path to the file
            max_lines: Maximum lines to analyze
            
        Returns:
            DetectionResult with format and confidence
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = []
                for i, line in enumerate(f):
                    if i >= max_lines:
                        break
                    lines.append(line)
            
            # Analyze content for each format
            format_scores = {}
            
            for format_type, patterns in cls.PATTERNS.items():
                score = 0
                matches = 0
                
                for pattern in patterns:
                    pattern_re = re.compile(pattern, re.MULTILINE)
                    found_matches = pattern_re.findall('\n'.join(lines))
                    matches += len(found_matches)
                    if found_matches:
                        score += len(found_matches)
                
                if matches > 0:
                    # Calculate confidence based on matches and total lines
                    confidence = min(0.95, 0.3 + (score / max(len(lines), 1)) * 0.65)
                    format_scores[format_type] = (confidence, matches)
            
            if format_scores:
                # Get the format with highest confidence
                best_format = max(format_scores.items(), key=lambda x: x[1][0])
                return DetectionResult(
                    format=best_format[0],
                    confidence=best_format[1][0],
                    method="content_analysis",
                    details={"matches": best_format[1][1], "total_lines": len(lines)}
                )
            
            return None
            
        except Exception as e:
            return None


class FileExtensionDetector:
    """Detector based on file extensions."""
    
    EXTENSION_MAP = {
        '.stl': ModelFormat.STL,
        '.obj': ModelFormat.OBJ,
        '.3mf': ModelFormat.THREE_MF,
        '.step': ModelFormat.STEP,
        '.stp': ModelFormat.STEP,
        '.ply': ModelFormat.PLY,
        '.x3d': ModelFormat.X3D,
    }
    
    @classmethod
    def detect_format(cls, file_path: Path) -> Optional[DetectionResult]:
        """
        Detect format based on file extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            DetectionResult with format and confidence
        """
        start_time = time.time()
        extension = file_path.suffix.lower()
        format_type = cls.EXTENSION_MAP.get(extension)
        
        if format_type:
            processing_time = time.time() - start_time
            return DetectionResult(
                format=format_type,
                confidence=0.70,  # Lower confidence for extension-only detection
                method="file_extension",
                details={"extension": extension},
                processing_time=processing_time
            )
        
        return None


class EnhancedFormatDetector(IFormatDetector):
    """
    Enhanced format detector combining multiple detection strategies.
    
    Features:
    - Multiple detection strategies (magic numbers, content analysis, extensions)
    - Confidence scoring and result ranking
    - Performance optimization for large files
    - Thread-safe operation
    - Caching of detection results
    """
    
    def __init__(self):
        """Initialize the enhanced format detector."""
        self.logger = get_logger(self.__class__.__name__)
        self._cache = {}
        self._cache_lock = threading.RLock()
        self._cache_max_size = 1000
        
        # Detection strategies in order of preference
        self._strategies = [
            MagicNumberDetector(),
            ContentAnalyzer(),
            FileExtensionDetector()
        ]
    
    def detect_format(self, file_path: Path) -> Optional[ModelFormat]:
        """
        Detect the format of a 3D model file.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            ModelFormat enum if format is detected, None otherwise
        """
        result = self.detect_format_with_confidence(file_path)
        return result.format if result else None
    
    def detect_format_with_confidence(self, file_path: Path) -> Optional[DetectionResult]:
        """
        Detect format with confidence score.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            DetectionResult with format and confidence, None if detection fails
        """
        # Check cache first
        cache_key = self._get_cache_key(file_path)
        with self._cache_lock:
            cached_result = self._cache.get(cache_key)
            if cached_result:
                self.logger.debug(f"Format detection cache hit for {file_path}")
                return cached_result
        
        # Perform detection
        start_time = time.time()
        results = []
        
        try:
            # Run all detection strategies
            for strategy in self._strategies:
                try:
                    result = strategy.detect_format(file_path)
                    if result:
                        results.append(result)
                except Exception as e:
                    self.logger.warning(f"Detection strategy {strategy.__class__.__name__} failed: {str(e)}")
                    continue
            
            # Select best result
            best_result = self._select_best_result(results)
            
            # Cache the result
            if best_result:
                with self._cache_lock:
                    self._cache[cache_key] = best_result
                    self._cleanup_cache_if_needed()
            
            processing_time = time.time() - start_time
            if best_result:
                self.logger.info(
                    f"Format detection completed for {file_path}: "
                    f"{best_result.format.value} (confidence: {best_result.confidence:.2f}, "
                    f"method: {best_result.method}, time: {processing_time:.3f}s)"
                )
            else:
                self.logger.warning(f"Format detection failed for {file_path} (time: {processing_time:.3f}s)")
            
            return best_result
            
        except Exception as e:
            self.logger.error(f"Format detection error for {file_path}: {str(e)}")
            return None
    
    def get_format_confidence(self, file_path: Path) -> float:
        """
        Get confidence level for format detection.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            Confidence level between 0.0 and 1.0
        """
        result = self.detect_format_with_confidence(file_path)
        return result.confidence if result else 0.0
    
    def get_all_possible_formats(self) -> List[ModelFormat]:
        """
        Get list of all formats that can be detected.
        
        Returns:
            List of all detectable ModelFormat enums
        """
        return list(ModelFormat)
    
    def get_detection_details(self, file_path: Path) -> Dict[str, Any]:
        """
        Get detailed information about format detection.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            Dictionary containing detection details
        """
        result = self.detect_format_with_confidence(file_path)
        if result:
            return {
                "format": result.format.value if result.format else None,
                "confidence": result.confidence,
                "method": result.method,
                "details": result.details,
                "processing_time": getattr(result, 'processing_time', 0.0)
            }
        return {}
    
    def _get_cache_key(self, file_path: Path) -> str:
        """
        Generate cache key for file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Cache key string
        """
        try:
            stat = file_path.stat()
            return f"{file_path}_{stat.st_size}_{stat.st_mtime}"
        except Exception:
            return str(file_path)
    
    def _select_best_result(self, results: List[DetectionResult]) -> Optional[DetectionResult]:
        """
        Select the best detection result from multiple strategies.
        
        Args:
            results: List of detection results
            
        Returns:
            Best detection result or None
        """
        if not results:
            return None
        
        # Sort by confidence (highest first)
        results.sort(key=lambda x: x.confidence, reverse=True)
        
        # Return the result with highest confidence
        # If multiple results have similar confidence, prefer magic number detection
        best_result = results[0]
        
        # If we have multiple high-confidence results, prefer magic number detection
        if len(results) > 1 and results[1].confidence > 0.8:
            magic_results = [r for r in results if r.method == "magic_number"]
            if magic_results:
                best_result = magic_results[0]
        
        return best_result
    
    def _cleanup_cache_if_needed(self) -> None:
        """Clean up cache if it exceeds maximum size."""
        if len(self._cache) > self._cache_max_size:
            # Remove oldest entries (simple FIFO)
            keys_to_remove = list(self._cache.keys())[:len(self._cache) - self._cache_max_size]
            for key in keys_to_remove:
                del self._cache[key]
    
    def clear_cache(self) -> None:
        """Clear the detection cache."""
        with self._cache_lock:
            self._cache.clear()
            self.logger.info("Format detection cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary containing cache statistics
        """
        with self._cache_lock:
            return {
                "cache_size": len(self._cache),
                "max_cache_size": self._cache_max_size,
                "cache_entries": list(self._cache.keys())
            }


# Global instance
_format_detector = None
_detector_lock = threading.Lock()


def get_format_detector() -> EnhancedFormatDetector:
    """
    Get the global format detector instance.
    
    Returns:
        EnhancedFormatDetector instance
    """
    global _format_detector
    if _format_detector is None:
        with _detector_lock:
            if _format_detector is None:
                _format_detector = EnhancedFormatDetector()
    return _format_detector


# Alias for backward compatibility
FormatDetector = EnhancedFormatDetector
