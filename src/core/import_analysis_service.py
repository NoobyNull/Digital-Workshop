"""
Import Analysis Service for 3D Model Import Process.

Provides background geometry analysis for imported 3D models with:
- Triangle, vertex, face, and edge counting
- Bounding box calculation
- Volume and surface area estimation
- Mesh quality metrics
- Background processing with progress tracking
- Cancellation support
- Comprehensive JSON logging

Performance targets:
- Analysis time: < 5 seconds for models under 100MB
- Memory usage: Stable during repeated operations
- Background processing: Non-blocking UI

Example:
    >>> service = ImportAnalysisService()
    >>> service.analyze_model("model.stl", model_id=1)
    >>> result = service.get_analysis_result(1)
"""

import json
import logging
import time
import gc
import math
from pathlib import Path
from typing import Optional, Callable, List, Dict, Tuple
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict

from PySide6.QtCore import QThread, Signal

from src.core.logging_config import get_logger
from src.core.cancellation_token import CancellationToken
from src.core.data_structures import Model, Vector3D, Triangle
from src.parsers.stl_parser import STLParser
from src.core.database_manager import get_database_manager


class AnalysisStatus(Enum):
    """Analysis operation status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class GeometryAnalysisResult:
    """Result of geometry analysis for a 3D model."""

    model_id: int
    file_path: str
    triangle_count: int
    vertex_count: int
    face_count: int
    edge_count: int
    unique_vertex_count: int
    bounding_box_min: Tuple[float, float, float]
    bounding_box_max: Tuple[float, float, float]
    bounding_box_dimensions: Tuple[float, float, float]
    volume: Optional[float]
    surface_area: float
    non_manifold_edges: int
    duplicate_vertices: int
    degenerate_triangles: int
    analysis_time_seconds: float
    status: AnalysisStatus
    error_message: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert result to dictionary for database storage."""
        return {
            "model_id": self.model_id,
            "triangle_count": self.triangle_count,
            "vertex_count": self.vertex_count,
            "face_count": self.face_count,
            "edge_count": self.edge_count,
            "volume": self.volume,
            "surface_area": self.surface_area,
            "bounding_box_min_x": self.bounding_box_min[0],
            "bounding_box_min_y": self.bounding_box_min[1],
            "bounding_box_min_z": self.bounding_box_min[2],
            "bounding_box_max_x": self.bounding_box_max[0],
            "bounding_box_max_y": self.bounding_box_max[1],
            "bounding_box_max_z": self.bounding_box_max[2],
            "analysis_time_seconds": self.analysis_time_seconds,
        }


@dataclass
class BatchAnalysisResult:
    """Result of batch analysis operation."""

    total_models: int
    successful: int
    failed: int
    cancelled: int
    total_time: float
    results: List[GeometryAnalysisResult]


class AnalysisWorker(QThread):
    """
    Background worker thread for model geometry analysis.

    Performs detailed geometry analysis without blocking the UI thread.
    """

    # Signals for communication with main thread
    progress_updated = Signal(int, int, str)  # current, total, message
    analysis_completed = Signal(int, object)  # model_id, GeometryAnalysisResult
    analysis_failed = Signal(int, str)  # model_id, error_message
    batch_completed = Signal(object)  # BatchAnalysisResult

    def __init__(
        self,
        file_path: str,
        model_id: int,
        cancellation_token: Optional[CancellationToken] = None,
    ):
        """
        Initialize the analysis worker.

        Args:
            file_path: Path to the model file
            model_id: Database ID of the model
            cancellation_token: Optional cancellation token
        """
        super().__init__()
        self.file_path = file_path
        self.model_id = model_id
        self.cancellation_token = cancellation_token or CancellationToken()
        self.logger = get_logger(__name__)
        self.service = None  # Will be set by parent

    def run(self) -> None:
        """Execute the analysis in background thread."""
        try:
            if self.service:
                result = self.service._analyze_single_model(
                    self.file_path,
                    self.model_id,
                    lambda curr, total, msg: self.progress_updated.emit(curr, total, msg),
                    self.cancellation_token,
                )

                if result.status == AnalysisStatus.COMPLETED:
                    self.analysis_completed.emit(self.model_id, result)
                elif result.status == AnalysisStatus.FAILED:
                    self.analysis_failed.emit(
                        self.model_id, result.error_message or "Unknown error"
                    )

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Worker thread error: %s", e, exc_info=True)
            self.analysis_failed.emit(self.model_id, str(e))


