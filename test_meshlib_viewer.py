"""
Test script to evaluate meshlib's 3D visualization capabilities
for potential use as a VTK alternative in the 3D-MM application.
"""

import sys
import time
from pathlib import Path

# Add the src directory to the path to import our modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from parsers.stl_parser import STLModel, STLParser
from core.data_structures import Model, LoadingState, Vector3D, Triangle
from core.logging_config import get_logger

# Import meshlib modules
try:
    from meshlib import mrmeshpy, mrviewerpy
    MESHLIB_AVAILABLE = True
    print("MeshLib successfully imported")
except ImportError as e:
    MESHLIB_AVAILABLE = False
    print(f"MeshLib import failed: {e}")

def test_meshlib_stl_loading():
    """Test loading an STL file using meshlib."""
    if not MESHLIB_AVAILABLE:
        print("MeshLib not available, skipping test")
        return False
    
    logger = get_logger(__name__)
    
    # Try to load a sample STL file
    sample_stl = Path("tests/sample_files/cube_ascii.stl")
    if not sample_stl.exists():
        print(f"Sample STL file not found: {sample_stl}")
        return False
    
    try:
        # Load using our STL parser first
        stl_parser = STLParser()
        stl_model = stl_parser.parse_file(str(sample_stl))
        
        print(f"Loaded STL with {stl_model.stats.triangle_count} triangles using our parser")
        
        # Convert to meshlib format
        mesh = mrmeshpy.Mesh()
        
        # Add points and triangles from our STL model
        point_map = {}
        for triangle in stl_model.triangles:
            # Get or create points for each vertex
            for i, vertex in enumerate([triangle.vertex1, triangle.vertex2, triangle.vertex3]):
                key = (vertex.x, vertex.y, vertex.z)
                if key not in point_map:
                    point_id = mesh.points.addPoint(mrmeshpy.Vector3f(vertex.x, vertex.y, vertex.z))
                    point_map[key] = point_id
            
            # Add triangle
            v1 = point_map[(triangle.vertex1.x, triangle.vertex1.y, triangle.vertex1.z)]
            v2 = point_map[(triangle.vertex2.x, triangle.vertex2.y, triangle.vertex2.z)]
            v3 = point_map[(triangle.vertex3.x, triangle.vertex3.y, triangle.vertex3.z)]
            
            face = mrmeshpy.Face(v1, v2, v3)
            mesh.topology.addFace(face)
        
        print(f"Created meshlib mesh with {mesh.points.numPoints()} points and {mesh.topology.numFaces()} faces")
        return True
        
    except Exception as e:
        logger.error(f"Error testing meshlib STL loading: {e}")
        return False

def test_meshlib_direct_load():
    """Test loading STL directly with meshlib."""
    if not MESHLIB_AVAILABLE:
        print("MeshLib not available, skipping test")
        return False
    
    logger = get_logger(__name__)
    
    sample_stl = Path("tests/sample_files/cube_ascii.stl")
    if not sample_stl.exists():
        print(f"Sample STL file not found: {sample_stl}")
        return False
    
    try:
        # Try to load directly with meshlib
        load_settings = mrmeshpy.MeshLoadSettings()
        
        loaded_obj = mrmeshpy.loadMesh(str(sample_stl), load_settings)
        if loaded_obj:
            mesh = loaded_obj
            print(f"Direct meshlib load successful: {mesh.points.numPoints()} points, {mesh.topology.numFaces()} faces")
            return True
        else:
            print("Direct meshlib load failed or returned empty mesh")
            return False
            
    except Exception as e:
        logger.error(f"Error testing direct meshlib load: {e}")
        return False

