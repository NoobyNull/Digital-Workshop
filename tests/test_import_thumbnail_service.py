"""
Unit tests for ImportThumbnailService.

Tests thumbnail generation, caching, storage management, and batch operations.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.core.import_thumbnail_service import (
    ImportThumbnailService,
    StorageLocation,
    ThumbnailGenerationResult,
    ThumbnailBatchResult
)
from src.core.cancellation_token import CancellationToken


class TestImportThumbnailService(unittest.TestCase):
    """Test suite for ImportThumbnailService."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for test thumbnails
        self.temp_dir = tempfile.mkdtemp()
        self.test_storage_path = Path(self.temp_dir) / "test_thumbnails"
        self.test_storage_path.mkdir(parents=True, exist_ok=True)
        
        # Mock settings manager
        self.mock_settings = Mock()
        
    def tearDown(self):
        """Clean up test fixtures."""
        # Remove temporary directory
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_service_initialization_custom_storage(self):
        """Test service initialization with custom storage location."""
        service = ImportThumbnailService(
            storage_location=StorageLocation.CUSTOM,
            custom_storage_path=str(self.test_storage_path),
            settings_manager=self.mock_settings
        )
        
        self.assertEqual(service.storage_location, StorageLocation.CUSTOM)
        self.assertEqual(service.get_storage_directory(), self.test_storage_path)
        self.assertTrue(self.test_storage_path.exists())
    
    def test_service_initialization_appdata_storage(self):
        """Test service initialization with AppData storage location."""
        with patch.dict('os.environ', {'APPDATA': self.temp_dir}):
            service = ImportThumbnailService(
                storage_location=StorageLocation.APPDATA,
                settings_manager=self.mock_settings
            )
            
            expected_dir = Path(self.temp_dir) / "3DModelManager" / "thumbnails"
            self.assertEqual(service.get_storage_directory(), expected_dir)
            self.assertTrue(expected_dir.exists())
    
    def test_get_thumbnail_path(self):
        """Test getting thumbnail path for a given hash."""
        service = ImportThumbnailService(
            storage_location=StorageLocation.CUSTOM,
            custom_storage_path=str(self.test_storage_path)
        )
        
        test_hash = "abc123def456"
        expected_path = self.test_storage_path / f"{test_hash}.png"
        
        result_path = service.get_thumbnail_path(test_hash)
        self.assertEqual(result_path, expected_path)
    
    def test_is_thumbnail_cached_not_exists(self):
        """Test cache check when thumbnail doesn't exist."""
        service = ImportThumbnailService(
            storage_location=StorageLocation.CUSTOM,
            custom_storage_path=str(self.test_storage_path)
        )
        
        test_hash = "nonexistent_hash"
        self.assertFalse(service.is_thumbnail_cached(test_hash))
    
    def test_is_thumbnail_cached_exists(self):
        """Test cache check when thumbnail exists."""
        service = ImportThumbnailService(
            storage_location=StorageLocation.CUSTOM,
            custom_storage_path=str(self.test_storage_path)
        )
        
        # Create a fake thumbnail file
        test_hash = "existing_hash"
        thumbnail_path = self.test_storage_path / f"{test_hash}.png"
        thumbnail_path.write_bytes(b"fake_png_data")
        
        self.assertTrue(service.is_thumbnail_cached(test_hash))
    
    @patch('src.core.import_thumbnail_service.ThumbnailGenerator')
    def test_generate_thumbnail_success(self, mock_generator_class):
        """Test successful thumbnail generation."""
        # Setup mock
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        
        test_hash = "test_hash_123"
        expected_thumbnail_path = self.test_storage_path / f"{test_hash}.png"
        
        # Mock will create the file when called
        def create_thumbnail(*args, **kwargs):
            expected_thumbnail_path.write_bytes(b"fake_png_data")
            return expected_thumbnail_path
        
        mock_generator.generate_thumbnail.side_effect = create_thumbnail
        
        service = ImportThumbnailService(
            storage_location=StorageLocation.CUSTOM,
            custom_storage_path=str(self.test_storage_path)
        )
        
        result = service.generate_thumbnail(
            model_path="test_model.stl",
            file_hash=test_hash
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.file_hash, test_hash)
        self.assertEqual(result.thumbnail_path, expected_thumbnail_path)
        self.assertFalse(result.cached)
        self.assertIsNone(result.error)
    
    @patch('src.core.import_thumbnail_service.ThumbnailGenerator')
    def test_generate_thumbnail_cached(self, mock_generator_class):
        """Test thumbnail generation when already cached."""
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        
        test_hash = "cached_hash"
        thumbnail_path = self.test_storage_path / f"{test_hash}.png"
        
        # Create existing thumbnail
        thumbnail_path.write_bytes(b"existing_thumbnail")
        
        service = ImportThumbnailService(
            storage_location=StorageLocation.CUSTOM,
            custom_storage_path=str(self.test_storage_path)
        )
        
        result = service.generate_thumbnail(
            model_path="test_model.stl",
            file_hash=test_hash
        )
        
        self.assertTrue(result.success)
        self.assertTrue(result.cached)
        self.assertEqual(result.thumbnail_path, thumbnail_path)
        
        # Generator should not be called for cached thumbnail
        mock_generator.generate_thumbnail.assert_not_called()
    
    @patch('src.core.import_thumbnail_service.ThumbnailGenerator')
    def test_generate_thumbnail_force_regenerate(self, mock_generator_class):
        """Test forced thumbnail regeneration even when cached."""
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        
        test_hash = "force_regen_hash"
        thumbnail_path = self.test_storage_path / f"{test_hash}.png"
        
        # Create existing thumbnail
        thumbnail_path.write_bytes(b"old_thumbnail")
        
        mock_generator.generate_thumbnail.return_value = thumbnail_path
        
        service = ImportThumbnailService(
            storage_location=StorageLocation.CUSTOM,
            custom_storage_path=str(self.test_storage_path)
        )
        
        result = service.generate_thumbnail(
            model_path="test_model.stl",
            file_hash=test_hash,
            force_regenerate=True
        )
        
        self.assertTrue(result.success)
        self.assertFalse(result.cached)
        
        # Generator should be called even though thumbnail exists
        mock_generator.generate_thumbnail.assert_called_once()
    
    @patch('src.core.import_thumbnail_service.ThumbnailGenerator')
    def test_generate_thumbnail_failure(self, mock_generator_class):
        """Test thumbnail generation failure."""
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        mock_generator.generate_thumbnail.return_value = None
        
        service = ImportThumbnailService(
            storage_location=StorageLocation.CUSTOM,
            custom_storage_path=str(self.test_storage_path)
        )
        
        result = service.generate_thumbnail(
            model_path="test_model.stl",
            file_hash="fail_hash"
        )
        
        self.assertFalse(result.success)
        self.assertIsNone(result.thumbnail_path)
        self.assertIsNotNone(result.error)
    
    @patch('src.core.import_thumbnail_service.ThumbnailGenerator')
    def test_generate_thumbnails_batch(self, mock_generator_class):
        """Test batch thumbnail generation."""
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        
        # Setup test data
        file_info_list = [
            ("model1.stl", "hash1"),
            ("model2.stl", "hash2"),
            ("model3.stl", "hash3")
        ]
        
        # Mock successful generation for all files
        def mock_generate(model_path, file_hash, **kwargs):
            thumbnail_path = self.test_storage_path / f"{file_hash}.png"
            thumbnail_path.write_bytes(b"thumbnail_data")
            return thumbnail_path
        
        mock_generator.generate_thumbnail.side_effect = mock_generate
        
        service = ImportThumbnailService(
            storage_location=StorageLocation.CUSTOM,
            custom_storage_path=str(self.test_storage_path)
        )
        
        # Track progress callbacks
        progress_calls = []
        def progress_callback(completed, total, current_file):
            progress_calls.append((completed, total, current_file))
        
        result = service.generate_thumbnails_batch(
            file_info_list=file_info_list,
            progress_callback=progress_callback
        )
        
        self.assertEqual(result.total_files, 3)
        self.assertEqual(result.successful, 3)
        self.assertEqual(result.failed, 0)
        self.assertEqual(result.cached, 0)
        self.assertEqual(len(result.results), 3)
        
        # Verify progress callbacks were made
        self.assertGreater(len(progress_calls), 0)
    
    @patch('src.core.import_thumbnail_service.ThumbnailGenerator')
    def test_batch_generation_with_cancellation(self, mock_generator_class):
        """Test batch generation with cancellation support."""
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        
        file_info_list = [
            ("model1.stl", "hash1"),
            ("model2.stl", "hash2"),
            ("model3.stl", "hash3")
        ]
        
        # Create cancellation token - cancel before starting
        cancellation_token = CancellationToken()
        cancellation_token.cancel()  # Cancel immediately
        
        def mock_generate(*args, **kwargs):
            # Extract file_hash from kwargs or args
            file_hash = kwargs.get('file_hash', args[1] if len(args) > 1 else 'hash1')
            thumbnail_path = self.test_storage_path / f"{file_hash}.png"
            thumbnail_path.write_bytes(b"thumbnail_data")
            return thumbnail_path
        
        mock_generator.generate_thumbnail.side_effect = mock_generate
        
        service = ImportThumbnailService(
            storage_location=StorageLocation.CUSTOM,
            custom_storage_path=str(self.test_storage_path)
        )
        
        result = service.generate_thumbnails_batch(
            file_info_list=file_info_list,
            cancellation_token=cancellation_token
        )
        
        # Should stop immediately due to cancellation
        self.assertEqual(result.total_files, 3)
        self.assertEqual(result.successful, 0)  # No files should be processed
    
    def test_cleanup_orphaned_thumbnails(self):
        """Test cleanup of orphaned thumbnails."""
        service = ImportThumbnailService(
            storage_location=StorageLocation.CUSTOM,
            custom_storage_path=str(self.test_storage_path)
        )
        
        # Create some thumbnail files
        valid_hash = "valid_hash_1"
        orphan_hash_1 = "orphan_hash_1"
        orphan_hash_2 = "orphan_hash_2"
        
        (self.test_storage_path / f"{valid_hash}.png").write_bytes(b"valid")
        (self.test_storage_path / f"{orphan_hash_1}.png").write_bytes(b"orphan1")
        (self.test_storage_path / f"{orphan_hash_2}.png").write_bytes(b"orphan2")
        
        # Cleanup with only valid hash
        result = service.cleanup_orphaned_thumbnails(
            valid_hashes=[valid_hash]
        )
        
        self.assertEqual(result['removed'], 2)
        self.assertEqual(result['kept'], 1)
        self.assertEqual(result['errors'], 0)
        
        # Verify files were removed
        self.assertTrue((self.test_storage_path / f"{valid_hash}.png").exists())
        self.assertFalse((self.test_storage_path / f"{orphan_hash_1}.png").exists())
        self.assertFalse((self.test_storage_path / f"{orphan_hash_2}.png").exists())
    
    def test_clear_cache(self):
        """Test clearing the in-memory cache."""
        service = ImportThumbnailService(
            storage_location=StorageLocation.CUSTOM,
            custom_storage_path=str(self.test_storage_path)
        )
        
        # Add some items to cache
        test_hash = "test_hash"
        thumbnail_path = self.test_storage_path / f"{test_hash}.png"
        thumbnail_path.write_bytes(b"thumbnail")
        
        # Trigger cache population
        service.is_thumbnail_cached(test_hash)
        
        # Verify cache has items
        stats = service.get_cache_statistics()
        self.assertGreater(stats['cache_size'], 0)
        
        # Clear cache
        service.clear_cache()
        
        # Verify cache is empty
        stats = service.get_cache_statistics()
        self.assertEqual(stats['cache_size'], 0)
    
    def test_get_cache_statistics(self):
        """Test getting cache statistics."""
        service = ImportThumbnailService(
            storage_location=StorageLocation.CUSTOM,
            custom_storage_path=str(self.test_storage_path)
        )
        
        stats = service.get_cache_statistics()
        
        self.assertIn('cache_size', stats)
        self.assertIn('storage_dir', stats)
        self.assertIn('thumbnails_generated', stats)
        self.assertIn('thumbnails_cached', stats)
        self.assertIn('cache_hit_rate', stats)
        
        self.assertEqual(stats['cache_size'], 0)
        self.assertEqual(stats['thumbnails_generated'], 0)
    
    def test_set_storage_directory(self):
        """Test changing storage directory."""
        service = ImportThumbnailService(
            storage_location=StorageLocation.CUSTOM,
            custom_storage_path=str(self.test_storage_path)
        )
        
        old_dir = service.get_storage_directory()
        
        # Create new storage location
        new_storage = Path(self.temp_dir) / "new_thumbnails"
        
        service.set_storage_directory(
            storage_location=StorageLocation.CUSTOM,
            custom_path=str(new_storage)
        )
        
        new_dir = service.get_storage_directory()
        
        self.assertNotEqual(old_dir, new_dir)
        self.assertEqual(new_dir, new_storage)
        self.assertTrue(new_storage.exists())
    
    def test_verify_thumbnail_valid(self):
        """Test verifying a valid thumbnail."""
        service = ImportThumbnailService(
            storage_location=StorageLocation.CUSTOM,
            custom_storage_path=str(self.test_storage_path)
        )
        
        test_hash = "valid_png_hash"
        thumbnail_path = self.test_storage_path / f"{test_hash}.png"
        
        # Write valid PNG header
        png_header = b'\x89PNG\r\n\x1a\n'
        thumbnail_path.write_bytes(png_header + b'dummy_png_data')
        
        self.assertTrue(service.verify_thumbnail(test_hash))
    
    def test_verify_thumbnail_invalid_header(self):
        """Test verifying thumbnail with invalid PNG header."""
        service = ImportThumbnailService(
            storage_location=StorageLocation.CUSTOM,
            custom_storage_path=str(self.test_storage_path)
        )
        
        test_hash = "invalid_png_hash"
        thumbnail_path = self.test_storage_path / f"{test_hash}.png"
        
        # Write invalid header
        thumbnail_path.write_bytes(b'not_a_png_file')
        
        self.assertFalse(service.verify_thumbnail(test_hash))
    
    def test_verify_thumbnail_empty_file(self):
        """Test verifying an empty thumbnail file."""
        service = ImportThumbnailService(
            storage_location=StorageLocation.CUSTOM,
            custom_storage_path=str(self.test_storage_path)
        )
        
        test_hash = "empty_file_hash"
        thumbnail_path = self.test_storage_path / f"{test_hash}.png"
        
        # Write empty file
        thumbnail_path.write_bytes(b'')
        
        self.assertFalse(service.verify_thumbnail(test_hash))
    
    def test_verify_thumbnail_not_exists(self):
        """Test verifying a non-existent thumbnail."""
        service = ImportThumbnailService(
            storage_location=StorageLocation.CUSTOM,
            custom_storage_path=str(self.test_storage_path)
        )
        
        test_hash = "nonexistent_hash"
        self.assertFalse(service.verify_thumbnail(test_hash))
    
    @patch('src.core.import_thumbnail_service.ThumbnailGenerator')
    def test_memory_efficiency_batch_operations(self, mock_generator_class):
        """Test memory efficiency during batch operations."""
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        
        # Create large batch
        file_info_list = [(f"model{i}.stl", f"hash{i}") for i in range(20)]
        
        def mock_generate(model_path, file_hash, **kwargs):
            thumbnail_path = self.test_storage_path / f"{file_hash}.png"
            thumbnail_path.write_bytes(b"thumbnail_data")
            return thumbnail_path
        
        mock_generator.generate_thumbnail.side_effect = mock_generate
        
        service = ImportThumbnailService(
            storage_location=StorageLocation.CUSTOM,
            custom_storage_path=str(self.test_storage_path)
        )
        
        result = service.generate_thumbnails_batch(file_info_list=file_info_list)
        
        # Verify all were processed
        self.assertEqual(result.total_files, 20)
        self.assertEqual(result.successful, 20)
        
        # Verify statistics are tracking correctly
        stats = service.get_cache_statistics()
        self.assertEqual(stats['thumbnails_generated'], 20)


