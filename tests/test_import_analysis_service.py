"""
Unit tests for ImportAnalysisService.

Tests cover:
- Service initialization
- Single model analysis
- Batch analysis
- Geometry calculations
- Progress tracking
- Cancellation support
- Error handling
- Memory management
"""

import unittest
import tempfile
import struct
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import time

from src.core.import_analysis_service import (
    ImportAnalysisService,
    GeometryAnalysisResult,
    BatchAnalysisResult,
    AnalysisStatus,
    AnalysisWorker,
    BatchAnalysisWorker
)
from src.core.cancellation_token import CancellationToken
from src.core.data_structures import Model, Triangle, Vector3D, ModelStats, ModelFormat, LoadingState


class TestImportAnalysisService(unittest.TestCase):
    """Test cases for ImportAnalysisService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = ImportAnalysisService(database_manager=Mock())
        
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Cancel any running analyses
        self.service.cancel_all_analysis()
        
        # Clean up temporary directory
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_service_initialization(self):
        """Test service initializes correctly."""
        self.assertIsNotNone(self.service.logger)
        self.assertIsNotNone(self.service.db_manager)
        self.assertEqual(len(self.service._active_workers), 0)
        self.assertEqual(len(self.service._results_cache), 0)
    
    def test_count_unique_vertices(self):
        """Test unique vertex counting."""
        # Create triangles with some duplicate vertices
        tri1 = Triangle(
            Vector3D(0, 0, 1),
            Vector3D(0, 0, 0),
            Vector3D(1, 0, 0),
            Vector3D(0, 1, 0)
        )
        tri2 = Triangle(
            Vector3D(0, 0, 1),
            Vector3D(0, 0, 0),  # Duplicate
            Vector3D(1, 0, 0),  # Duplicate
            Vector3D(1, 1, 0)
        )
        
        triangles = [tri1, tri2]
        unique_count, total_count = self.service._count_unique_vertices(triangles)
        
        self.assertEqual(total_count, 6)  # 2 triangles * 3 vertices
        self.assertEqual(unique_count, 4)  # 4 unique vertices
    
    def test_build_edge_map(self):
        """Test edge map building."""
        tri = Triangle(
            Vector3D(0, 0, 1),
            Vector3D(0, 0, 0),
            Vector3D(1, 0, 0),
            Vector3D(0, 1, 0)
        )
        
        edge_map, edge_count = self.service._build_edge_map([tri])
        
        self.assertEqual(edge_count, 3)  # Triangle has 3 edges
        # Each edge should be counted once
        for count in edge_map.values():
            self.assertEqual(count, 1)
    
    def test_triangle_area_calculation(self):
        """Test triangle area calculation."""
        # Create a right triangle with legs of length 1
        tri = Triangle(
            Vector3D(0, 0, 1),
            Vector3D(0, 0, 0),
            Vector3D(1, 0, 0),
            Vector3D(0, 1, 0)
        )
        
        area = self.service._triangle_area(tri)
        
        # Area should be 0.5 (1/2 * base * height = 1/2 * 1 * 1)
        self.assertAlmostEqual(area, 0.5, places=5)
    
    def test_surface_area_calculation(self):
        """Test surface area calculation for multiple triangles."""
        # Create two triangles
        tri1 = Triangle(
            Vector3D(0, 0, 1),
            Vector3D(0, 0, 0),
            Vector3D(1, 0, 0),
            Vector3D(0, 1, 0)
        )
        tri2 = Triangle(
            Vector3D(0, 0, 1),
            Vector3D(0, 0, 0),
            Vector3D(1, 0, 0),
            Vector3D(0, 0, 1)
        )
        
        surface_area = self.service._calculate_surface_area([tri1, tri2])
        
        # Total area should be sum of both triangles
        expected = self.service._triangle_area(tri1) + self.service._triangle_area(tri2)
        self.assertAlmostEqual(surface_area, expected, places=5)
    
    def test_count_non_manifold_edges(self):
        """Test non-manifold edge detection."""
        # Create edge map where one edge is shared by 3 triangles
        edge_map = {
            ('v1', 'v2'): 2,  # Normal edge (shared by 2 triangles)
            ('v2', 'v3'): 3,  # Non-manifold edge (shared by 3 triangles)
            ('v3', 'v4'): 1,  # Boundary edge
        }
        
        non_manifold_count = self.service._count_non_manifold_edges(edge_map)
        
        self.assertEqual(non_manifold_count, 1)
    
    def test_count_degenerate_triangles(self):
        """Test degenerate triangle detection."""
        # Create a degenerate triangle (collinear vertices)
        degenerate_tri = Triangle(
            Vector3D(0, 0, 1),
            Vector3D(0, 0, 0),
            Vector3D(1, 0, 0),
            Vector3D(2, 0, 0)  # Collinear with previous two
        )
        
        # Create a normal triangle
        normal_tri = Triangle(
            Vector3D(0, 0, 1),
            Vector3D(0, 0, 0),
            Vector3D(1, 0, 0),
            Vector3D(0, 1, 0)
        )
        
        degenerate_count = self.service._count_degenerate_triangles([degenerate_tri, normal_tri])
        
        self.assertEqual(degenerate_count, 1)
    
    def test_volume_calculation_watertight(self):
        """Test volume calculation for watertight mesh."""
        # Create a simple tetrahedron (watertight)
        triangles = [
            Triangle(Vector3D(0, 0, 1), Vector3D(0, 0, 0), Vector3D(1, 0, 0), Vector3D(0, 1, 0)),
            Triangle(Vector3D(0, 0, 1), Vector3D(0, 0, 0), Vector3D(0, 1, 0), Vector3D(0, 0, 1)),
            Triangle(Vector3D(0, 0, 1), Vector3D(0, 0, 0), Vector3D(0, 0, 1), Vector3D(1, 0, 0)),
            Triangle(Vector3D(0, 0, 1), Vector3D(1, 0, 0), Vector3D(0, 1, 0), Vector3D(0, 0, 1)),
        ]
        
        volume = self.service._calculate_volume(triangles, is_watertight=True)
        
        # Volume should be positive and non-zero
        self.assertIsNotNone(volume)
        self.assertGreater(volume, 0)
    
    def test_volume_calculation_non_watertight(self):
        """Test volume calculation returns None for non-watertight mesh."""
        triangles = [
            Triangle(Vector3D(0, 0, 1), Vector3D(0, 0, 0), Vector3D(1, 0, 0), Vector3D(0, 1, 0))
        ]
        
        volume = self.service._calculate_volume(triangles, is_watertight=False)
        
        self.assertIsNone(volume)
    
    def test_create_cancelled_result(self):
        """Test creation of cancelled result."""
        start_time = time.time()
        time.sleep(0.01)  # Small delay to ensure non-zero time
        
        result = self.service._create_cancelled_result(1, "test.stl", start_time)
        
        self.assertEqual(result.model_id, 1)
        self.assertEqual(result.status, AnalysisStatus.CANCELLED)
        self.assertGreater(result.analysis_time_seconds, 0)
    
    def test_get_analysis_result(self):
        """Test retrieving cached analysis result."""
        # Create and cache a result
        result = GeometryAnalysisResult(
            model_id=1,
            file_path="test.stl",
            triangle_count=100,
            vertex_count=300,
            face_count=50,
            edge_count=150,
            unique_vertex_count=150,
            bounding_box_min=(0, 0, 0),
            bounding_box_max=(10, 10, 10),
            bounding_box_dimensions=(10, 10, 10),
            volume=100.0,
            surface_area=200.0,
            non_manifold_edges=0,
            duplicate_vertices=0,
            degenerate_triangles=0,
            analysis_time_seconds=1.5,
            status=AnalysisStatus.COMPLETED
        )
        
        self.service._results_cache[1] = result
        
        # Retrieve result
        retrieved = self.service.get_analysis_result(1)
        
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.model_id, 1)
        self.assertEqual(retrieved.triangle_count, 100)
    
    def test_get_statistics(self):
        """Test getting service statistics."""
        stats = self.service.get_statistics()
        
        self.assertIn('total_analyzed', stats)
        self.assertIn('total_failed', stats)
        self.assertIn('total_cancelled', stats)
        self.assertIn('active_analyses', stats)
        self.assertIn('cached_results', stats)
        self.assertIn('avg_analysis_time', stats)
    
    def test_is_analysis_running(self):
        """Test checking if analysis is running."""
        # Initially no analysis running
        self.assertFalse(self.service.is_analysis_running(1))
        
        # Create a mock worker
        mock_worker = Mock()
        mock_worker.isRunning.return_value = True
        self.service._active_workers[1] = mock_worker
        
        # Now analysis should be running
        self.assertTrue(self.service.is_analysis_running(1))
    
    def test_result_to_dict(self):
        """Test converting result to dictionary."""
        result = GeometryAnalysisResult(
            model_id=1,
            file_path="test.stl",
            triangle_count=100,
            vertex_count=300,
            face_count=50,
            edge_count=150,
            unique_vertex_count=150,
            bounding_box_min=(0, 0, 0),
            bounding_box_max=(10, 10, 10),
            bounding_box_dimensions=(10, 10, 10),
            volume=100.0,
            surface_area=200.0,
            non_manifold_edges=0,
            duplicate_vertices=0,
            degenerate_triangles=0,
            analysis_time_seconds=1.5,
            status=AnalysisStatus.COMPLETED
        )
        
        result_dict = result.to_dict()
        
        self.assertIn('model_id', result_dict)
        self.assertIn('triangle_count', result_dict)
        self.assertIn('volume', result_dict)
        self.assertIn('surface_area', result_dict)
        self.assertIn('bounding_box_min_x', result_dict)
        self.assertEqual(result_dict['model_id'], 1)
        self.assertEqual(result_dict['triangle_count'], 100)


class TestGeometryAnalysis(unittest.TestCase):
    """Test geometry analysis with real model data."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = ImportAnalysisService(database_manager=Mock())
    
    def test_analyze_cube_geometry(self):
        """Test analyzing a simple cube geometry."""
        # Create a cube with 12 triangles (2 per face)
        # This is a simplified cube representation
        triangles = []
        
        # Bottom face
        triangles.append(Triangle(Vector3D(0, -1, 0), Vector3D(0, 0, 0), Vector3D(1, 0, 0), Vector3D(0, 0, 1)))
        triangles.append(Triangle(Vector3D(0, -1, 0), Vector3D(1, 0, 0), Vector3D(1, 0, 1), Vector3D(0, 0, 1)))
        
        # Top face
        triangles.append(Triangle(Vector3D(0, 1, 0), Vector3D(0, 1, 0), Vector3D(1, 1, 0), Vector3D(0, 1, 1)))
        triangles.append(Triangle(Vector3D(0, 1, 0), Vector3D(1, 1, 0), Vector3D(1, 1, 1), Vector3D(0, 1, 1)))
        
        model = Model(
            header="Test Cube",
            triangles=triangles,
            stats=ModelStats(
                vertex_count=12,
                triangle_count=4,
                min_bounds=Vector3D(0, 0, 0),
                max_bounds=Vector3D(1, 1, 1),
                file_size_bytes=1000,
                format_type=ModelFormat.STL,
                parsing_time_seconds=0.1
            ),
            format_type=ModelFormat.STL,
            loading_state=LoadingState.FULL_GEOMETRY
        )
        
        # Mock the _load_model method to return our test model
        with patch.object(self.service, '_load_model', return_value=model):
            result = self.service._analyze_single_model("test_cube.stl", 1, None, None)
        
        self.assertEqual(result.status, AnalysisStatus.COMPLETED)
        self.assertEqual(result.triangle_count, 4)
        self.assertGreater(result.surface_area, 0)


