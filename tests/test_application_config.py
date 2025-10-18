#!/usr/bin/env python3
"""
Unit tests for ApplicationConfig module.

This module tests the ApplicationConfig class functionality including
default configuration, version handling, and application metadata.
"""

import unittest

from src.core.application_config import ApplicationConfig


class TestApplicationConfig(unittest.TestCase):
    """Test cases for ApplicationConfig class."""
    
    def test_default_config(self):
        """Test that default configuration is created correctly."""
        config = ApplicationConfig.get_default()
        
        # Test basic properties
        self.assertEqual(config.name, "3D-MM")
        self.assertEqual(config.display_name, "3D Model Manager")
        self.assertEqual(config.version, "1.0.0")
        self.assertEqual(config.organization_name, "3D-MM Development Team")
        self.assertEqual(config.organization_domain, "3dmm.local")
        
        # Test feature flags
        self.assertTrue(config.enable_hardware_acceleration)
        self.assertTrue(config.enable_high_dpi)
        self.assertTrue(config.enable_performance_monitoring)
        
        # Test resource limits
        self.assertEqual(config.max_memory_usage_mb, 2048)
        self.assertIsNone(config.model_cache_size_mb)  # Should be adaptive
        
        # Test UI configuration
        self.assertEqual(config.default_window_width, 1200)
        self.assertEqual(config.default_window_height, 800)
        self.assertEqual(config.minimum_window_width, 800)
        self.assertEqual(config.minimum_window_height, 600)
    
    def test_custom_config(self):
        """Test that custom configuration can be created."""
        config = ApplicationConfig(
            name="Test-App",
            version="2.0.0",
            organization_name="Test Org"
        )
        
        self.assertEqual(config.name, "Test-App")
        self.assertEqual(config.version, "2.0.0")
        self.assertEqual(config.organization_name, "Test Org")
    
    def test_version_string_without_build(self):
        """Test version string formatting without build number."""
        config = ApplicationConfig(version="1.2.3")
        self.assertEqual(config.get_full_version_string(), "1.2.3")
    
    def test_version_string_with_build(self):
        """Test version string formatting with build number."""
        config = ApplicationConfig(version="1.2.3", build_number="456")
        self.assertEqual(config.get_full_version_string(), "1.2.3 (Build 456)")
    
    def test_app_identifier(self):
        """Test application identifier generation."""
        config = ApplicationConfig(
            name="Test-App",
            organization_domain="test.example.com"
        )
        self.assertEqual(config.get_app_identifier(), "test.example.com.test-app")
    
    def test_immutability(self):
        """Test that configuration is immutable."""
        config = ApplicationConfig.get_default()

        # Attempting to modify should raise an exception
        with self.assertRaises(Exception):
            config.name = "New Name"

        with self.assertRaises(Exception):
            config.version = "2.0.0"

    def test_memory_override_settings(self):
        """Test memory override configuration fields."""
        config = ApplicationConfig.get_default()
        self.assertFalse(config.use_manual_memory_override)
        self.assertIsNone(config.manual_memory_override_mb)
        self.assertEqual(config.min_memory_specification_mb, 512)
        self.assertEqual(config.system_memory_reserve_percent, 20)

    def test_effective_memory_limit_auto_mode(self):
        """Test smart memory calculation in auto mode."""
        config = ApplicationConfig.get_default()
        available_mb = 6144  # 6GB available
        total_mb = 8192     # 8GB total
        limit = config.get_effective_memory_limit_mb(available_mb, total_mb)
        # min(1024, 3072, 6553) = 1024
        self.assertEqual(limit, 1024)

    def test_effective_memory_limit_manual_override(self):
        """Test manual override takes precedence."""
        config = ApplicationConfig(
            use_manual_memory_override=True,
            manual_memory_override_mb=2048
        )
        available_mb = 6144
        total_mb = 8192
        limit = config.get_effective_memory_limit_mb(available_mb, total_mb)
        # Should return manual override value
        self.assertEqual(limit, 2048)

    def test_effective_memory_limit_high_end_system(self):
        """Test memory calculation on high-end system (128GB)."""
        config = ApplicationConfig.get_default()
        available_mb = 82874   # ~80GB available
        total_mb = 130785      # ~128GB total
        limit = config.get_effective_memory_limit_mb(available_mb, total_mb)
        # min(1024, 41437, 104628) = 1024
        self.assertEqual(limit, 1024)

    def test_effective_memory_limit_respects_minimum(self):
        """Test that calculated limit respects minimum."""
        config = ApplicationConfig.get_default()
        available_mb = 256  # Very low available memory
        total_mb = 512      # Very low total
        limit = config.get_effective_memory_limit_mb(available_mb, total_mb)
        # Should not go below min_memory_specification_mb (512)
        self.assertGreaterEqual(limit, config.min_memory_specification_mb)


if __name__ == "__main__":
    unittest.main()