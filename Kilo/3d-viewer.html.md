<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3D Model Viewer - Digital Workshop User Manual</title>
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
        .view-mode-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .view-mode-card {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            transition: transform 0.2s ease;
        }
        .view-mode-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .view-mode-icon {
            font-size: 2.5rem;
            margin-bottom: 15px;
        }
        .camera-controls {
            background: #e9ecef;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }
        .control-group {
            margin: 15px 0;
        }
        .control-group label {
            display: block;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .control-group input[type="range"] {
            width: 100%;
            margin: 5px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>3D Model Viewer</h1>
            <p>Rendering Modes, Camera Controls, and Material Application</p>
        </div>

        <div class="content">
            <div class="toc">
                <h3>📋 Quick Navigation</h3>
                <ul>
                    <li><a href="#viewer-overview">Viewer Overview</a></li>
                    <li><a href="#rendering-modes">Rendering Modes</a></li>
                    <li><a href="#camera-controls">Camera Controls</a></li>
                    <li><a href="#view-navigations">View Navigation</a></li>
                    <li><a href="#measurement-tools">Measurement Tools</a></li>
                    <li><a href="#view-organization">View Organization</a></li>
                    <li><a href="#performance-optimization">Performance Optimization</a></li>
                    <li><a href="#advanced-features">Advanced Features</a></li>
                </ul>
            </div>

            <div class="section">
                <p>The 3D Model Viewer in Digital Workshop is your digital equivalent of examining a piece of furniture in your workshop under good lighting. Just as you might walk around a completed chair to check proportions, examine joinery details, and assess the overall quality, the 3D viewer allows you to inspect your digital models from every angle with realistic materials and lighting.</p>

                <p>Whether you're checking the fit of components, evaluating the visual impact of different wood finishes, or simply ensuring your design will work as intended, the 3D viewer provides the tools you need to see your projects clearly. Think of it as having perfect workshop lighting that never changes and the ability to instantly see your piece from any angle without moving it.</p>
            </div>

            <div class="section" id="viewer-overview">
                <h2>Viewer Overview</h2>

                <p>The 3D Model Viewer occupies the central area of Digital Workshop's interface, serving as your primary workspace for examining and evaluating 3D models. Like the main workbench in your workshop, this is where the most important visual inspection and quality checking happens.</p>

                <div class="image-placeholder">
                    [Image: 3d-viewer-interface.png]
                    <br>Figure 1: Complete 3D viewer interface showing all control elements
                </div>

                <h3>Main Viewer Components</h3>

                <h4>Central Viewing Area</h4>
                <p>The large central space where your 3D models are displayed:</p>
                <ul>
                    <li><strong>Real-time Rendering:</strong> Models are displayed with realistic lighting and shadows</li>
                    <li><strong>Material Preview:</strong> Wood textures and finishes are applied in real-time</li>
                    <li><strong>Interactive Navigation:</strong> Click and drag to rotate, scroll to zoom</li>
                    <li><strong>Multiple Objects:</strong> View complete assemblies or individual components</li>
                </ul>

                <h4>Viewer Controls</h4>
                <p>Located around the viewing area, these controls adjust how you see your models:</p>
                <ul>
                    <li><strong>Rendering Mode Buttons:</strong> Switch between solid, wireframe, and other views</li>
                    <li><strong>Zoom Controls:</strong> Precise zoom in/out and fit-to-view options</li>
                    <li><strong>View Presets:</strong> Standard views (front, top, side, isometric)</li>
                    <li><strong>Camera Tools:</strong> Move, orbit, and focus on specific areas</li>
                </ul>

                <h4>Information Display</h4>
                <p>Real-time information about your current view:</p>
                <ul>
                    <li><strong>Zoom Level:</strong> Current magnification percentage</li>
                    <li><strong>Camera Position:</strong> 3D coordinates of current view point</li>
                    <li><strong>Object Statistics:</strong> Number of polygons, file size, materials used</li>
                    <li><strong>Performance Metrics:</strong> Frame rate and rendering speed</li>
                </ul>

                <h3>Viewer Coordinate System</h3>
                <p>Digital Workshop uses a standard woodworking coordinate system that matches real-world conventions:</p>
                
                <ul>
                    <li><strong>X-Axis:</strong> Left to right (width)</li>
                    <li><strong>Y-Axis:</strong> Front to back (depth)</li>
                    <li><strong>Z-Axis:</strong> Bottom to top (height)</li>
                </ul>

                <div class="note">
                    <strong>📐 Coordinate System Tip:</strong> This coordinate system matches traditional woodworking measurements where width (X) is typically the longest dimension, depth (Y) is front-to-back, and height (Z) is vertical. This consistency makes it easier to translate digital designs to physical builds.
                </div>
            </div>

            <div class="section" id="rendering-modes">
                <h2>Rendering Modes</h2>

                <p>Digital Workshop offers several rendering modes, each optimized for different types of inspection and analysis. Think of these modes like different types of workshop lighting - some provide detailed views of construction, others focus on proportions, and some help identify potential issues.</p>

                <div class="view-mode-grid">
                    <div class="view-mode-card">
                        <div class="view-mode-icon">🎯</div>
                        <h4>Solid Mode</h4>
                        <p>Realistic rendering with materials, lighting, and shadows. Best for final design review and client presentations.</p>
                    </div>
                    <div class="view-mode-card">
                        <div class="view-mode-icon">📐</div>
                        <h4>Wireframe Mode</h4>
                        <p>Shows only the edges and geometry. Perfect for checking joinery and complex internal structures.</p>
                    </div>
                    <div class="view-mode-card">
                        <div class="view-mode-icon">👁️</div>
                        <h4>Hidden Line</h4>
                        <p>Solid objects with hidden edges removed. Good for technical drawings and manufacturing documentation.</p>
                    </div>
                    <div class="view-mode-card">
                        <div class="view-mode-icon">🎨</div>
                        <h4>Material Preview</h4>
                        <p>Enhanced material display with detailed wood grain and surface textures. Ideal for finish planning.</p>
                    </div>
                </div>

                <h3>Solid Rendering Mode</h3>
                <p>This is the default mode and provides the most realistic view of your models:</p>

                <div class="workflow-step">
                    <h4>🎯 Using Solid Mode Effectively</h4>
                    <ul>
                        <li><strong>Realistic Materials:</strong> Wood species and finishes are applied automatically</li>
                        <li><strong>Lighting Effects:</strong> Realistic shadows and highlights help assess proportions</li>
                        <li><strong>Surface Quality:</strong> See how the final piece will look</li>
                        <li><strong>Color Accuracy:</strong> Different wood species display their natural colors</li>
                        <li><strong>Grain Patterns:</strong> Realistic wood grain patterns help with aesthetic decisions</li>
                    </ul>
                </div>

                <p>Best use cases for Solid Mode:</p>
                <ul>
                    <li>Final design review before building</li>
                    <li>Client presentations and approvals</li>
                    <li>Aesthetic evaluation of different wood combinations</li>
                    <li>Checking overall proportions and visual balance</li>
                </ul>

                <h3>Wireframe Mode</h3>
                <p>Wireframe mode strips away all surface details to show only the underlying geometry:</p>

                <div class="workflow-step">
                    <h4>📐 When to Use Wireframe Mode</h4>
                    <ul>
                        <li><strong>Joinery Inspection:</strong> See how pieces connect and fit together</li>
                        <li><strong>Complex Geometry:</strong> Examine intricate shapes and curves</li>
                        <li><strong>Assembly Verification:</strong> Check that all components align properly</li>
                        <li><strong>Construction Planning:</strong> Visualize how the piece will be assembled</li>
                        <li><strong>Problem Diagnosis:</strong> Identify geometry issues or gaps</li>
                    </ul>
                </div>

                <div class="tip">
                    <strong>💡 Wireframe Tip:</strong> Switch to wireframe mode when you need to see through objects or examine internal structures that would be hidden in solid mode. This is like being able to see through the wood to check joinery fit.
                </div>

                <h3>Hidden Line Mode</h3>
                <p>Hidden line mode shows solid objects but removes edges that would be hidden from the current viewpoint:</p>
                
                <ul>
                    <li><strong>Clean Technical Views:</strong> Perfect for creating clean documentation</li>
                    <li><strong>Manufacturing Drawings:</strong> Clear views of all visible edges</li>
                    <li><strong>Assembly Instructions:</strong> Show how components fit together</li>
                    <li><strong>Presentation Graphics:</strong> Professional-looking technical illustrations</li>
                </ul>

                <h3>Material Preview Mode</h3>
                <p>Enhanced material display with detailed textures and surface properties:</p>

                <ul>
                    <li><strong>Detailed Wood Grain:</strong> See realistic grain patterns and variations</li>
                    <li><strong>Surface Texture:</strong> Feel the difference between smooth and rough finishes</li>
                    <li><strong>Color Variations:</strong> Natural color differences within wood species</li>
                    <li><strong>Finish Simulation:</strong> Preview different stains, varnishes, and paints</li>
                </ul>

                <div class="image-placeholder">
                    [Image: rendering-modes-comparison.png]
                    <br>Figure 2: Side-by-side comparison of different rendering modes
                </div>

                <h3>Switching Between Modes</h3>
                <p>Changing rendering modes is simple and immediate:</p>
                <ol>
                    <li>Look for the rendering mode buttons in the viewer toolbar</li>
                    <li>Click the desired mode (Solid, Wireframe, Hidden Line, or Material Preview)</li>
                    <li>The view updates instantly without reloading the model</li>
                    <li>Experiment with different modes to find the best view for your current task</li>
                </ol>
            </div>

            <div class="section" id="camera-controls">
                <h2>Camera Controls</h2>

                <p>Mastering the camera controls in Digital Workshop is like learning to position yourself optimally around a workpiece in your physical workshop. The right viewpoint can reveal proportions, show fit issues, or highlight design problems that might not be apparent from other angles.</p>

                <div class="camera-controls">
                    <div class="control-group">
                        <label>🖱️ Mouse Controls</label>
                        <ul>
                            <li><strong>Left Click + Drag:</strong> Orbit around the model</li>
                            <li><strong>Right Click + Drag:</strong> Pan the view</li>
                            <li><strong>Mouse Wheel:</strong> Zoom in and out</li>
                            <li><strong>Middle Click + Drag:</strong> Pan the view (alternative)</li>
                        </ul>
                    </div>
                    
                    <div class="control-group">
                        <label>⌨️ Keyboard Shortcuts</label>
                        <ul>
                            <li><strong>Space:</strong> Hold to temporarily pan view</li>
                            <li><strong>Home:</strong> Return to default camera position</li>
                            <li><strong>Ctrl + 0:</strong> Fit model to view window</li>
                            <li><strong>F:</strong> Focus on selected objects</li>
                        </ul>
                    </div>
                </div>

                <h3>Basic Camera Movements</h3>

                <h4>Orbiting (Rotating View)</h4>
                <p>Rotating around your model is like walking around a piece of furniture in your workshop:</p>

                <div class="workflow-step">
                    <h4>🔄 How to Orbit Effectively</h4>
                    <ol>
                        <li>Position your cursor over the model</li>
                        <li>Click and hold the left mouse button</li>
                        <li>Drag in any direction to rotate the view</li>
                        <li>Continue dragging to examine the model from all angles</li>
                        <li>Release the mouse button when you find a good view</li>
                    </ol>
                </div>

                <h4>Panning (Moving View)</h4>
                <p>Panning moves your viewpoint without changing the viewing angle:</p>

                <ul>
                    <li><strong>Right Click + Drag:</strong> Move view horizontally and vertically</li>
                    <li><strong>Middle Click + Drag:</strong> Alternative pan method</li>
                    <li><strong>Arrow Keys:</strong> Small incremental pans</li>
                    <li><strong>Shift + Arrow Keys:</strong> Larger incremental pans</li>
                </ul>

                <h4>Zooming (Magnification)</h4>
                <p>Zooming lets you examine details or see the overall design:</p>

                <ul>
                    <li><strong>Mouse Wheel:</strong> Scroll up to zoom in, down to zoom out</li>
                    <li><strong>Zoom Buttons:</strong> Plus and minus buttons in toolbar</li>
                    <li><strong>Fit to View:</strong> Automatically adjust zoom to show entire model</li>
                    <li><strong>Zoom to Selection:</strong> Focus on currently selected objects</li>
                </ul>

                <div class="tip">
                    <strong>💡 Camera Efficiency Tip:</strong> Use the "Fit to View" button (Ctrl+0) frequently when you get lost or disoriented. It's like stepping back to see the big picture when you're working on detailed joinery.
                </div>

                <h3>Advanced Camera Features</h3>

                <h4>Camera Focus</h4>
                <p>Automatically position the camera to focus on specific objects or areas:</p>

                <ul>
                    <li><strong>Focus on Selection:</strong> Press F to focus camera on selected objects</li>
                    <li><strong>Focus on Component:</strong> Double-click any object to focus on it</li>
                    <li><strong>Focus on Region:</strong> Draw a box around an area to focus there</li>
                    <li><strong>Return to Previous:</strong> Go back to previous camera position</li>
                </ul>

                <h4>Camera Animation</h4>
                <p>Smooth camera movements for professional presentations:</p>

                <ul>
                    <li><strong>Smooth Transitions:</strong> Camera moves smoothly between positions</li>
                    <li><strong>Animation Speed:</strong> Adjust how fast camera movements occur</li>
                    <li><strong>Path Recording:</strong> Record camera movements for presentations</li>
                    <li><strong>Keyframe Animation:</strong> Create smooth camera sequences</li>
                </ul>

                <div class="image-placeholder">
                    [Image: camera-control-diagram.png]
                    <br>Figure 3: Visual guide to camera controls and movements
                </div>
            </div>

            <div class="section" id="view-navigations">
                <h2>View Navigation and Presets</h2>

                <p>Digital Workshop includes predefined view angles that match standard woodworking perspectives. These preset views are like having designated inspection stations in your workshop - specific locations where you can examine your work from traditional woodworking viewpoints.</p>

                <h3>Standard View Presets</h3>
                <p>Quick access to the most commonly used viewing angles:</p>

                <h4>Primary Views</h4>
                <div class="view-mode-grid">
                    <div class="view-mode-card">
                        <div class="view-mode-icon">👁️</div>
                        <h4>Front View</h4>
                        <p>Looking at the face of the piece. Shows front elevation and overall proportions.</p>
                    </div>
                    <div class="view-mode-card">
                        <div class="view-mode-icon">👁️</div>
                        <h4>Side View</h4>
                        <p>Looking at the side profile. Shows depth relationships and side proportions.</p>
                    </div>
                    <div class="view-mode-card">
                        <div class="view-mode-icon">👁️</div>
                        <h4>Top View</h4>
                        <p>Looking down from above. Shows plan view and component layout.</p>
                    </div>
                    <div class="view-mode-card">
                        <div class="view-mode-icon">👁️</div>
                        <h4>Isometric View</h4>
                        <p>Combined view showing front, side, and top simultaneously. Good for overall assessment.</p>
                    </div>
                </div>

                <h3>Specialized Views</h3>

                <h4>Detail Views</h4>
                <ul>
                    <li><strong>Close-up Views:</strong> Automatic zoom to show fine details</li>
                    <li><strong>Joinery Views:</strong> Optimized angles for examining joints</li>
                    <li><strong>Component Views:</strong> Focus on individual parts</li>
                    <li><strong>Assembly Views:</strong> Show how parts fit together</li>
                </ul>

                <h4>Working Views</h4>
                <ul>
                    <li><strong>Workshop View:</strong> Angle as if standing in your workshop</li>
                    <li><strong>Table View:</strong> Looking down as if on a workbench</li>
                    <li><strong>Floor View:</strong> Looking up from floor level</li>
                    <li><strong>Customer View:</strong> Angle optimized for client presentation</li>
                </ul>

                <div class="workflow-step">
                    <h4>🎯 Using View Presets Effectively</h4>
                    <ol>
                        <li>Click the view preset buttons in the toolbar</li>
                        <li>Try different preset angles to find the best view for your current task</li>
                        <li>Use multiple presets in sequence to examine different aspects</li>
                        <li>Combine presets with different rendering modes for comprehensive analysis</li>
                        <li>Save your own custom presets for project-specific views</li>
                    </ol>
                </div>

                <h3>Creating Custom Views</h3>
                <p>Save your own frequently used viewing angles:</p>

                <ol>
                    <li>Position the camera at your desired angle and zoom level</li>
                    <li>Go to <strong>View → Save Custom View</strong></li>
                    <li>Enter a descriptive name (e.g., "Dovetail Detail", "Cabinet Interior")</li>
                    <li>Your custom view appears in the preset menu</li>
                    <li>Click the saved view name to return to that camera position anytime</li>
                </ol>

                <div class="note">
                    <strong>📋 Custom View Tip:</strong> Create custom views for complex assemblies or frequently examined details. This saves time and ensures consistent analysis angles across different projects.
                </div>
            </div>

            <div class="section" id="measurement-tools">
                <h2>Measurement and Analysis Tools</h2>

                <p>The 3D viewer includes precise measurement tools that serve as your digital calipers and measuring tapes. Just as you would measure components in your workshop to ensure proper fit, these tools help you verify dimensions, check clearances, and validate your digital designs.</p>

                <h3>Distance Measurement</h3>
                <p>Measure straight-line distances between any two points:</p>

                <div class="workflow-step">
                    <h4>📏 How to Measure Distances</h4>
                    <ol>
                        <li>Click the "Measure Distance" tool in the viewer toolbar</li>
                        <li>Click the first point you want to measure from</li>
                        <li>Click the second point you want to measure to</li>
                        <li>A measurement line appears showing the distance</li>
                        <li>The measurement is displayed in your preferred units (inches or millimeters)</li>
                    </ol>
                </div>

                <h3>Angle Measurement</h3>
                <p>Measure angles between surfaces or features:</p>

                <ul>
                    <li><strong>Surface Angles:</strong> Measure the angle between two surfaces</li>
                    <li><strong>Feature Angles:</strong> Measure angles of specific design elements</li>
                    <li><strong>Compound Angles:</strong> Measure complex angles in 3D space</li>
                    <li><strong>Reference Angles:</strong> Compare to standard angles (90°, 45°, etc.)</li>
                </ul>

                <h3>Area and Volume Calculations</h3>
                <p>Calculate surface areas and internal volumes:</p>

                <ul>
                    <li><strong>Surface Area:</strong> Total area of exposed surfaces</li>
                    <li><strong>Cross-sectional Area:</strong> Area of specific cuts or sections</li>
                    <li><strong>Internal Volume:</strong> Volume enclosed by the model</li>
                    <li><strong>Material Volume:</strong> Volume of material needed to create the piece</li>
                </ul>

                <h3>Clearance Analysis</h3>
                <p>Check for proper clearances and fit:</p>

                <ul>
                    <li><strong>Minimum Clearance:</strong> Smallest distance between components</li>
                    <li><strong>Clearance Verification:</strong> Check against design requirements</li>
                    <li><strong>Fit Analysis:</strong> Determine if parts will fit together properly</li>
                    <li><strong>Movement Clearance:</strong> Ensure moving parts have adequate space</li>
                </ul>

                <div class="tip">
                    <strong>💡 Measurement Tip:</strong> Use measurement tools throughout your design process, not just at the end. Regular measurements help catch errors early and ensure your digital design matches your intended physical dimensions.
                </div>

                <div class="image-placeholder">
                    [Image: measurement-tools-interface.png]
                    <br>Figure 4: Measurement tools in action showing various measurement types
                </div>
            </div>

            <div class="section" id="view-organization">
                <h2>View Organization and Comparison</h2>

                <p>For complex projects, Digital Workshop provides tools to organize and compare different views. This is like having multiple workbenches or inspection stations where you can examine different aspects of your work simultaneously.</p>

                <h3>Multiple View Windows</h3>
                <p>Open multiple viewer windows to compare different aspects:</p>

                <ul>
                    <li><strong>Side-by-Side Views:</strong> Compare different angles simultaneously</li>
                    <li><strong>Before/After Comparison:</strong> See design changes in progress</li>
                    <li><strong>Material Comparison:</strong> Compare different wood species or finishes</li>
                    <li><strong>Version Comparison:</strong> Compare different design iterations</li>
                </ul>

                <h3>View Snapshots</h3>
                <p>Capture and save specific viewing states:</p>

                <ol>
                    <li>Position your model and set the viewing parameters</li>
                    <li>Click "Snapshot" to capture the current view</li>
                    <li>Name the snapshot descriptively</li>
                    <li>Return to the saved snapshot anytime with a single click</li>
                </ol>

                <div class="note">
                    <strong>📷 Snapshot Organization:</strong> Create snapshots at key stages of your design process. This helps you track your progress and provides reference points if you need to backtrack or try different approaches.
                </div>
            </div>

            <div class="section" id="performance-optimization">
                <h2>Performance Optimization</h2>

                <p>Digital Workshop's 3D viewer is optimized for smooth performance, but you can further optimize it based on your computer's capabilities and the complexity of your models. This is similar to adjusting lighting and workspace setup in your physical workshop for optimal visibility and efficiency.</p>

                <h3>Performance Settings</h3>
                <p>Adjust viewer performance based on your needs:</p>

                <h4>Quality Settings</h4>
                <ul>
                    <li><strong>High Quality:</strong> Best visual quality for detailed work (requires powerful graphics)</li>
                    <li><strong>Balanced:</strong> Good balance of quality and performance (recommended for most users)</li>
                    <li><strong>Performance:</strong> Optimized for speed, good for large models</li>
                    <li><strong>Custom:</strong> Fine-tune individual settings</li>
                </ul>

                <h4>Rendering Options</h4>
                <ul>
                    <li><strong>Anti-aliasing:</strong> Smooth edges for cleaner appearance</li>
                    <li><strong>Shadow Quality:</strong> Realistic shadows with performance cost</li>
                    <li><strong>Texture Resolution:</strong> Balance between detail and speed</li>
                    <li><strong>Reflection Quality:</strong> Surface reflections with performance impact</li>
                </ul>

                <h3>Model Optimization</h3>
                <p>Optimize individual models for better performance:</p>

                <ul>
                    <li><strong>Polygon Reduction:</strong> Simplify complex geometry while maintaining appearance</li>
                    <li><strong>LOD (Level of Detail):</strong> Automatically adjust detail based on zoom level</li>
                    <li><strong>Texture Optimization:</strong> Compress textures to reduce memory usage</li>
                    <li><strong>Material Simplification:</strong> Reduce material complexity for better performance</li>
                </ul>

                <div class="warning">
                    <strong>⚠️ Performance Caution:</strong> While optimization improves performance, excessive simplification can affect the accuracy of your visual inspection. Use high quality settings when precision is critical, and optimize for speed only when reviewing large assemblies or during initial design phases.
                </div>
            </div>

            <div class="section" id="advanced-features">
                <h2>Advanced Viewer Features</h2>

                <p>Beyond basic viewing and navigation, Digital Workshop's 3D viewer includes advanced features that enhance your ability to analyze and understand complex designs. These features are like having specialized inspection tools and measurement equipment in your digital workshop.</p>

                <h3>Section Views</h3>
                <p>Create cross-sectional views to examine interior details:</p>

                <ul>
                    <li><strong>Cut Planes:</strong> Slice through models to see internal structure</li>
                    <li><strong>Adjustable Cuts:</strong> Move cut planes to examine different sections</li>
                    <li><strong>Multiple Cuts:</strong> Create several section views simultaneously</li>
                    <li><strong>Section Analysis:</strong> Measure features within cut sections</li>
                </ul>

                <h3>Exploded Views</h3>
                <p>Temporarily separate components to see how they assemble:</p>

                <ul>
                    <li><strong>Automatic Explosion:</strong> System separates components intelligently</li>
                    <li><strong>Manual Control:</strong> Adjust explosion amount for clarity</li>
                    <li><strong>Component Isolation:</strong> Move specific components for closer examination</li>
                    <li><strong>Assembly Animation:</strong> Watch components come together</li>
                </ul>

                <h3>Virtual Reality Preview</h3>
                <p>Experience your designs in virtual reality:</p>

                <ul>
                    <li><strong>VR Headset Support:</strong> Compatible with major VR systems</li>
                    <li><strong>True Scale:</strong> Experience designs at actual physical size</li>
                    <li><strong>Immersive Review:</strong> Walk around and examine designs naturally</li>
                    <li><strong>Client Presentations:</strong> Show designs in an engaging format</li>
                </ul>

                <div class="tip">
                    <strong>💡 Advanced Feature Tip:</strong> Start with basic viewer features and gradually explore advanced capabilities. Like learning to use new workshop tools, mastering these features takes practice but provides powerful new capabilities for design analysis and presentation.
                </div>

                <h3>Best Practices for Effective 3D Viewing</h3>

                <div class="note">
                    <strong>📋 3D Viewer Best Practices:</strong>
                    <ul>
                        <li>Use solid rendering mode for final design review and client presentations</li>
                        <li>Switch to wireframe mode for joinery inspection and technical analysis</li>
                        <li>Take advantage of multiple viewing angles to catch design issues</li>
                        <li>Use measurement tools regularly to verify dimensions</li>
                        <li>Save custom views for frequently examined details</li>
                        <li>Optimize performance settings based on your computer's capabilities</li>
                        <li>Create snapshots at key design milestones for reference</li>
                        <li>Use section views to examine internal structures and complex assemblies</li>
                    </ul>
                </div>

                <p>The 3D Model Viewer is your window into the digital world of your woodworking projects. Like any powerful tool, it takes practice to use effectively, but once mastered, it becomes an invaluable part of your design and planning process. Whether you're verifying joinery, evaluating proportions, or presenting designs to clients, the 3D viewer provides the clarity and precision you need to create exceptional furniture and cabinetry.</p>

                <p>Remember that the goal of the 3D viewer is to help you create better physical pieces. Use it to catch problems before they become expensive mistakes in your workshop, to explore design alternatives quickly, and to communicate your vision clearly to clients and collaborators. The time you spend learning to use the viewer effectively will be repaid many times over in improved design quality and reduced building time.</p>
            </div>

            <div style="text-align: center; margin-top: 50px;">
                <a href="index.html" class="btn back-link">← Back to Main Index</a>
                <a href="model-management.html" class="btn">← Previous: Model Management</a>
                <a href="materials.html" class="btn">Next: Materials & Textures →</a>
            </div>
        </div>
    </div>
</body>
</html>