class TestStorageLocation(unittest.TestCase):
    """Test the StorageLocation enum."""
    
    def test_storage_location_values(self):
        """Test StorageLocation enum values."""
        self.assertEqual(StorageLocation.APPDATA.value, "appdata")
        self.assertEqual(StorageLocation.CUSTOM.value, "custom")


class TestThumbnailResults(unittest.TestCase):
    """Test result data classes."""
    
    def test_thumbnail_generation_result(self):
        """Test ThumbnailGenerationResult dataclass."""
        result = ThumbnailGenerationResult(
            file_path="test.stl",
            file_hash="abc123",
            thumbnail_path=Path("test.png"),
            generation_time=1.5,
            success=True,
            error=None,
            cached=False
        )
        
        self.assertEqual(result.file_path, "test.stl")
        self.assertEqual(result.file_hash, "abc123")
        self.assertTrue(result.success)
        self.assertFalse(result.cached)
    
    def test_thumbnail_batch_result(self):
        """Test ThumbnailBatchResult dataclass."""
        result = ThumbnailBatchResult(
            total_files=10,
            successful=8,
            failed=2,
            cached=3,
            total_time=15.5,
            results=[]
        )
        
        self.assertEqual(result.total_files, 10)
        self.assertEqual(result.successful, 8)
        self.assertEqual(result.failed, 2)
        self.assertEqual(result.cached, 3)


if __name__ == '__main__':
    unittest.main()