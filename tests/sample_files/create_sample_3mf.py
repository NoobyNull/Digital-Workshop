"""
Script to create a simple 3MF file for testing the 3MF parser.
"""

import zipfile
import os
from pathlib import Path


def create_sample_3mf():
    """Create a sample 3MF file with a simple cube."""
    # Create the 3D model content
    model_content = """<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">
  <metadata name="Title">Test Cube</metadata>
  <metadata name="Designer">3D-MM</metadata>
  <metadata name="Description">Simple cube for testing 3MF parser</metadata>
  <resources>
    <object id="1" type="model">
      <mesh>
        <vertices>
          <vertex x="0" y="0" z="0" />
          <vertex x="100" y="0" z="0" />
          <vertex x="100" y="100" z="0" />
          <vertex x="0" y="100" z="0" />
          <vertex x="0" y="0" z="100" />
          <vertex x="100" y="0" z="100" />
          <vertex x="100" y="100" z="100" />
          <vertex x="0" y="100" z="100" />
        </vertices>
        <triangles>
          <!-- Bottom face -->
          <triangle v1="0" v2="1" v3="2" />
          <triangle v1="0" v2="2" v3="3" />
          <!-- Top face -->
          <triangle v1="4" v2="7" v3="6" />
          <triangle v1="4" v2="6" v3="5" />
          <!-- Front face -->
          <triangle v1="0" v2="4" v3="5" />
          <triangle v1="0" v2="5" v3="1" />
          <!-- Back face -->
          <triangle v1="2" v2="6" v3="7" />
          <triangle v1="2" v2="7" v3="3" />
          <!-- Left face -->
          <triangle v1="0" v2="3" v3="7" />
          <triangle v1="0" v2="7" v3="4" />
          <!-- Right face -->
          <triangle v1="1" v2="5" v3="6" />
          <triangle v1="1" v2="6" v3="2" />
        </triangles>
      </mesh>
    </object>
  </resources>
  <build>
    <item objectid="1" />
  </build>
</model>"""

    # Create content types file
    content_types_content = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml" />
    <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml" />
</Types>"""

    # Create relationships file
    rels_content = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel" />
</Relationships>"""

    # Create the 3MF file
    output_path = Path(__file__).parent / "cube.3mf"
    
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add content types
        zf.writestr("[Content_Types].xml", content_types_content)
        
        # Add relationships
        zf.writestr("_rels/.rels", rels_content)
        
        # Add 3D model
        zf.writestr("3D/3dmodel.model", model_content)
    
    print(f"Created sample 3MF file: {output_path}")


if __name__ == "__main__":
    create_sample_3mf()