def test_meshlib_viewer():
    """Test meshlib's viewer capabilities."""
    if not MESHLIB_AVAILABLE:
        print("MeshLib not available, skipping test")
        return False
    
    logger = get_logger(__name__)
    
    try:
        # Create viewer launch parameters
        launch_params = mrviewerpy.ViewerLaunchParams()
        launch_params.name = "MeshLib Test Viewer"
        launch_params.width = 800
        launch_params.height = 600
        launch_params.windowMode = mrviewerpy.ViewerLaunchParamsMode.Show
        
        # Note: We won't actually launch the viewer as it would block
        # But we can verify the setup works
        print("MeshLib viewer setup successful (not launching to avoid blocking)")
        
        # Test that we can create a viewer instance
        viewer = mrviewerpy.Viewer()
        print("MeshLib viewer instance created successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing meshlib viewer: {e}")
        return False

def compare_with_vtk():
    """Compare meshlib capabilities with current VTK implementation."""
    print("\n=== MeshLib vs VTK Comparison ===")
    
    # VTK capabilities (from current implementation)
    vtk_features = [
        "Interactive camera controls (orbit, pan, zoom)",
        "Multiple rendering modes (solid, wireframe, points)",
        "Qt integration via QVTKRenderWindowInteractor",
        "Performance monitoring and FPS tracking",
        "Progressive loading with quality levels",
        "Axes orientation indicator",
        "Configurable lighting",
        "Memory-efficient rendering with resource cleanup"
    ]
    
    # MeshLib capabilities (based on our research)
    meshlib_features = [
        "GLFW-based mesh viewer",
        "Scene tree management",
        "Multiple object types (meshes, points, voxels, lines)",
        "Viewport management",
        "Camera controls",
        "Screenshot capture",
        "UI system for controls",
        "Python bindings for mesh processing",
        "Direct STL loading",
        "Selection system"
    ]
    
    print("\nVTK Features:")
    for feature in vtk_features:
        print(f"  [OK] {feature}")
    
    print("\nMeshLib Features:")
    for feature in meshlib_features:
        print(f"  [OK] {feature}")
    
    print("\nKey Differences:")
    print("  - VTK: Mature, Qt-integrated, more visualization features")
    print("  - MeshLib: Newer, GLFW-based, more mesh processing features")
    print("  - VTK: Better for embedded Qt widgets")
    print("  - MeshLib: Standalone viewer with comprehensive UI")

def main():
    """Main test function."""
    print("=== MeshLib Evaluation for 3D-MM ===")
    
    # Test basic meshlib functionality
    print("\n1. Testing meshlib STL loading...")
    test1 = test_meshlib_stl_loading()
    
    print("\n2. Testing direct meshlib STL loading...")
    test2 = test_meshlib_direct_load()
    
    print("\n3. Testing meshlib viewer setup...")
    test3 = test_meshlib_viewer()
    
    # Compare with VTK
    print("\n4. Comparing with VTK...")
    compare_with_vtk()
    
    # Summary
    print("\n=== Test Results ===")
    print(f"STL Loading (manual conversion): {'[PASS]' if test1 else '[FAIL]'}")
    print(f"STL Loading (direct): {'[PASS]' if test2 else '[FAIL]'}")
    print(f"Viewer Setup: {'[PASS]' if test3 else '[FAIL]'}")
    
    if test1 or test2:
        print("\nMeshLib can successfully load STL files")
    else:
        print("\nMeshLib STL loading failed")
    
    if test3:
        print("MeshLib viewer setup works")
    else:
        print("MeshLib viewer setup failed")
    
    print("\n=== Recommendation ===")
    if MESHLIB_AVAILABLE and (test1 or test2):
        print("MeshLib shows promise as a VTK alternative, but:")
        print("  1. It uses GLFW instead of Qt, making integration more complex")
        print("  2. The viewer is standalone, not easily embedded in Qt widgets")
        print("  3. VTK provides better Qt integration for this use case")
        print("  4. MeshLib would require significant architectural changes")
        print("\nRecommendation: Stick with VTK for this application")
    else:
        print("MeshLib is not suitable as a VTK alternative for this application")

if __name__ == "__main__":
    main()