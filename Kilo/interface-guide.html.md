<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Interface Guide - Digital Workshop User Manual</title>
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
        .interface-layout {
            display: grid;
            grid-template-columns: 1fr 2fr 1fr;
            gap: 20px;
            margin: 30px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        .panel-description {
            background: white;
            padding: 15px;
            border-radius: 6px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .center-panel {
            background: white;
            padding: 15px;
            border-radius: 6px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }
        .keyboard-shortcut {
            background: #e9ecef;
            border: 1px solid #ced4da;
            border-radius: 4px;
            padding: 2px 6px;
            font-family: monospace;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Interface Guide</h1>
            <p>Main Window Layout, Panels, and Workspace Customization</p>
        </div>

        <div class="content">
            <div class="toc">
                <h3>📋 Quick Navigation</h3>
                <ul>
                    <li><a href="#main-layout">Main Window Layout</a></li>
                    <li><a href="#panel-overview">Panel Overview</a></li>
                    <li><a href="#customization">Customizing Your Workspace</a></li>
                    <li><a href="#docking-system">Dockable Panels System</a></li>
                    <li><a href="#menu-navigation">Menu System</a></li>
                    <li><a href="#keyboard-shortcuts">Keyboard Shortcuts</a></li>
                    <li><a href="#workspace-presets">Workspace Presets</a></li>
                </ul>
            </div>

            <div class="section">
                <p>Digital Workshop's interface is designed like a well-organized workbench - everything has its place and purpose, making your workflow efficient and enjoyable. Whether you're importing 3D models, planning material cuts, or analyzing G-code, the interface adapts to support your current task while keeping essential tools always within reach.</p>

                <p>Think of the interface as your digital workshop layout. Just as you might arrange your workbench with frequently used tools nearby and storage for materials, Digital Workshop allows you to arrange panels and tools according to how you work best. The key is understanding what each area does and how to customize it for your specific projects.</p>
            </div>

            <div class="section" id="main-layout">
                <h2>Main Window Layout</h2>
                
                <p>The Digital Workshop main window is divided into logical sections that mirror the natural flow of woodworking projects. Imagine your physical workshop: you have a workbench (main viewing area), tool storage (side panels), and material storage (project panels). The digital interface follows this same intuitive layout.</p>

                <div class="image-placeholder">
                    [Image: main-window-layout.png]
                    <br>Figure 1: Complete interface layout showing all major components
                </div>

                <h3>Window Components Overview</h3>
                <div class="interface-layout">
                    <div class="panel-description">
                        <h4>Left Side Panel</h4>
                        <p><strong>Model Library & Project Manager</strong></p>
                        <ul>
                            <li>3D model imports</li>
                            <li>Project organization</li>
                            <li>File browser</li>
                            <li>Recent files</li>
                        </ul>
                    </div>
                    
                    <div class="center-panel">
                        <h4>Central Viewing Area</h4>
                        <p><strong>3D Viewer & Main Workspace</strong></p>
                        <ul style="text-align: left;">
                            <li>3D model display</li>
                            <li>Material preview</li>
                            <li>G-code visualization</li>
                            <li>Project overview</li>
                        </ul>
                    </div>
                    
                    <div class="panel-description">
                        <h4>Right Side Panel</h4>
                        <p><strong>Properties & Analysis Tools</strong></p>
                        <ul>
                            <li>Object properties</li>
                            <li>Material settings</li>
                            <li>AI analysis results</li>
                            <li>Cost estimation</li>
                        </ul>
                    </div>
                </div>

                <h3>Top Menu Bar</h3>
                <p>The menu bar at the top of the window provides access to all Digital Workshop features, organized logically:</p>
                
                <ul>
                    <li><strong>File:</strong> Open, save, import, and export functions</li>
                    <li><strong>Edit:</strong> Undo, redo, copy, and paste operations</li>
                    <li><strong>View:</strong> Display options, zoom, and panel visibility</li>
                    <li><strong>Tools:</strong> Specialized tools like cut list optimizer and feeds & speeds calculator</li>
                    <li><strong>Project:</strong> Project management and organization features</li>
                    <li><strong>AI:</strong> Artificial intelligence analysis and recommendations</li>
                    <li><strong>Help:</strong> Documentation, tutorials, and support resources</li>
                </ul>

                <h3>Status Bar</h3>
                <p>Located at the bottom of the window, the status bar provides important information about your current work:</p>
                
                <ul>
                    <li><strong>Current Tool:</strong> What tool or feature is currently active</li>
                    <li><strong>Zoom Level:</strong> Current magnification in the 3D viewer</li>
                    <li><strong>Coordinates:</strong> Current cursor position in 3D space</li>
                    <li><strong>Project Status:</strong> Whether your project has unsaved changes</li>
                </ul>

                <div class="note">
                    <strong>💡 Interface Tip:</strong> The status bar changes based on your current task. When working in the 3D viewer, you'll see camera position and zoom information. When editing project properties, you'll see relevant project statistics and material totals.
                </div>
            </div>

            <div class="section" id="panel-overview">
                <h2>Panel Overview</h2>

                <p>Digital Workshop uses a modular panel system where each panel focuses on a specific aspect of your project. This approach keeps your workspace uncluttered while ensuring all essential tools are available when needed. Think of each panel as a specialized workbench within your digital workshop.</p>

                <h3>Left Side Panels</h3>

                <h4>Model Library Panel</h4>
                <p>This panel serves as your digital material storage, similar to how you might store lumber and hardware in your physical workshop. It provides several key functions:</p>
                
                <ul>
                    <li><strong>File Import:</strong> Drag and drop 3D models directly into your project</li>
                    <li><strong>Organization Tools:</strong> Sort files by type, date, project, or custom tags</li>
                    <li><strong>Preview Thumbnails:</strong> See what each file contains before importing</li>
                    <li><strong>Search Function:</strong> Find specific models quickly using keywords</li>
                </ul>

                <div class="image-placeholder">
                    [Image: model-library-panel.png]
                    <br>Figure 2: Model Library panel showing organized file structure
                </div>

                <h4>Project Manager Panel</h4>
                <p>Your project organization hub, where you can manage multiple woodworking projects simultaneously. This panel helps you maintain the "Keep Organized" principle by providing:</p>
                
                <ul>
                    <li><strong>Project Overview:</strong> List of all your current and past projects</li>
                    <li><strong>File Structure:</strong> Automatic organization of project-related files</li>
                    <li><strong>Progress Tracking:</strong> Visual indicators of project completion</li>
                    <li><strong>Recent Activity:</strong> Timeline of recent work and changes</li>
                </ul>

                <h3>Right Side Panels</h3>

                <h4>Properties Panel</h4>
                <p>When you select any object in your project, the Properties panel provides detailed information and editing options. This is like having a measuring tape and calipers always ready in your workshop:</p>
                
                <ul>
                    <li><strong>Dimensions:</strong> Length, width, thickness, and precise measurements</li>
                    <li><strong>Material Information:</strong> Wood species, grain direction, finish requirements</li>
                    <li><strong>Cost Data:</strong> Material costs, labor estimates, equipment usage</li>
                    <li><strong>Manufacturing Notes:</strong> Cutting instructions, joinery details, special considerations</li>
                </ul>

                <h4>Analysis Panel</h4>
                <p>When using AI analysis features, this panel displays results and recommendations. It's like having an experienced craftsman reviewing your work and offering insights:</p>
                
                <ul>
                    <li><strong>Design Analysis:</strong> Structural integrity and design recommendations</li>
                    <li><strong>Material Suggestions:</strong> Optimal wood species and material choices</li>
                    <li><strong>Cost Optimization:</strong> Ways to reduce material waste and costs</li>
                    <li><strong>Manufacturing Advice:</strong> Suggested tools and techniques</li>
                </ul>

                <h3>Bottom Panel Area</h3>

                <h4>G-Code Preview Panel</h4>
                <p>When working with CNC machining, this panel shows the toolpath visualization. Think of it as a dry run of your machining operation, letting you see exactly what will happen before you cut any material:</p>
                
                <ul>
                    <li><strong>Toolpath Visualization:</strong> See the exact route your CNC bit will take</li>
                    <li><strong>Simulation Controls:</strong> Play, pause, and step through the machining process</li>
                    <li><strong>Feed Rate Analysis:</strong> Visual representation of cutting speed and depth</li>
                    <li><strong>Error Detection:</strong> Automatic identification of potential collision points</li>
                </ul>
            </div>

            <div class="section" id="customization">
                <h2>Customizing Your Workspace</h2>

                <p>Just as every craftsman organizes their workshop differently based on personal preferences and the type of work they do, Digital Workshop allows you to customize the interface to match your working style. The goal is to create a digital workspace that feels as natural and efficient as your physical workshop.</p>

                <h3>Panel Sizing and Positioning</h3>
                
                <p>You can resize panels by dragging their borders, just like adjusting the height of your workbench or the reach of your storage shelves. This flexibility ensures that frequently used panels can be larger while less important ones can be minimized.</p>

                <div class="tip">
                    <strong>💡 Efficiency Tip:</strong> If you frequently work with large 3D models, make the central viewing area larger. If you do a lot of project planning, expand the Project Manager panel. Customize your workspace based on what you use most often.
                </div>

                <h4>Resizing Panels</h4>
                <ol>
                    <li>Position your mouse cursor over the border between panels</li>
                    <li>The cursor will change to a double-headed arrow (↔)</li>
                    <li>Click and drag to increase or decrease panel size</li>
                    <li>Release the mouse button to set the new size</li>
                </ol>

                <h4>Moving Panels</h4>
                <p>Most panels can be repositioned to different areas of the window:</p>
                <ol>
                    <li>Click and hold the panel's title bar</li>
                    <li>Drag the panel to a new location</li>
                    <li>Look for visual indicators showing where the panel can be placed</li>
                    <li>Release the mouse button to dock the panel in the new location</li>
                </ol>

                <h3>Workspace Presets</h3>
                <p>Digital Workshop includes several pre-configured workspace layouts optimized for different types of work. These are like having specialized workstations in your workshop - one for detailed measuring, another for rough cutting, and a third for finishing work.</p>

                <h4>Available Presets</h4>
                
                <div class="panel-description" style="margin: 20px 0;">
                    <h5>📐 Design-Focused Layout</h5>
                    <p><strong>Best for:</strong> Creating and modifying 3D models</p>
                    <ul>
                        <li>Large central 3D viewer</li>
                        <li>Properties panel for detailed editing</li>
                        <li>Model library for quick access to components</li>
                        <li>Minimal distractions from other panels</li>
                    </ul>
                </div>

                <div class="panel-description" style="margin: 20px 0;">
                    <h5>🏭 Manufacturing Layout</h5>
                    <p><strong>Best for:</strong> CNC programming and G-code analysis</p>
                    <ul>
                        <li>G-code previewer in central position</li>
                        <li>Feeds & speeds calculator readily accessible</li>
                        <li>Cut list optimizer prominent</li>
                        <li>Material analysis tools visible</li>
                    </ul>
                </div>

                <div class="panel-description" style="margin: 20px 0;">
                    <h5>💰 Business Layout</h5>
                    <p><strong>Best for:</strong> Project costing and client presentations</p>
                    <ul>
                        <li>Cost estimator panel prominent</li>
                        <li>Project manager for tracking multiple jobs</li>
                        <li>Material costing tools visible</li>
                        <li>Client-ready presentation view</li>
                    </ul>
                </div>

                <h4>Switching Between Presets</h4>
                <ol>
                    <li>Click <strong>View → Workspace Layouts</strong> in the menu bar</li>
                    <li>Select the preset that matches your current work</li>
                    <li>The interface will automatically rearrange to optimize for that workflow</li>
                </ol>

                <div class="note">
                    <strong>📝 Personal Note:</strong> Don't be afraid to experiment with different layouts. Just as you might reorganize your workshop layout when taking on different types of projects, try different workspace presets to find what works best for your specific workflow.
                </div>

                <div class="image-placeholder">
                    [Image: workspace-presets-comparison.png]
                    <br>Figure 3: Comparison of different workspace layout presets
                </div>
            </div>

            <div class="section" id="docking-system">
                <h2>Dockable Panels System</h2>

                <p>The docking system in Digital Workshop works like adjustable shelving in your workshop - you can move, resize, and reorganize panels to create the perfect layout for your current project. This flexibility ensures that whether you're doing detailed design work or broad project planning, your digital workshop adapts to your needs.</p>

                <h3>Understanding Dock Zones</h3>
                <p>Digital Workshop divides the window into specific areas where panels can be docked. Think of these as designated spaces in your workshop - you wouldn't put your table saw next to your finishing supplies, and similarly, certain panels work better in specific locations.</p>

                <h4>Available Dock Zones</h4>
                <ul>
                    <li><strong>Left Side:</strong> Ideal for Model Library and Project Manager (easy access for importing and organization)</li>
                    <li><strong>Right Side:</strong> Perfect for Properties and Analysis panels (natural location for detailed information)</li>
                    <li><strong>Bottom:</strong> Excellent for G-code previewer and cut list optimizer (breadth view of manufacturing data)</li>
                    <li><strong>Top:</strong> Suitable for tool-specific panels like Feeds & Speeds calculator</li>
                </ul>

                <h3>Panel Management Actions</h3>

                <h4>Showing and Hiding Panels</h4>
                <p>To keep your workspace uncluttered, you can show or hide panels as needed:</p>
                <ul>
                    <li><strong>Hide Panel:</strong> Click the X button in the panel's title bar</li>
                    <li><strong>Show Panel:</strong> Use <strong>View → Panels</strong> menu and check the panel you want to display</li>
                    <li><strong>Quick Toggle:</strong> Double-click the panel's title bar to hide/show</li>
                </ul>

                <h4>Floating Panels</h4>
                <p>For complex projects, you might want a panel to float independently, similar to having a separate work surface for detailed measuring:</p>
                <ol>
                    <li>Drag a panel away from its docked position</li>
                    <li>The panel becomes a floating window</li>
                    <li>Move it to any location on your screen</li>
                    <li>Resize it independently of other panels</li>
                    <li>To re-dock: drag the floating panel back to a dock zone</li>
                </ol>

                <div class="warning">
                    <strong>⚠️ Organization Reminder:</strong> While floating panels offer flexibility, they can clutter your workspace if overused. Keep the "Keep Organized" principle in mind - only float panels when you truly need them in a separate location.
                </div>

                <h4>Tabbed Panels</h4>
                <p>When multiple panels occupy the same dock zone, they appear as tabs, like having multiple project folders in a filing cabinet:</p>
                <ul>
                    <li>Click tab headers to switch between panels</li>
                    <li>Drag tab headers to rearrange their order</li>
                    <li>Right-click tabs for additional options (close, float, etc.)</li>
                </ul>

                <div class="image-placeholder">
                    [Image: docking-system-diagram.png]
                    <br>Figure 4: Visual guide to panel docking and undocking
                </div>
            </div>

            <div class="section" id="menu-navigation">
                <h2>Menu System</h2>

                <p>The menu system in Digital Workshop is organized like a well-structured workshop manual - functions are grouped logically and can be found where you'd expect them to be. This thoughtful organization makes it easy to find the tools you need, whether you're a beginner or an experienced user.</p>

                <h3>Main Menu Overview</h3>

                <h4>File Menu</h4>
                <p>Your project entry and exit point, like the door to your workshop:</p>
                <ul>
                    <li><strong>New Project:</strong> Start a fresh woodworking project</li>
                    <li><strong>Open Project:</strong> Load an existing project</li>
                    <li><strong>Save/Save As:</strong> Preserve your work (similar to putting away tools after use)</li>
                    <li><strong>Import:</strong> Bring 3D models into your project</li>
                    <li><strong>Export:</strong> Share your designs with others or prepare files for manufacturing</li>
                    <li><strong>Recent Files:</strong> Quick access to recently worked projects</li>
                </ul>

                <h4>Edit Menu</h4>
                <p>Basic editing operations, like having a sharp pencil and eraser for making corrections:</p>
                <ul>
                    <li><strong>Undo/Redo:</strong> Correct mistakes or explore different approaches</li>
                    <li><strong>Copy/Paste:</strong> Duplicate components for efficient design</li>
                    <li><strong>Delete:</strong> Remove unwanted objects from your project</li>
                    <li><strong>Select All:</strong> Bulk operations on multiple objects</li>
                </ul>

                <h4>View Menu</h4>
                <p>Control what you see and how you see it, like adjusting lighting and positioning in your workshop:</p>
                <ul>
                    <li><strong>Zoom Controls:</strong> Get close details or see the big picture</li>
                    <li><strong>Rendering Modes:</strong> Switch between solid, wireframe, and other views</li>
                    <li><strong>Panel Visibility:</strong> Show or hide specific interface elements</li>
                    <li><strong>Layout Presets:</strong> Quickly switch between workspace configurations</li>
                </ul>

                <h4>Tools Menu</h4>
                <p>Specialized woodworking tools for digital design:</p>
                <ul>
                    <li><strong>Cut List Optimizer:</strong> Calculate optimal material usage</li>
                    <li><strong>Feeds & Speeds Calculator:</strong> Determine optimal cutting parameters</li>
                    <li><strong>Cost Estimator:</strong> Calculate project costs</li>
                    <li><strong>G-Code Previewer:</strong> Visualize machining operations</li>
                </ul>

                <h4>Project Menu</h4>
                <p>High-level project management functions:</p>
                <ul>
                    <li><strong>Project Properties:</strong> Set project-wide parameters</li>
                    <li><strong>Material Library:</strong> Manage wood species and finishes</li>
                    <li><strong>Project Statistics:</strong> View totals and summaries</li>
                    <li><strong>Backup/Archive:</strong> Preserve project versions</li>
                </ul>

                <h4>AI Menu</h4>
                <p>Artificial intelligence features that act like having an experienced mentor:</p>
                <ul>
                    <li><strong>Analyze Design:</strong> Get AI feedback on your project</li>
                    <li><strong>Material Recommendations:</strong> Receive suggestions for optimal wood choices</li>
                    <li><strong>Cost Optimization:</strong> Find ways to reduce expenses</li>
                    <li><strong>AI Settings:</strong> Configure AI provider preferences</li>
                </ul>

                <h3>Context Menus</h3>
                <p>Right-clicking on objects or in empty areas brings up context-sensitive menus. These are like having specialized tools readily available for specific tasks - the exact tools shown depend on what you've selected, making your workflow more efficient.</p>

                <div class="image-placeholder">
                    [Image: menu-system-overview.png]
                    <br>Figure 5: Complete menu system with all available options
                </div>
            </div>

            <div class="section" id="keyboard-shortcuts">
                <h2>Keyboard Shortcuts</h2>

                <p>Keyboard shortcuts in Digital Workshop are like muscle memory for your most common actions - once learned, they make your workflow much faster and more efficient. Just as experienced woodworkers develop intuitive movements with their tools, keyboard shortcuts help you work more fluidly with Digital Workshop.</p>

                <h3>Essential Shortcuts</h3>

                <h4>File Operations</h4>
                <ul>
                    <li><span class="keyboard-shortcut">Ctrl+N</span> New Project</li>
                    <li><span class="keyboard-shortcut">Ctrl+O</span> Open Project</li>
                    <li><span class="keyboard-shortcut">Ctrl+S</span> Save Project</li>
                    <li><span class="keyboard-shortcut">Ctrl+Z</span> Undo</li>
                    <li><span class="keyboard-shortcut">Ctrl+Y</span> Redo</li>
                </ul>

                <h4>View Controls</h4>
                <ul>
                    <li><span class="keyboard-shortcut">Ctrl++</span> Zoom In</li>
                    <li><span class="keyboard-shortcut">Ctrl+-</span> Zoom Out</li>
                    <li><span class="keyboard-shortcut">Ctrl+0</span> Fit to View</li>
                    <li><span class="keyboard-shortcut">Space</span> Pan (hold and drag)</li>
                    <li><span class="keyboard-shortcut">Mouse Wheel</span> Zoom in/out</li>
                </ul>

                <h4>3D Navigation</h4>
                <ul>
                    <li><span class="keyboard-shortcut">Left Mouse</span> Rotate view</li>
                    <li><span class="keyboard-shortcut">Right Mouse</span> Pan view</li>
                    <li><span class="keyboard-shortcut">Middle Mouse</span> Zoom</li>
                    <li><span class="keyboard-shortcut">Home</span> Reset camera to default view</li>
                </ul>

                <h4>Selection and Editing</h4>
                <ul>
                    <li><span class="keyboard-shortcut">Ctrl+A</span> Select All</li>
                    <li><span class="keyboard-shortcut">Delete</span> Delete selected objects</li>
                    <li><span class="keyboard-shortcut">F2</span> Rename selected object</li>
                    <li><span class="keyboard-shortcut">Escape</span> Cancel current operation</li>
                </ul>

                <h4>Tools and Panels</h4>
                <ul>
                    <li><span class="keyboard-shortcut">F1</span> Show help</li>
                    <li><span class="keyboard-shortcut">F11</span> Toggle full screen</li>
                    <li><span class="keyboard-shortcut">Tab</span> Cycle through open panels</li>
                    <li><span class="keyboard-shortcut">Ctrl+1-9</span> Switch between workspace presets</li>
                </ul>

                <div class="tip">
                    <strong>💡 Learning Tip:</strong> Start by memorizing 3-5 shortcuts that you use most often. Once these become automatic, gradually add more. This builds muscle memory just like learning to use hand tools efficiently.
                </div>

                <h3>Customizing Shortcuts</h3>
                <p>Like organizing your workshop tools in the arrangement that makes most sense to you, you can customize keyboard shortcuts to match your preferences:</p>
                <ol>
                    <li>Go to <strong>Edit → Preferences → Keyboard</strong></li>
                    <li>Browse the list of available functions</li>
                    <li>Click on any function and press your desired key combination</li>
                    <li>Click "Apply" to save your changes</li>
                </ol>
            </div>

            <div class="section" id="workspace-presets">
                <h2>Workspace Presets and Organization</h2>

                <p>The final key to mastering Digital Workshop's interface is understanding how to organize your workspace for different types of projects. Just as you might reorganize your workshop layout when switching from furniture making to cabinetry, Digital Workshop's workspace presets help you adapt to different project requirements.</p>

                <h3>Project Type Recommendations</h3>

                <h4>Furniture Projects</h4>
                <p>For chairs, tables, cabinets, and other furniture:</p>
                <ul>
                    <li>Use Design-Focused Layout for detailed modeling</li>
                    <li>Keep Properties panel prominent for precise dimensions</li>
                    <li>Enable Cut List optimizer for material planning</li>
                    <li>Use Cost estimator for project budgeting</li>
                </ul>

                <h4>CNC Machining Projects</h4>
                <p>When programming CNC operations:</p>
                <ul>
                    <li>Use Manufacturing Layout for G-code visualization</li>
                    <li>Keep Feeds & Speeds calculator accessible</li>
                    <li>Enable material analysis for optimal tool selection</li>
                    <li>Use G-code previewer for toolpath verification</li>
                </ul>

                <h4>Business Planning Projects</h4>
                <p>When estimating costs and managing multiple projects:</p>
                <ul>
                    <li>Use Business Layout for comprehensive cost analysis</li>
                    <li>Keep Project Manager visible for multiple job tracking</li>
                    <li>Enable Cost estimator for accurate pricing</li>
                    <li>Use Material library for current pricing</li>
                </ul>

                <h3>Creating Custom Layouts</h3>
                <p>Once you understand how you work best, you can save your own custom workspace configurations:</p>
                <ol>
                    <li>Arrange panels to your preferred layout</li>
                    <li>Adjust sizes and positions as needed</li>
                    <li>Go to <strong>View → Save Current Layout</strong></li>
                    <li>Give your layout a descriptive name</li>
                    <li>Use <strong>View → Load Layout</strong> to restore it later</li>
                </ol>

                <div class="image-placeholder">
                    [Image: custom-workspace-setup.png]
                    <br>Figure 6: Example of a custom workspace layout for complex projects
                </div>

                <h3>Maintaining Organization</h3>
                <p>The most important aspect of interface customization is maintaining the "Keep Organized" principle. Here are some guidelines:</p>

                <div class="note">
                    <strong>📋 Organization Checklist:</strong>
                    <ul>
                        <li>Save custom layouts with descriptive names</li>
                        <li>Keep frequently used panels easily accessible</li>
                        <li>Hide unused panels to reduce visual clutter</li>
                        <li>Regularly clean up temporary files and unused imports</li>
                        <li>Archive completed projects to keep current workspace focused</li>
                    </ul>
                </div>

                <p>Remember that your workspace should evolve with your needs. Just as you might reorganize your workshop as your skills develop and projects become more complex, don't hesitate to modify your Digital Workshop interface to better serve your current workflow.</p>

                <p>Digital Workshop's interface is designed to be powerful yet approachable, combining the precision of computer-aided design with the intuitive organization that experienced craftspeople appreciate. Take time to explore different layouts and customization options - the investment in setting up your ideal digital workshop will pay dividends in efficiency and enjoyment for years to come.</p>
            </div>

            <div style="text-align: center; margin-top: 50px;">
                <a href="index.html" class="btn back-link">← Back to Main Index</a>
                <a href="getting-started.html" class="btn">← Previous: Getting Started</a>
                <a href="model-management.html" class="btn">Next: Model Management →</a>
            </div>
        </div>
    </div>
</body>
</html>