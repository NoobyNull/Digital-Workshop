<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Model Management - Digital Workshop User Manual</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5rem;
            font-weight: 300;
        }
        .content {
            padding: 40px;
            max-width: 900px;
            margin: 0 auto;
        }
        .toc {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 25px;
            margin: 30px 0;
        }
        .toc h3 {
            margin-top: 0;
            color: #2c3e50;
        }
        .toc ul {
            list-style-type: none;
            padding-left: 0;
        }
        .toc li {
            margin: 10px 0;
        }
        .toc a {
            color: #007bff;
            text-decoration: none;
            padding: 5px 0;
            display: block;
        }
        .toc a:hover {
            text-decoration: underline;
        }
        .section {
            margin: 40px 0;
        }
        .section h2 {
            color: #2c3e50;
            border-bottom: 3px solid #007bff;
            padding-bottom: 10px;
            margin-top: 40px;
        }
        .section h3 {
            color: #34495e;
            margin-top: 30px;
        }
        .note {
            background: #e7f3ff;
            border-left: 4px solid #007bff;
            padding: 15px;
            margin: 20px 0;
        }
        .warning {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
        }
        .tip {
            background: #d4edda;
            border-left: 4px solid #28a745;
            padding: 15px;
            margin: 20px 0;
        }
        .image-placeholder {
            background: #f8f9fa;
            border: 2px dashed #dee2e6;
            padding: 40px;
            text-align: center;
            margin: 20px 0;
            color: #6c757d;
            font-style: italic;
        }
        .btn {
            display: inline-block;
            background: #007bff;
            color: white;
            padding: 12px 24px;
            border-radius: 6px;
            text-decoration: none;
            margin: 10px 10px 10px 0;
            transition: background-color 0.3s ease;
        }
        .btn:hover {
            background: #0056b3;
        }
        .back-link {
            background: #6c757d;
            margin-top: 40px;
        }
        .back-link:hover {
            background: #5a6268;
        }
        .file-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .file-card {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 6px;
            padding: 15px;
            text-align: center;
            transition: transform 0.2s ease;
        }
        .file-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .file-icon {
            font-size: 2rem;
            margin-bottom: 10px;
        }
        .workflow-step {
            background: #e9ecef;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            border-left: 4px solid #007bff;
        }
        .workflow-step h4 {
            margin-top: 0;
            color: #2c3e50;
        }
        .search-example {
            background: #f8f9fa;
            border: 1px solid #ced4da;
            border-radius: 4px;
            padding: 10px;
            font-family: monospace;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Model Management</h1>
            <p>Import, Organize, and Search Your 3D Model Library</p>
        </div>

        <div class="content">
            <div class="toc">
                <h3>📋 Quick Navigation</h3>
                <ul>
                    <li><a href="#file-import">File Import Methods</a></li>
                    <li><a href="#supported-formats">Supported File Formats</a></li>
                    <li><a href="#organization-system">Library Organization</a></li>
                    <li><a href="#search-functionality">Search and Filter</a></li>
                    <li><a href="#project-association">Project Association</a></li>
                    <li><a href="#bulk-operations">Bulk Operations</a></li>
                    <li><a href="#file-maintenance">File Maintenance</a></li>
                </ul>
            </div>

            <div class="section">
                <p>Think of Digital Workshop's Model Library as your digital lumber yard and hardware store combined. Just as you would organize physical materials in your workshop - separating hardwood from softwood, keeping hardware sorted by size and type - the Model Library helps you organize your digital files systematically and efficiently.</p>

                <p>The key to successful model management is the "Keep Organized" principle applied to digital files. A well-organized library saves time, reduces frustration, and makes your design process smoother. Whether you're importing models from online sources, scanning physical objects, or creating designs from scratch, proper organization ensures you can find what you need when you need it.</p>

                <div class="image-placeholder">
                    [Image: model-library-overview.png]
                    <br>Figure 1: Complete Model Library interface showing organized file structure
                </div>
            </div>

            <div class="section" id="file-import">
                <h2>File Import Methods</h2>

                <p>Digital Workshop supports multiple ways to get your 3D models into the system, each designed for different situations and user preferences. Think of these as different routes to your workshop - some faster, some more thorough, but all leading to the same destination.</p>

                <h3>Drag and Drop Import</h3>
                <p>The simplest method for importing files is drag and drop, similar to carrying lumber from your truck to your workshop bench:</p>

                <div class="workflow-step">
                    <h4>📁 How to Use Drag and Drop</h4>
                    <ol>
                        <li>Open Digital Workshop and navigate to the Model Library panel</li>
                        <li>Locate your 3D files in Windows Explorer (or Finder on Mac)</li>
                        <li>Select one or multiple files by clicking and dragging a selection box</li>
                        <li>Drag the selected files into the Model Library panel</li>
                        <li>Files will automatically appear in your library with thumbnails</li>
                        <li>Digital Workshop will analyze and optimize each file automatically</li>
                    </ol>
                </div>

                <div class="tip">
                    <strong>💡 Efficiency Tip:</strong> You can drag entire folders of 3D models into Digital Workshop, and it will import all supported files automatically. This is especially useful when organizing a large collection of downloaded models or when moving your entire library to a new computer.
                </div>

                <h3>Menu-Based Import</h3>
                <p>For more control over the import process, use the menu-based approach:</p>

                <div class="workflow-step">
                    <h4>🎯 Using the Import Menu</h4>
                    <ol>
                        <li>Click <strong>File → Import → 3D Models</strong> from the main menu</li>
                        <li>Navigate to your desired folder in the file browser</li>
                        <li>Select individual files or use Ctrl-click (Cmd-click on Mac) for multiple selection</li>
                        <li>Review import settings before proceeding</li>
                        <li>Click "Import" to begin the process</li>
                        <li>Monitor progress in the status bar</li>
                    </ol>
                </div>

                <h3>Import Settings</h3>
                <p>Digital Workshop offers several import configuration options to optimize your workflow:</p>

                <ul>
                    <li><strong>Auto-Organize:</strong> Automatically sort imported files by type and date</li>
                    <li><strong>Create Thumbnails:</strong> Generate preview images for quick visual identification</li>
                    <li><strong>Optimize Geometry:</strong> Reduce file size while maintaining quality</li>
                    <li><strong>Apply Default Materials:</strong> Automatically assign wood textures based on model content</li>
                    <li><strong>Generate Metadata:</strong> Create searchable tags and descriptions</li>
                </ul>

                <div class="note">
                    <strong>📝 Import Tip:</strong> The first time you import models, enable all import features. This ensures your library is complete and searchable from the start. You can disable features later if you prefer faster imports.
                </div>

                <div class="image-placeholder">
                    [Image: import-dialog-settings.png]
                    <br>Figure 2: Import dialog with configuration options
                </div>
            </div>

            <div class="section" id="supported-formats">
                <h2>Supported File Formats</h2>

                <p>Digital Workshop supports most major 3D file formats, ensuring compatibility with virtually any 3D modeling software or online source. Think of these formats as different languages for describing 3D objects - Digital Workshop speaks them all fluently.</p>

                <h3>Primary Supported Formats</h3>
                <div class="file-grid">
                    <div class="file-card">
                        <div class="file-icon">📄</div>
                        <h4>STL</h4>
                        <p>Standard format for 3D printing and CNC machining</p>
                    </div>
                    <div class="file-card">
                        <div class="file-icon">📄</div>
                        <h4>OBJ</h4>
                        <p>Universal format supporting materials and textures</p>
                    </div>
                    <div class="file-card">
                        <div class="file-icon">📄</div>
                        <h4>PLY</h4>
                        <p>Stanford Polygon Library format for complex models</p>
                    </div>
                    <div class="file-card">
                        <div class="file-icon">📄</div>
                        <h4>3MF</h4>
                        <p>Modern format for 3D manufacturing</p>
                    </div>
                </div>

                <h3>CAD Format Support</h3>
                <div class="file-grid">
                    <div class="file-card">
                        <div class="file-icon">📄</div>
                        <h4>DXF</h4>
                        <p>AutoCAD Drawing Exchange Format</p>
                    </div>
                    <div class="file-card">
                        <div class="file-icon">📄</div>
                        <h4>DWG</h4>
                        <p>AutoCAD native format</p>
                    </div>
                    <div class="file-card">
                        <div class="file-icon">📄</div>
                        <h4>STEP</h4>
                        <p>Standard for Exchange of Product Data</p>
                    </div>
                    <div class="file-card">
                        <div class="file-icon">📄</div>
                        <h4>IGES</h4>
                        <p>Initial Graphics Exchange Specification</p>
                    </div>
                </div>

                <h3>Proprietary Format Support</h3>
                <p>Digital Workshop can also import from popular 3D modeling software:</p>
                <ul>
                    <li><strong>SketchUp (.skp):</strong> Google SketchUp files</li>
                    <li><strong>Fusion 360 (.f3d):</strong> Autodesk Fusion 360 projects</li>
                    <li><strong>SolidWorks (.sldprt):</strong> SolidWorks parts and assemblies</li>
                    <li><strong>Rhino (.3dm):</strong> Rhinoceros 3D models</li>
                    <li><strong>Blender (.blend):</strong> Blender project files</li>
                </ul>

                <div class="warning">
                    <strong>⚠️ Format Considerations:</strong> While Digital Workshop supports many formats, complex proprietary files may require conversion. If you encounter issues importing a specific format, try exporting to STL or OBJ first - these are the most universally compatible formats.
                </div>

                <h3>File Size and Complexity Limits</h3>
                <p>To maintain optimal performance, Digital Workshop has recommended limits:</p>
                <ul>
                    <li><strong>Maximum File Size:</strong> 500 MB per model (larger files will be automatically optimized)</li>
                    <li><strong>Maximum Polygons:</strong> 10 million triangles (excessively complex models will be simplified)</li>
                    <li><strong>Recommended Size:</strong> 1-50 MB for optimal performance and quick loading</li>
                </ul>

                <div class="note">
                    <strong>🔧 Optimization Note:</strong> Digital Workshop automatically optimizes large or complex models during import. This process preserves visual quality while reducing file size and improving performance. You can monitor this process in the import progress dialog.
                </div>
            </div>

            <div class="section" id="organization-system">
                <h2>Library Organization System</h2>

                <p>Digital Workshop's organization system is designed around the same principles that make a well-organized workshop efficient: logical grouping, easy access, and systematic maintenance. Just as you might organize your physical workshop with dedicated areas for different types of work, the Model Library provides flexible organizational tools.</p>

                <h3>Folder-Based Organization</h3>
                <p>The foundation of the organization system is a flexible folder structure that you can customize to match your workflow:</p>

                <div class="workflow-step">
                    <h4>📁 Creating Your Folder Structure</h4>
                    <ol>
                        <li>Right-click in the Model Library panel</li>
                        <li>Select "New Folder" from the context menu</li>
                        <li>Enter a descriptive name (e.g., "Chair Components", "Hardware", "Templates")</li>
                        <li>Drag and drop models into appropriate folders</li>
                        <li>Create subfolders for detailed organization</li>
                    </ol>
                </div>

                <h4>Recommended Folder Structures</h4>
                <div class="panel-description" style="margin: 20px 0;">
                    <h5>🏗️ Project-Based Organization</h5>
                    <ul>
                        <li>Bookcase_Project_2025/</li>
                        <ul>
                            <li>Components/ (individual parts)</li>
                            <li>Hardware/ (fasteners, brackets)</li>
                            <li>Templates/ (patterns, jigs)</li>
                            <li>Materials/ (wood species references)</li>
                        </ul>
                    </ul>
                </div>

                <div class="panel-description" style="margin: 20px 0;">
                    <h5>🪵 Material-Based Organization</h5>
                    <ul>
                        <li>Hardwood/</li>
                        <ul>
                            <li>Oak/</li>
                            <li>Maple/</li>
                            <li>Cherry/</li>
                            <li>Walnut/</li>
                        </ul>
                        <li>Softwood/</li>
                        <ul>
                            <li>Pine/</li>
                            <li>Cedar/</li>
                            <li>Fir/</li>
                        </ul>
                        <li>Sheet_Goods/</li>
                        <ul>
                            <li>Plywood/</li>
                            <li>MDF/</li>
                            <li>Particleboard/</li>
                        </ul>
                    </ul>
                </div>

                <div class="panel-description" style="margin: 20px 0;">
                    <h5>🔧 Function-Based Organization</h5>
                    <ul>
                        <li>Joinery/</li>
                        <ul>
                            <li>Dovetails/</li>
                            <li>Mortise_Tenon/</li>
                            <li>Biscuit_Joints/</li>
                        </ul>
                        <li>Hardware/</li>
                        <ul>
                            <li>Hinges/</li>
                            <li>Handles/</li>
                            <li>Fasteners/</li>
                        </ul>
                        <li>Patterns/</li>
                        <ul>
                            <li>Curves/</li>
                            <li>Profiles/</li>
                            <li>Templates/</li>
                        </ul>
                    </ul>
                </div>

                <h3>Automatic Organization Features</h3>
                <p>Digital Workshop includes intelligent features to help maintain organization:</p>

                <h4>Smart Sorting</h4>
                <ul>
                    <li><strong>Date-Based:</strong> Automatically sort by import date or modification date</li>
                    <li><strong>Type-Based:</strong> Group files by format (STL, OBJ, etc.)</li>
                    <li><strong>Size-Based:</strong> Sort by file size for easy identification of large files</li>
                    <li><strong>Usage-Based:</strong> Prioritize frequently used models</li>
                </ul>

                <h4>Intelligent Tagging</h4>
                <p>When you import models, Digital Workshop automatically analyzes and tags them:</p>
                <ul>
                    <li><strong>Content Tags:</strong> "chair", "table", "cabinet", "hardware"</li>
                    <li><strong>Material Tags:</strong> "wood", "metal", "plastic"</li>
                    <li><strong>Complexity Tags:</strong> "simple", "detailed", "ornate"</li>
                    <li><strong>Project Tags:</strong> "furniture", "decorative", "functional"</li>
                </ul>

                <div class="tip">
                    <strong>💡 Organization Tip:</strong> Spend 5 minutes creating your folder structure before importing large numbers of files. It's much easier to organize as you go than to reorganize scattered files later. Think of this like laying out your workshop before moving in tools and materials.
                </div>

                <div class="image-placeholder">
                    [Image: folder-structure-examples.png]
                    <br>Figure 3: Examples of different organizational folder structures
                </div>
            </div>

            <div class="section" id="search-functionality">
                <h2>Search and Filter Capabilities</h2>

                <p>The search functionality in Digital Workshop is like having a skilled assistant who knows exactly where everything is stored in your workshop. Whether you're looking for a specific component or trying to find similar designs, the search system helps you locate files quickly and efficiently.</p>

                <h3>Basic Search</h3>
                <p>The simple search box at the top of the Model Library panel provides quick access to your files:</p>

                <div class="search-example">
                    Search examples:<br>
                    • "chair" - finds all models containing "chair"<br>
                    • "oak" - finds models with oak materials<br>
                    • "2024" - finds models from 2024<br>
                    • "hardware" - finds fasteners and brackets
                </div>

                <h3>Advanced Search Options</h3>
                <p>For complex searches, use the advanced search dialog:</p>

                <h4>Text-Based Searches</h4>
                <ul>
                    <li><strong>File Name:</strong> Search by exact or partial file names</li>
                    <li><strong>Tags:</strong> Find models with specific tags</li>
                    <li><strong>Description:</strong> Search within model descriptions and notes</li>
                    <li><strong>Comments:</strong> Find files with user-added comments</li>
                </ul>

                <h4>Attribute-Based Searches</h4>
                <ul>
                    <li><strong>File Type:</strong> Filter by specific formats (STL, OBJ, etc.)</li>
                    <li><strong>File Size:</strong> Find models within size ranges</li>
                    <li><strong>Date Range:</strong> Search by import or modification dates</li>
                    <li><strong>Material Type:</strong> Find models using specific wood species</li>
                    <li><strong>Complexity Level:</strong> Filter by polygon count or detail level</li>
                </ul>

                <h4>Visual Searches</h4>
                <ul>
                    <li><strong>Color Matching:</strong> Find models with similar colors or materials</li>
                    <li><strong>Shape Similarity:</strong> Search for models with similar geometry</li>
                    <li><strong>Thumbnail Visual Search:</strong> Upload an image to find similar models</li>
                </ul>

                <h3>Search Combinations</h3>
                <p>You can combine multiple search criteria for precise results:</p>

                <div class="search-example">
                    Complex search example:<br>
                    Find all "chair" models that are:<br>
                    • Made from "oak" material<br>
                    • Imported in 2024<br>
                    • Tagged as "dining room"<br>
                    • Smaller than 50 MB<br>
                    • STL format
                </div>

                <div class="workflow-step">
                    <h4>🔍 How to Use Advanced Search</h4>
                    <ol>
                        <li>Click the "Advanced Search" button in the Model Library panel</li>
                        <li>Enter your search criteria in the appropriate fields</li>
                        <li>Set any date ranges or size limits if needed</li>
                        <li>Choose whether to match "All" or "Any" of your criteria</li>
                        <li>Click "Search" to execute the query</li>
                        <li>Review results and refine if necessary</li>
                    </ol>
                </div>

                <h3>Saved Searches</h3>
                <p>For frequently used search criteria, save your searches for quick access:</p>
                <ol>
                    <li>Set up your search criteria in the advanced search dialog</li>
                    <li>Click "Save Search" and enter a descriptive name</li>
                    <li>Your saved searches appear in a dropdown menu</li>
                    <li>Click any saved search to instantly apply those criteria</li>
                </ol>

                <div class="tip">
                    <strong>💡 Search Efficiency Tip:</strong> Create saved searches for your most common queries. For example, "Recent Imports", "Large Models", "Oak Furniture", or "Hardware Components". This saves time and ensures consistent search results.
                </div>
            </div>

            <div class="section" id="project-association">
                <h2>Project Association</h2>

                <p>One of Digital Workshop's most powerful features is the ability to associate models with specific projects. This creates a logical connection between your design files and your actual woodworking projects, making it easy to see what materials and components are needed for each job.</p>

                <h3>Automatic Project Association</h3>
                <p>When you import models into an active project, Digital Workshop automatically links them:</p>

                <div class="workflow-step">
                    <h4>🔗 How Project Association Works</h4>
                    <ol>
                        <li>Open or create a project in Digital Workshop</li>
                        <li>Import 3D models while the project is active</li>
                        <li>Models are automatically tagged with the project name</li>
                        <li>All project-associated models appear in the project view</li>
                        <li>You can filter the library to show only project-related models</li>
                    </ol>
                </div>

                <h3>Manual Project Linking</h3>
                <p>You can also associate existing models with projects:</p>
                <ol>
                    <li>Select one or more models in the library</li>
                    <li>Right-click and choose "Associate with Project"</li>
                    <li>Select the project from the dropdown menu</li>
                    <li>Optionally add project-specific notes or tags</li>
                    <li>Click "Link" to complete the association</li>
                </ol>

                <h3>Project-Based Library Views</h3>
                <p>The Model Library offers several ways to view project-related models:</p>

                <h4>Project Filter</h4>
                <ul>
                    <li><strong>Current Project Only:</strong> Shows models associated with the currently active project</li>
                    <li><strong>All Projects:</strong> Shows models from all projects with project indicators</li>
                    <li><strong>No Project:</strong> Shows only unassociated models</li>
                    <li><strong>Project Comparison:</strong> Side-by-side view of models from different projects</li>
                </ul>

                <h4>Project Statistics</h4>
                <p>Digital Workshop provides detailed statistics for project-associated models:</p>
                <ul>
                    <li><strong>Total Models:</strong> Number of components in the project</li>
                    <li><strong>Material Types:</strong> Breakdown of wood species and other materials</li>
                    <li><strong>File Sizes:</strong> Total storage space required</li>
                    <li><strong>Complexity Analysis:</strong> Average polygon count and detail level</li>
                </ul>

                <div class="note">
                    <strong>📋 Project Organization Tip:</strong> Create a dedicated project folder structure in your Model Library. This makes it easy to see all components for a project at a glance and helps when working on multiple projects simultaneously.
                </div>

                <div class="image-placeholder">
                    [Image: project-association-interface.png]
                    <br>Figure 4: Interface showing project-associated models and filtering options
                </div>
            </div>

            <div class="section" id="bulk-operations">
                <h2>Bulk Operations</h2>

                <p>When working with large numbers of models, Digital Workshop provides tools for performing operations on multiple files simultaneously. This is like having helpers in your workshop who can carry multiple pieces of lumber or organize several tools at once - much more efficient than handling each item individually.</p>

                <h3>Multi-Selection Methods</h3>
                <p>Before performing bulk operations, you need to select multiple models:</p>

                <h4>Selection Techniques</h4>
                <ul>
                    <li><strong>Click and Drag:</strong> Draw a selection box around multiple items</li>
                    <li><strong>Ctrl-Click:</strong> Add individual items to your selection</li>
                    <li><strong>Shift-Click:</strong> Select a range of items between two clicks</li>
                    <li><strong>Select All:</strong> Use Ctrl+A to select everything in the current view</li>
                    <li><strong>Filter and Select:</strong> Apply filters first, then select all visible items</li>
                </ul>

                <h3>Available Bulk Operations</h3>

                <h4>File Operations</h4>
                <ul>
                    <li><strong>Move to Folder:</strong> Relocate multiple files to a new location</li>
                    <li><strong>Copy to Folder:</strong> Duplicate files in a new location</li>
                    <li><strong>Delete:</strong> Remove multiple files with confirmation</li>
                    <li><strong>Rename:</strong> Apply naming patterns to multiple files</li>
                </ul>

                <h4>Metadata Operations</h4>
                <ul>
                    <li><strong>Add Tags:</strong> Apply the same tags to multiple models</li>
                    <li><strong>Remove Tags:</strong> Delete specific tags from selected items</li>
                    <li><strong>Update Descriptions:</strong> Modify descriptions for multiple models</li>
                    <li><strong>Set Materials:</strong> Apply wood species or finishes to selected items</li>
                </ul>

                <h4>Project Operations</h4>
                <ul>
                    <li><strong>Associate with Project:</strong> Link multiple models to the same project</li>
                    <li><strong>Export for Project:</strong> Copy selected models to a project folder</li>
                    <li><strong>Generate Cut Lists:</strong> Create material lists from selected components</li>
                    <li><strong>Calculate Costs:</strong> Estimate material costs for selected items</li>
                </ul>

                <div class="workflow-step">
                    <h4>⚡ Performing Bulk Operations</h4>
                    <ol>
                        <li>Select multiple models using any of the selection methods</li>
                        <li>Right-click on any selected item to open the context menu</li>
                        <li>Choose the bulk operation you want to perform</li>
                        <li>Review the operation details and affected files</li>
                        <li>Confirm the action (bulk operations cannot be undone)</li>
                        <li>Monitor progress if the operation takes time</li>
                    </ol>
                </div>

                <div class="warning">
                    <strong>⚠️ Bulk Operation Caution:</strong> Bulk operations affect multiple files and cannot be easily undone. Always verify your selection before proceeding, and consider creating a backup of your library before large bulk operations.
                </div>
            </div>

            <div class="section" id="file-maintenance">
                <h2>File Maintenance and Cleanup</h2>

                <p>Just as your physical workshop needs regular cleaning and maintenance, your Digital Workshop library benefits from periodic attention. Regular maintenance keeps your library organized, frees up disk space, and ensures optimal performance.</p>

                <h3>Duplicate File Management</h3>
                <p>Over time, you may accumulate duplicate files in your library. Digital Workshop includes tools to identify and manage duplicates:</p>

                <h4>Finding Duplicates</h4>
                <ol>
                    <li>Go to <strong>Tools → Library Maintenance → Find Duplicates</strong></li>
                    <li>Choose search criteria (file name, content, or both)</li>
                    <li>Set similarity thresholds for content comparison</li>
                    <li>Review the list of potential duplicates</li>
                    <li>Select duplicates to remove or merge</li>
                </ol>

                <h4>Duplicate Resolution Options</h4>
                <ul>
                    <li><strong>Keep Oldest:</strong> Retain the first imported version</li>
                    <li><strong>Keep Newest:</strong> Keep the most recently modified version</li>
                    <li><strong>Keep Largest:</strong> Retain the highest quality version</li>
                    <li><strong>Manual Review:</strong> Choose which version to keep for each duplicate</li>
                    <li><strong>Merge Information:</strong> Combine metadata from multiple versions</li>
                </ul>

                <h3>Orphaned File Detection</h3>
                <p>Some files in your library may no longer be associated with any project or may have broken references:</p>

                <h4>Orphan Cleanup Process</h4>
                <ol>
                    <li>Run <strong>Tools → Library Maintenance → Find Orphans</strong></li>
                    <li>Review the list of orphaned files</li>
                    <li>Decide whether to keep, archive, or delete each file</li>
                    <li>Optionally associate orphans with appropriate projects</li>
                    <li>Execute the cleanup operation</li>
                </ol>

                <h3>Storage Optimization</h3>
                <p>Digital Workshop can optimize your library to reduce storage requirements:</p>

                <h4>Optimization Options</h4>
                <ul>
                    <li><strong>Compress Thumbnails:</strong> Reduce thumbnail file sizes while maintaining quality</li>
                    <li><strong>Optimize Geometry:</strong> Simplify complex models to reduce file size</li>
                    <li><strong>Remove Unused Materials:</strong> Delete material files no longer referenced</li>
                    <li><strong>Consolidate Project Files:</strong> Move project-associated files to project folders</li>
                </ul>

                <h3>Backup and Archive</h3>
                <p>Protect your library with regular backups:</p>

                <h4>Backup Strategies</h4>
                <ul>
                    <li><strong>Full Library Backup:</strong> Complete copy of all files and metadata</li>
                    <li><strong>Project-Specific Backup:</strong> Backup only files associated with specific projects</li>
                    <li><strong>Incremental Backup:</strong> Only backup files that have changed since the last backup</li>
                    <li><strong>Archive Old Projects:</strong> Move completed projects to long-term storage</li>
                </ul>

                <div class="tip">
                    <strong>💡 Maintenance Schedule:</strong> Perform library maintenance monthly for active users, or quarterly for occasional users. Set a recurring reminder in your calendar, just like scheduling workshop cleaning or tool maintenance.
                </div>

                <h3>Library Health Monitoring</h3>
                <p>Digital Workshop provides diagnostic tools to monitor library health:</p>
                <ul>
                    <li><strong>File Integrity Check:</strong> Verify that all files can be opened and are not corrupted</li>
                    <li><strong>Metadata Validation:</strong> Ensure all tags, descriptions, and associations are valid</li>
                    <li><strong>Performance Analysis:</strong> Identify slow-loading or problematic files</li>
                    <li><strong>Storage Usage Report:</strong> Show detailed breakdown of disk space usage</li>
                </ul>

                <div class="image-placeholder">
                    [Image: maintenance-tools-interface.png]
                    <br>Figure 5: Library maintenance and optimization tools
                </div>

                <h3>Best Practices Summary</h3>
                <div class="note">
                    <strong>📋 Model Management Best Practices:</strong>
                    <ul>
                        <li>Create a logical folder structure before importing large numbers of files</li>
                        <li>Use descriptive file names that include project name and component type</li>
                        <li>Tag models with relevant information (material, project, function)</li>
                        <li>Associate models with specific projects for easy organization</li>
                        <li>Perform regular maintenance to remove duplicates and orphaned files</li>
                        <li>Back up your library regularly, especially before major changes</li>
                        <li>Use bulk operations efficiently when working with multiple files</li>
                        <li>Keep your library organized from the start - it's easier than reorganizing later</li>
                    </ul>
                </div>

                <p>Remember that good model management is an investment in your future productivity. Just as a well-organized workshop makes you more efficient and less frustrated, a well-organized digital library saves time and reduces stress when working on projects. The time you spend organizing your models now will be repaid many times over as your library grows and your projects become more complex.</p>
            </div>

            <div style="text-align: center; margin-top: 50px;">
                <a href="index.html" class="btn back-link">← Back to Main Index</a>
                <a href="interface-guide.html" class="btn">← Previous: Interface Guide</a>
                <a href="3d-viewer.html" class="btn">Next: 3D Model Viewer →</a>
            </div>
        </div>
    </div>
</body>
</html>