class BatchAnalysisWorker(QThread):
    """
    Background worker for batch analysis of multiple models.
    """

    # Signals
    progress_updated = Signal(int, int, str)  # current, total, message
    batch_completed = Signal(object)  # BatchAnalysisResult

    def __init__(
        self,
        file_model_pairs: List[Tuple[str, int]],
        service,
        cancellation_token: Optional[CancellationToken] = None,
    ):
        """
        Initialize batch analysis worker.

        Args:
            file_model_pairs: List of (file_path, model_id) tuples
            service: Reference to ImportAnalysisService
            cancellation_token: Optional cancellation token
        """
        super().__init__()
        self.file_model_pairs = file_model_pairs
        self.service = service
        self.cancellation_token = cancellation_token or CancellationToken()
        self.logger = get_logger(__name__)

    def run(self) -> None:
        """Execute batch analysis."""
        try:
            result = self.service._analyze_batch_internal(
                self.file_model_pairs,
                lambda curr, total, msg: self.progress_updated.emit(curr, total, msg),
                self.cancellation_token,
            )
            self.batch_completed.emit(result)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Batch worker error: %s", e, exc_info=True)


class ImportAnalysisService:
    """
    Service for analyzing 3D model geometry during the import process.

    Provides comprehensive geometry analysis including:
    - Triangle, vertex, face, and edge counting
    - Bounding box calculation and dimensions
    - Volume estimation (for watertight meshes)
    - Surface area calculation
    - Mesh quality metrics (non-manifold edges, degenerate triangles)
    - Background processing with progress tracking
    - Cancellation support
    - Database integration for storing results

    The service can analyze models in background threads without blocking
    the UI, with support for both single and batch operations.

    Example:
        >>> service = ImportAnalysisService()
        >>> service.start_analysis("model.stl", model_id=1)
        >>> # Analysis runs in background
        >>> result = service.get_analysis_result(1)
    """

    def __init__(self, database_manager=None) -> None:
        """
        Initialize the import analysis service.

        Args:
            database_manager: Optional database manager instance
        """
        self.logger = get_logger(__name__)
        self.db_manager = database_manager or get_database_manager()

        # Active workers
        self._active_workers: Dict[int, AnalysisWorker] = {}
        self._batch_worker: Optional[BatchAnalysisWorker] = None

        # Analysis results cache
        self._results_cache: Dict[int, GeometryAnalysisResult] = {}

        # Statistics
        self._stats = {
            "total_analyzed": 0,
            "total_failed": 0,
            "total_cancelled": 0,
            "total_analysis_time": 0.0,
        }

        self._log_json(
            "service_initialized",
            {"database_manager": str(type(self.db_manager).__name__)},
        )

    def _log_json(self, event: str, data: dict) -> None:
        """Log event in JSON format as required by quality standards."""
        # Only log if DEBUG level is enabled to reduce verbosity
        if not self.logger.isEnabledFor(logging.DEBUG):
            return

        log_entry = {"event": event, "timestamp": time.time(), **data}
        self.logger.debug(json.dumps(log_entry))

    def start_analysis(
        self,
        file_path: str,
        model_id: int,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        completion_callback: Optional[Callable[[GeometryAnalysisResult], None]] = None,
        cancellation_token: Optional[CancellationToken] = None,
    ) -> None:
        """
        Start background analysis of a 3D model.

        Args:
            file_path: Path to the model file
            model_id: Database ID of the model
            progress_callback: Optional callback(current, total, message)
            completion_callback: Optional callback(result) when complete
            cancellation_token: Optional cancellation token
        """
        self._log_json(
            "analysis_started",
            {"model_id": model_id, "file_path": Path(file_path).name},
        )

        # Create worker thread
        worker = AnalysisWorker(file_path, model_id, cancellation_token)
        worker.service = self

        # Connect signals
        if progress_callback:
            worker.progress_updated.connect(progress_callback)

        if completion_callback:
            worker.analysis_completed.connect(lambda mid, result: completion_callback(result))

        # Connect internal handlers
        worker.analysis_completed.connect(self._on_analysis_completed)
        worker.analysis_failed.connect(self._on_analysis_failed)
        worker.finished.connect(lambda: self._on_worker_finished(model_id))

        # Store and start worker
        self._active_workers[model_id] = worker
        worker.start()

    def start_batch_analysis(
        self,
        file_model_pairs: List[Tuple[str, int]],
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        completion_callback: Optional[Callable[[BatchAnalysisResult], None]] = None,
        cancellation_token: Optional[CancellationToken] = None,
    ) -> None:
        """
        Start background batch analysis of multiple models.

        Args:
            file_model_pairs: List of (file_path, model_id) tuples
            progress_callback: Optional callback(current, total, message)
            completion_callback: Optional callback(BatchAnalysisResult) when complete
            cancellation_token: Optional cancellation token
        """
        self._log_json("batch_analysis_started", {"total_models": len(file_model_pairs)})

        # Create batch worker
        worker = BatchAnalysisWorker(file_model_pairs, self, cancellation_token)

        # Connect signals
        if progress_callback:
            worker.progress_updated.connect(progress_callback)

        if completion_callback:
            worker.batch_completed.connect(completion_callback)

        # Connect internal handler
        worker.batch_completed.connect(self._on_batch_completed)

        # Store and start worker
        self._batch_worker = worker
        worker.start()

    def _analyze_single_model(
        self,
        file_path: str,
        model_id: int,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        cancellation_token: Optional[CancellationToken] = None,
    ) -> GeometryAnalysisResult:
        """
        Analyze a single model (internal method for worker threads).

        Args:
            file_path: Path to the model file
            model_id: Database ID of the model
            progress_callback: Optional progress callback
            cancellation_token: Optional cancellation token

        Returns:
            GeometryAnalysisResult with analysis details
        """
        start_time = time.time()
        file_name = Path(file_path).name

        try:
            # Check cancellation
            if cancellation_token is not None and cancellation_token.is_cancelled():
                return self._create_cancelled_result(model_id, file_path, start_time)

            # Report progress
            if progress_callback:
                progress_callback(0, 100, f"Loading {file_name}...")

            # Load model using appropriate parser
            model = self._load_model(file_path, progress_callback, cancellation_token)

            if cancellation_token is not None and cancellation_token.is_cancelled():
                return self._create_cancelled_result(model_id, file_path, start_time)

            # Perform geometry analysis
            if progress_callback:
                progress_callback(40, 100, "Analyzing geometry...")

            result = self._perform_geometry_analysis(
                model,
                model_id,
                file_path,
                start_time,
                progress_callback,
                cancellation_token,
            )

            # Store in database
            if result.status == AnalysisStatus.COMPLETED:
                if progress_callback:
                    progress_callback(95, 100, "Saving results...")
                self._store_analysis_result(result)

            if progress_callback:
                progress_callback(100, 100, "Analysis complete")

            # Force garbage collection
            gc.collect()

            return result

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            analysis_time = time.time() - start_time
            error_msg = f"Analysis failed: {e}"

            self.logger.error("%s for {file_name}", error_msg, exc_info=True)
            self._log_json(
                "analysis_failed",
                {
                    "model_id": model_id,
                    "file": file_name,
                    "error": str(e),
                    "analysis_time_seconds": round(analysis_time, 3),
                },
            )

            return GeometryAnalysisResult(
                model_id=model_id,
                file_path=file_path,
                triangle_count=0,
                vertex_count=0,
                face_count=0,
                edge_count=0,
                unique_vertex_count=0,
                bounding_box_min=(0, 0, 0),
                bounding_box_max=(0, 0, 0),
                bounding_box_dimensions=(0, 0, 0),
                volume=None,
                surface_area=0.0,
                non_manifold_edges=0,
                duplicate_vertices=0,
                degenerate_triangles=0,
                analysis_time_seconds=analysis_time,
                status=AnalysisStatus.FAILED,
                error_message=error_msg,
            )

    def _load_model(
        self,
        file_path: str,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        cancellation_token: Optional[CancellationToken] = None,
    ) -> Model:
        """
        Load a 3D model using the appropriate parser.

        Args:
            file_path: Path to the model file
            progress_callback: Optional progress callback
            cancellation_token: Optional cancellation token

        Returns:
            Loaded Model object
        """
        file_ext = Path(file_path).suffix.lower()

        # For now, we support STL files
        # TODO: Add support for OBJ, STEP, 3MF, etc.
        if file_ext == ".stl":
            parser = STLParser()

            # Create progress wrapper if needed
            parser_progress = None
            if progress_callback:

                def parser_progress_wrapper(percent, message) -> None:
                    # Map parser progress (0-100) to our range (0-40)
                    mapped_percent = int(percent * 0.4)
                    progress_callback(mapped_percent, 100, message)

                class ProgressWrapper:
                    def report(self, percent, message) -> None:
                        parser_progress_wrapper(percent, message)

                parser_progress = ProgressWrapper()

            model = parser.parse_file(file_path, parser_progress)
            return model
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")

    def _perform_geometry_analysis(
        self,
        model: Model,
        model_id: int,
        file_path: str,
        start_time: float,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        cancellation_token: Optional[CancellationToken] = None,
    ) -> GeometryAnalysisResult:
        """
        Perform detailed geometry analysis on a loaded model.

        Args:
            model: Loaded Model object
            model_id: Database ID
            file_path: Path to model file
            start_time: Analysis start time
            progress_callback: Optional progress callback
            cancellation_token: Optional cancellation token

        Returns:
            GeometryAnalysisResult with all metrics
        """
        # Basic counts
        triangle_count = len(model.triangles) if model.triangles else model.stats.triangle_count
        vertex_count = triangle_count * 3

        # Check cancellation
        if cancellation_token is not None and cancellation_token.is_cancelled():
            return self._create_cancelled_result(model_id, file_path, start_time)

        # Count unique vertices and build edge map
        if progress_callback:
            progress_callback(50, 100, "Analyzing vertices and edges...")

        unique_vertices, vertex_count_actual = self._count_unique_vertices(
            model.triangles if model.triangles else []
        )
        edge_map, edge_count = self._build_edge_map(model.triangles if model.triangles else [])

        # Check cancellation
        if cancellation_token is not None and cancellation_token.is_cancelled():
            return self._create_cancelled_result(model_id, file_path, start_time)

        # Detect mesh quality issues
        if progress_callback:
            progress_callback(60, 100, "Checking mesh quality...")

        non_manifold_count = self._count_non_manifold_edges(edge_map)
        degenerate_count = self._count_degenerate_triangles(
            model.triangles if model.triangles else []
        )
        duplicate_vertices = vertex_count_actual - unique_vertices

        # Calculate surface area
        if progress_callback:
            progress_callback(70, 100, "Calculating surface area...")

        surface_area = self._calculate_surface_area(model.triangles if model.triangles else [])

        # Check cancellation
        if cancellation_token and cancellation_token.is_cancelled():
            return self._create_cancelled_result(model_id, file_path, start_time)

        # Calculate volume (if watertight)
        if progress_callback:
            progress_callback(80, 100, "Calculating volume...")

        volume = self._calculate_volume(
            model.triangles if model.triangles else [], non_manifold_count == 0
        )

        # Get bounding box from model stats
        min_bounds = model.stats.min_bounds
        max_bounds = model.stats.max_bounds

        bounding_box_min = (min_bounds.x, min_bounds.y, min_bounds.z)
        bounding_box_max = (max_bounds.x, max_bounds.y, max_bounds.z)
        bounding_box_dims = (
            max_bounds.x - min_bounds.x,
            max_bounds.y - min_bounds.y,
            max_bounds.z - min_bounds.z,
        )

        # Face count (approximate as triangle count / 2 for typical models)
        face_count = triangle_count // 2

        analysis_time = time.time() - start_time

        self._log_json(
            "analysis_completed",
            {
                "model_id": model_id,
                "file": Path(file_path).name,
                "triangle_count": triangle_count,
                "vertex_count": vertex_count_actual,
                "unique_vertices": unique_vertices,
                "edge_count": edge_count,
                "surface_area": round(surface_area, 3),
                "volume": round(volume, 3) if volume else None,
                "non_manifold_edges": non_manifold_count,
                "degenerate_triangles": degenerate_count,
                "analysis_time_seconds": round(analysis_time, 3),
            },
        )

        return GeometryAnalysisResult(
            model_id=model_id,
            file_path=file_path,
            triangle_count=triangle_count,
            vertex_count=vertex_count_actual,
            face_count=face_count,
            edge_count=edge_count,
            unique_vertex_count=unique_vertices,
            bounding_box_min=bounding_box_min,
            bounding_box_max=bounding_box_max,
            bounding_box_dimensions=bounding_box_dims,
            volume=volume,
            surface_area=surface_area,
            non_manifold_edges=non_manifold_count,
            duplicate_vertices=duplicate_vertices,
            degenerate_triangles=degenerate_count,
            analysis_time_seconds=analysis_time,
            status=AnalysisStatus.COMPLETED,
        )

    def _count_unique_vertices(self, triangles: List[Triangle]) -> Tuple[int, int]:
        """
        Count unique vertices in the model.

        Args:
            triangles: List of triangles

        Returns:
            Tuple of (unique_count, total_count)
        """
        if not triangles:
            return 0, 0

        # Use set to track unique vertices (with rounding for floating point)
        unique_verts = set()
        total_count = 0

        for tri in triangles:
            for vertex in tri.get_vertices():
                total_count += 1
                # Round to 6 decimal places to handle floating point precision
                vert_tuple = (
                    round(vertex.x, 6),
                    round(vertex.y, 6),
                    round(vertex.z, 6),
                )
                unique_verts.add(vert_tuple)

        return len(unique_verts), total_count

    def _build_edge_map(self, triangles: List[Triangle]) -> Tuple[Dict, int]:
        """
        Build edge connectivity map for mesh analysis.

        Args:
            triangles: List of triangles

        Returns:
            Tuple of (edge_map, edge_count)
        """
        edge_map = defaultdict(int)

        for tri in triangles:
            vertices = tri.get_vertices()
            # Create edges from triangle vertices
            edges = [
                (vertices[0], vertices[1]),
                (vertices[1], vertices[2]),
                (vertices[2], vertices[0]),
            ]

            for v1, v2 in edges:
                # Normalize edge (always smaller vertex first)
                edge_key = tuple(
                    sorted(
                        [
                            (round(v1.x, 6), round(v1.y, 6), round(v1.z, 6)),
                            (round(v2.x, 6), round(v2.y, 6), round(v2.z, 6)),
                        ]
                    )
                )
                edge_map[edge_key] += 1

        return edge_map, len(edge_map)

    def _count_non_manifold_edges(self, edge_map: Dict) -> int:
        """
        Count non-manifold edges (edges shared by more than 2 triangles).

        Args:
            edge_map: Edge connectivity map

        Returns:
            Count of non-manifold edges
        """
        non_manifold = 0
        for count in edge_map.values():
            if count > 2:
                non_manifold += 1
        return non_manifold

    def _count_degenerate_triangles(self, triangles: List[Triangle]) -> int:
        """
        Count degenerate triangles (zero area or collinear vertices).

        Args:
            triangles: List of triangles

        Returns:
            Count of degenerate triangles
        """
        degenerate = 0
        epsilon = 1e-10

        for tri in triangles:
            area = self._triangle_area(tri)
            if area < epsilon:
                degenerate += 1

        return degenerate

    def _triangle_area(self, triangle: Triangle) -> float:
        """
        Calculate triangle area using cross product.

        Args:
            triangle: Triangle object

        Returns:
            Triangle area
        """
        v1 = triangle.vertex1
        v2 = triangle.vertex2
        v3 = triangle.vertex3

        # Vectors from v1 to v2 and v1 to v3
        a = Vector3D(v2.x - v1.x, v2.y - v1.y, v2.z - v1.z)
        b = Vector3D(v3.x - v1.x, v3.y - v1.y, v3.z - v1.z)

        # Cross product
        cross = Vector3D(a.y * b.z - a.z * b.y, a.z * b.x - a.x * b.z, a.x * b.y - a.y * b.x)

        # Magnitude
        magnitude = math.sqrt(cross.x**2 + cross.y**2 + cross.z**2)
        return magnitude / 2.0

    def _calculate_surface_area(self, triangles: List[Triangle]) -> float:
        """
        Calculate total surface area of the model.

        Args:
            triangles: List of triangles

        Returns:
            Total surface area
        """
        if not triangles:
            return 0.0

        total_area = 0.0
        for tri in triangles:
            total_area += self._triangle_area(tri)

        return total_area

    def _calculate_volume(self, triangles: List[Triangle], is_watertight: bool) -> Optional[float]:
        """
        Calculate volume using signed volume of tetrahedra method.
        Only accurate for watertight meshes.

        Args:
            triangles: List of triangles
            is_watertight: Whether mesh is watertight (no non-manifold edges)

        Returns:
            Volume if watertight, None otherwise
        """
        if not triangles or not is_watertight:
            return None

        volume = 0.0

        for tri in triangles:
            v1 = tri.vertex1
            v2 = tri.vertex2
            v3 = tri.vertex3

            # Signed volume of tetrahedron formed by triangle and origin
            volume += (
                v1.x * (v2.y * v3.z - v2.z * v3.y)
                + v2.x * (v3.y * v1.z - v3.z * v1.y)
                + v3.x * (v1.y * v2.z - v1.z * v2.y)
            ) / 6.0

        return abs(volume)

    def _create_cancelled_result(
        self, model_id: int, file_path: str, start_time: float
    ) -> GeometryAnalysisResult:
        """Create a cancelled result."""
        analysis_time = time.time() - start_time

        self._log_json(
            "analysis_cancelled",
            {
                "model_id": model_id,
                "file": Path(file_path).name,
                "analysis_time_seconds": round(analysis_time, 3),
            },
        )

        return GeometryAnalysisResult(
            model_id=model_id,
            file_path=file_path,
            triangle_count=0,
            vertex_count=0,
            face_count=0,
            edge_count=0,
            unique_vertex_count=0,
            bounding_box_min=(0, 0, 0),
            bounding_box_max=(0, 0, 0),
            bounding_box_dimensions=(0, 0, 0),
            volume=None,
            surface_area=0.0,
            non_manifold_edges=0,
            duplicate_vertices=0,
            degenerate_triangles=0,
            analysis_time_seconds=analysis_time,
            status=AnalysisStatus.CANCELLED,
        )

    def _analyze_batch_internal(
        self,
        file_model_pairs: List[Tuple[str, int]],
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        cancellation_token: Optional[CancellationToken] = None,
    ) -> BatchAnalysisResult:
        """
        Internal method for batch analysis.

        Args:
            file_model_pairs: List of (file_path, model_id) tuples
            progress_callback: Optional progress callback
            cancellation_token: Optional cancellation token

        Returns:
            BatchAnalysisResult with summary
        """
        start_time = time.time()
        total_models = len(file_model_pairs)
        results = []

        for idx, (file_path, model_id) in enumerate(file_model_pairs):
            # Check cancellation
            if cancellation_token is not None and cancellation_token.is_cancelled():
                break

            # Report progress
            if progress_callback:
                file_name = Path(file_path).name
                progress_callback(idx, total_models, f"Analyzing {file_name}...")

            # Analyze model
            result = self._analyze_single_model(file_path, model_id, None, cancellation_token)
            results.append(result)

        # Final progress
        if progress_callback:
            progress_callback(len(results), total_models, "Batch analysis complete")

        batch_time = time.time() - start_time
        successful = sum(1 for r in results if r.status == AnalysisStatus.COMPLETED)
        failed = sum(1 for r in results if r.status == AnalysisStatus.FAILED)
        cancelled = sum(1 for r in results if r.status == AnalysisStatus.CANCELLED)

        self._log_json(
            "batch_analysis_completed",
            {
                "total_models": total_models,
                "successful": successful,
                "failed": failed,
                "cancelled": cancelled,
                "time_seconds": round(batch_time, 3),
                "avg_time_per_model": round(batch_time / max(1, len(results)), 3),
            },
        )

        return BatchAnalysisResult(
            total_models=total_models,
            successful=successful,
            failed=failed,
            cancelled=cancelled,
            total_time=batch_time,
            results=results,
        )

    def _store_analysis_result(self, result: GeometryAnalysisResult) -> None:
        """
        Store analysis result in the database.

        Args:
            result: GeometryAnalysisResult to store
        """
        try:
            # TODO: Implement database storage when model_analysis table is created
            # For now, just cache it
            self._results_cache[result.model_id] = result

            self.logger.info("Stored analysis result for model %s", result.model_id)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to store analysis result: %s", e, exc_info=True)

    def get_analysis_result(self, model_id: int) -> Optional[GeometryAnalysisResult]:
        """
        Get cached analysis result for a model.

        Args:
            model_id: Database ID of the model

        Returns:
            GeometryAnalysisResult if available, None otherwise
        """
        return self._results_cache.get(model_id)

    def is_analysis_running(self, model_id: int) -> bool:
        """
        Check if analysis is currently running for a model.

        Args:
            model_id: Database ID of the model

        Returns:
            True if analysis is running
        """
        return model_id in self._active_workers

    def cancel_analysis(self, model_id: int) -> bool:
        """
        Cancel analysis for a specific model.

        Args:
            model_id: Database ID of the model

        Returns:
            True if cancellation was requested
        """
        worker = self._active_workers.get(model_id)
        if worker and worker.isRunning():
            worker.cancellation_token.cancel()
            self.logger.info("Requested cancellation for model %s", model_id)
            return True
        return False

    def cancel_all_analysis(self) -> None:
        """Cancel all running analyses."""
        for model_id in list(self._active_workers.keys()):
            self.cancel_analysis(model_id)

        if self._batch_worker and self._batch_worker.isRunning():
            self._batch_worker.cancellation_token.cancel()

    def _on_analysis_completed(self, model_id: int, result: GeometryAnalysisResult) -> None:
        """Handle analysis completion."""
        self._stats["total_analyzed"] += 1
        self._stats["total_analysis_time"] += result.analysis_time_seconds
        self._results_cache[model_id] = result

    def _on_analysis_failed(self, model_id: int, error_message: str) -> None:
        """Handle analysis failure."""
        self._stats["total_failed"] += 1
        self.logger.error("Analysis failed for model %s: {error_message}", model_id)

    def _on_worker_finished(self, model_id: int) -> None:
        """Handle worker thread completion."""
        if model_id in self._active_workers:
            del self._active_workers[model_id]

    def _on_batch_completed(self, result: BatchAnalysisResult) -> None:
        """Handle batch completion."""
        self._stats["total_analyzed"] += result.successful
        self._stats["total_failed"] += result.failed
        self._stats["total_cancelled"] += result.cancelled
        self._batch_worker = None

    def get_statistics(self) -> Dict:
        """
        Get service statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            **self._stats,
            "active_analyses": len(self._active_workers),
            "cached_results": len(self._results_cache),
            "avg_analysis_time": round(
                self._stats["total_analysis_time"] / max(1, self._stats["total_analyzed"]),
                3,
            ),
        }
