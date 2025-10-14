"""
Script to create sample STL files for testing.
"""

import struct
from pathlib import Path


def create_binary_sample():
    """Create a sample binary STL file (a simple cube)."""
    output_dir = Path(__file__).parent
    filepath = output_dir / "cube_binary.stl"
    
    # Define cube vertices (8 corners)
    vertices = [
        (0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),  # Bottom face
        (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)   # Top face
    ]
    
    # Define cube triangles (12 triangles for 6 faces)
    # Each triangle is defined as (normal, v1, v2, v3)
    triangles = [
        # Bottom face (z=0)
        ((0, 0, -1), vertices[0], vertices[1], vertices[2]),
        ((0, 0, -1), vertices[0], vertices[2], vertices[3]),
        
        # Top face (z=1)
        ((0, 0, 1), vertices[4], vertices[6], vertices[5]),
        ((0, 0, 1), vertices[4], vertices[7], vertices[6]),
        
        # Front face (y=0)
        ((0, -1, 0), vertices[0], vertices[5], vertices[1]),
        ((0, -1, 0), vertices[0], vertices[4], vertices[5]),
        
        # Back face (y=1)
        ((0, 1, 0), vertices[2], vertices[7], vertices[6]),
        ((0, 1, 0), vertices[2], vertices[3], vertices[7]),
        
        # Left face (x=0)
        ((-1, 0, 0), vertices[0], vertices[3], vertices[7]),
        ((-1, 0, 0), vertices[0], vertices[7], vertices[4]),
        
        # Right face (x=1)
        ((1, 0, 0), vertices[1], vertices[6], vertices[2]),
        ((1, 0, 0), vertices[1], vertices[5], vertices[6]),
    ]
    
    with open(filepath, 'wb') as f:
        # Write header (80 bytes)
        header = b"Sample Binary STL Cube - 3D-MM Test File"
        f.write(header.ljust(80, b'\x00'))
        
        # Write triangle count (4 bytes)
        f.write(struct.pack('<I', len(triangles)))
        
        # Write triangles
        for normal, v1, v2, v3 in triangles:
            # Normal vector (3 floats)
            f.write(struct.pack('<fff', *normal))
            
            # Vertex 1 (3 floats)
            f.write(struct.pack('<fff', *v1))
            
            # Vertex 2 (3 floats)
            f.write(struct.pack('<fff', *v2))
            
            # Vertex 3 (3 floats)
            f.write(struct.pack('<fff', *v3))
            
            # Attribute byte count (2 bytes)
            f.write(struct.pack('<H', 0))
    
    print(f"Created binary STL file: {filepath}")
    return filepath


def create_ascii_sample():
    """Create a sample ASCII STL file (a simple cube)."""
    output_dir = Path(__file__).parent
    filepath = output_dir / "cube_ascii.stl"
    
    # Define cube vertices (8 corners)
    vertices = [
        (0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),  # Bottom face
        (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)   # Top face
    ]
    
    # Define cube triangles (12 triangles for 6 faces)
    triangles = [
        # Bottom face (z=0)
        ((0, 0, -1), vertices[0], vertices[1], vertices[2]),
        ((0, 0, -1), vertices[0], vertices[2], vertices[3]),
        
        # Top face (z=1)
        ((0, 0, 1), vertices[4], vertices[6], vertices[5]),
        ((0, 0, 1), vertices[4], vertices[7], vertices[6]),
        
        # Front face (y=0)
        ((0, -1, 0), vertices[0], vertices[5], vertices[1]),
        ((0, -1, 0), vertices[0], vertices[4], vertices[5]),
        
        # Back face (y=1)
        ((0, 1, 0), vertices[2], vertices[7], vertices[6]),
        ((0, 1, 0), vertices[2], vertices[3], vertices[7]),
        
        # Left face (x=0)
        ((-1, 0, 0), vertices[0], vertices[3], vertices[7]),
        ((-1, 0, 0), vertices[0], vertices[7], vertices[4]),
        
        # Right face (x=1)
        ((1, 0, 0), vertices[1], vertices[6], vertices[2]),
        ((1, 0, 0), vertices[1], vertices[5], vertices[6]),
    ]
    
    with open(filepath, 'w') as f:
        f.write("solid Sample ASCII STL Cube - 3D-MM Test File\n")
        
        for normal, v1, v2, v3 in triangles:
            f.write(f"  facet normal {normal[0]} {normal[1]} {normal[2]}\n")
            f.write("    outer loop\n")
            f.write(f"      vertex {v1[0]} {v1[1]} {v1[2]}\n")
            f.write(f"      vertex {v2[0]} {v2[1]} {v2[2]}\n")
            f.write(f"      vertex {v3[0]} {v3[1]} {v3[2]}\n")
            f.write("    endloop\n")
            f.write("  endfacet\n")
        
        f.write("endsolid Sample ASCII STL Cube - 3D-MM Test File\n")
    
    print(f"Created ASCII STL file: {filepath}")
    return filepath


if __name__ == "__main__":
    # Create sample files directory if it doesn't exist
    sample_dir = Path(__file__).parent
    sample_dir.mkdir(exist_ok=True)
    
    create_binary_sample()
    create_ascii_sample()
    print("Sample STL files created successfully!")