class TestCancellation(unittest.TestCase):
    """Test cancellation support."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = ImportAnalysisService(database_manager=Mock())
    
    def test_cancellation_token_respected(self):
        """Test that cancellation token is respected during analysis."""
        # Create a cancelled token
        token = CancellationToken()
        token.cancel()
        
        # Create a simple model
        model = Model(
            header="Test",
            triangles=[],
            stats=ModelStats(
                vertex_count=0,
                triangle_count=0,
                min_bounds=Vector3D(0, 0, 0),
                max_bounds=Vector3D(1, 1, 1),
                file_size_bytes=100,
                format_type=ModelFormat.STL,
                parsing_time_seconds=0.1
            ),
            format_type=ModelFormat.STL
        )
        
        # Mock _load_model to return test model
        with patch.object(self.service, '_load_model', return_value=model):
            result = self.service._analyze_single_model("test.stl", 1, None, token)
        
        self.assertEqual(result.status, AnalysisStatus.CANCELLED)


class TestBatchAnalysis(unittest.TestCase):
    """Test batch analysis functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = ImportAnalysisService(database_manager=Mock())
    
    def test_batch_analysis_empty_list(self):
        """Test batch analysis with empty file list."""
        result = self.service._analyze_batch_internal([], None, None)
        
        self.assertEqual(result.total_models, 0)
        self.assertEqual(result.successful, 0)
        self.assertEqual(result.failed, 0)
        self.assertEqual(result.cancelled, 0)
    
    def test_batch_analysis_statistics(self):
        """Test that batch analysis updates statistics correctly."""
        # Create mock results
        mock_results = [
            Mock(status=AnalysisStatus.COMPLETED),
            Mock(status=AnalysisStatus.COMPLETED),
            Mock(status=AnalysisStatus.FAILED),
        ]
        
        # Mock _analyze_single_model to return our mock results
        with patch.object(self.service, '_analyze_single_model', side_effect=mock_results):
            result = self.service._analyze_batch_internal(
                [("file1.stl", 1), ("file2.stl", 2), ("file3.stl", 3)],
                None,
                None
            )
        
        self.assertEqual(result.total_models, 3)
        self.assertEqual(result.successful, 2)
        self.assertEqual(result.failed, 1)


class TestMemoryManagement(unittest.TestCase):
    """Test memory management and cleanup."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = ImportAnalysisService(database_manager=Mock())
    
    def test_garbage_collection_called(self):
        """Test that garbage collection is called after analysis."""
        # This test verifies that gc.collect() is called
        # to ensure proper cleanup
        
        model = Model(
            header="Test",
            triangles=[],
            stats=ModelStats(
                vertex_count=0,
                triangle_count=0,
                min_bounds=Vector3D(0, 0, 0),
                max_bounds=Vector3D(1, 1, 1),
                file_size_bytes=100,
                format_type=ModelFormat.STL,
                parsing_time_seconds=0.1
            ),
            format_type=ModelFormat.STL
        )
        
        with patch.object(self.service, '_load_model', return_value=model):
            with patch('gc.collect') as mock_gc:
                self.service._analyze_single_model("test.stl", 1, None, None)
                
                # Verify gc.collect was called
                mock_gc.assert_called()


if __name__ == '__main__':
    unittest.main()