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


if __name__ == "__main__":
    unittest.main()