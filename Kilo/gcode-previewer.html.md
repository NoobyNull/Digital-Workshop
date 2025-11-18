<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>G-Code Previewer - Digital Workshop User Manual</title>
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
        .toolpath-viewer {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            text-align: center;
        }
        .gcode-example {
            background: #2d3748;
            color: #e2e8f0;
            padding: 20px;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            overflow-x: auto;
            margin: 20px 0;
        }
        .simulation-controls {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
            padding: 20px;
            background: #e9ecef;
            border-radius: 8px;
        }
        .control-button {
            background: #007bff;
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 6px;
            cursor: pointer;
            text-align: center;
            transition: background-color 0.3s ease;
        }
        .control-button:hover {
            background: #0056b3;
        }
        .analysis-panel {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }
        .error-highlight {
            background: #ff6b6b;
            color: white;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: monospace;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>G-Code Previewer</h1>
            <p>CNC Toolpath Visualization and Analysis Tools</p>
        </div>

        <div class="content">
            <div class="toc">
                <h3>📋 Quick Navigation</h3>
                <ul>
                    <li><a href="#gcode-overview">G-Code System Overview</a></li>
                    <li><a href="#toolpath-visualization">Toolpath Visualization</a></li>
                    <li><a href="#simulation-controls">Simulation Controls</a></li>
                    <li><a href="#analysis-tools">Analysis Tools</a></li>
                    <li><a href="#error-detection">Error Detection</a></li>
                    <li><a href="#optimization">Toolpath Optimization</a></li>
                    <li><a href="#export-options">Export and Integration</a></li>
                    <li><a href="#troubleshooting-gcode">G-Code Troubleshooting</a></li>
                </ul>
            </div>

            <div class="section">
                <p>The G-Code Previewer in Digital Workshop serves as your digital equivalent of a test cut on scrap wood. Just as you might make practice cuts to verify settings and check for potential problems before working on your final piece, the G-Code Previewer lets you visualize and analyze your CNC toolpaths before you cut any actual material.</p>

                <p>Whether you're programming complex 3D carvings, simple pocket cuts, or detailed inlays, the G-Code Previewer helps you catch mistakes, optimize cutting sequences, and ensure your CNC machine will produce the results you expect. Think of it as having a rehearsal before the main performance - you can spot problems, refine techniques, and build confidence in your machining strategy.</p>
            </div>

            <div class="section" id="gcode-overview">
                <h2>G-Code System Overview</h2>

                <p>G-code is the programming language that tells your CNC machine what to do - much like a recipe tells you how to prepare a meal. Digital Workshop's G-Code Previewer helps you understand, visualize, and optimize this code before sending it to your machine, ensuring successful machining operations.</p>

                <div class="image-placeholder">
                    [Image: gcode-previewer-interface.png]
                    <br>Figure 1: Complete G-Code Previewer interface with toolpath visualization
                </div>

                <h3>What is G-Code?</h3>
                <p>G-code consists of instructions that control CNC machine movements and operations:</p>

                <h4>Basic G-Code Commands</h4>
                <div class="gcode-example">
G00 - Rapid positioning (move without cutting)<br>
G01 - Linear interpolation (straight line cuts)<br>
G02 - Circular interpolation clockwise<br>
G03 - Circular interpolation counterclockwise<br>
G17 - XY plane selection<br>
G20 - Inch units<br>
G21 - Millimeter units<br>
G54-G59 - Work coordinate systems<br>
M03 - Spindle on clockwise<br>
M05 - Spindle stop<br>
M08 - Coolant on<br>
M09 - Coolant off<br>
                </div>

                <h3>G-Code File Structure</h3>
                <p>Understanding the structure helps in troubleshooting and optimization:</p>

                <h4>File Components</h4>
                <ul>
                    <li><strong>Header:</strong> Machine setup and initialization commands</li>
                    <li><strong>Tool Changes:</strong> Automatic tool change commands and positions</li>
                    <li><strong>Rapid Moves:</strong> Non-cutting movements between cuts</li>
                    <li><strong>Cutting Moves:</strong> Actual machining operations</li>
                    <li><strong>Footer:</strong> Machine shutdown and cleanup</li>
                </ul>

                <div class="note">
                    <strong>📝 G-Code Reading Tip:</strong> Each line of G-code represents a specific action. Start by learning the basic movement commands (G00, G01, G02, G03) and spindle control (M03, M05). These account for most of what you'll see in typical woodworking G-code.
                </div>
            </div>

            <div class="section" id="toolpath-visualization">
                <h2>Toolpath Visualization</h2>

                <p>The toolpath visualization system shows exactly where your CNC bit will travel, helping you understand the cutting sequence and identify potential issues before machining. It's like having X-ray vision to see exactly what will happen during your CNC operation.</p>

                <h3>Visual Display Modes</h3>

                <div class="toolpath-viewer">
                    <h4>🎯 Toolpath Display Options</h4>
                    <p>Different visualization modes for different analysis needs</p>
                </div>

                <h4>Path Visualization</h4>
                <ul>
                    <li><strong>2D Path View:</strong> Top-down view showing cutting paths</li>
                    <li><strong>3D Toolpath:</strong> Three-dimensional view of complete toolpath</li>
                    <li><strong>Layer-by-Layer:</strong> Show cuts by depth or tool</li>
                    <li><strong>Animation Mode:</strong> Watch the toolpath being drawn in real-time</li>
                </ul>

                <h4>Material Simulation</h4>
                <ul>
                    <li><strong>Stock Material:</strong> Show the starting material block</li>
                    <li><strong>Material Removal:</strong> Watch material being removed during cutting</li>
                    <li><strong>Final Shape:</strong> See the finished part after all operations</li>
                    <li><strong>Cross-Section View:</strong> Examine internal cuts and geometry</li>
                </ul>

                <h3>Toolpath Color Coding</h3>
                <p>Digital Workshop uses color coding to convey important information about your toolpath:</p>

                <h4>Movement Types</h4>
                <ul>
                    <li><strong>Red:</strong> Rapid movements (G00) - non-cutting travel</li>
                    <li><strong>Blue:</strong> Cutting movements (G01) - actual machining</li>
                    <li><strong>Green:</strong> Arc movements (G02/G03) - curved cutting paths</li>
                    <li><strong>Yellow:</strong> Tool changes - pauses for tool switching</li>
                    <li><strong>Orange:</strong> Safety planes - rapid moves above work</li>
                </ul>

                <h4>Depth Information</h4>
                <ul>
                    <li><strong>Light Shades:</strong> Shallow cuts (near surface)</li>
                    <li><strong>Dark Shades:</strong> Deep cuts (farther into material)</li>
                    <li><strong>Color Gradients:</strong> Smooth transition showing depth changes</li>
                </ul>

                <div class="workflow-step">
                    <h4>🔍 How to Read Toolpath Visualization</h4>
                    <ol>
                        <li>Start with 2D view to understand overall cutting pattern</li>
                        <li>Use color coding to distinguish between cutting and rapid moves</li>
                        <li>Check that tool doesn't crash into material unexpectedly</li>
                        <li>Verify that rapid moves stay above the work surface</li>
                        <li>Use 3D view to examine depth relationships</li>
                        <li>Look for inefficient movement patterns or unnecessary moves</li>
                    </ol>
                </div>

                <h3>Zoom and Navigation</h3>
                <p>Navigate through your toolpath just like walking around a physical workpiece:</p>

                <ul>
                    <li><strong>Fit to View:</strong> Automatically show entire toolpath</li>
                    <li><strong>Zoom to Selection:</strong> Focus on specific cutting operations</li>
                    <li><strong>Pan:</strong> Move around large toolpaths</li>
                    <li><strong>Rotate:</strong> View toolpath from different angles</li>
                    <li><strong>Reset View:</strong> Return to default viewing position</li>
                </ul>

                <div class="image-placeholder">
                    [Image: toolpath-visualization-modes.png]
                    <br>Figure 2: Different toolpath visualization modes and color coding
                </div>
            </div>

            <div class="section" id="simulation-controls">
                <h2>Simulation Controls</h2>

                <p>The simulation controls let you step through your G-code program one instruction at a time, just like rehearsing a complex woodworking sequence before executing it on your actual project. This detailed step-by-step analysis helps you catch errors and optimize your cutting strategy.</p>

                <div class="simulation-controls">
                    <button class="control-button">⏮️ Rewind</button>
                    <button class="control-button">⏪ Step Back</button>
                    <button class="control-button">⏸️ Pause</button>
                    <button class="control-button">▶️ Play</button>
                    <button class="control-button">⏩ Step Forward</button>
                    <button class="control-button">⏭️ Fast Forward</button>
                </div>

                <h3>Playback Controls</h3>

                <h4>Basic Playback</h4>
                <ul>
                    <li><strong>Play/Pause:</strong> Start or stop automatic toolpath animation</li>
                    <li><strong>Step Controls:</strong> Move forward or backward one command at a time</li>
                    <li><strong>Speed Control:</strong> Adjust animation speed for detailed analysis</li>
                    <li><strong>Loop Playback:</strong> Repeat animation for continuous review</li>
                </ul>

                <h4>Advanced Controls</h4>
                <ul>
                    <li><strong>Jump to Line:</strong> Go directly to specific G-code line</li>
                    <li><strong>Bookmark Positions:</strong> Mark important points for quick reference</li>
                    <li><strong>Reverse Playback:</strong> Watch toolpath backwards to analyze retreat moves</li>
                    <li><strong>Variable Speed:</strong> Slow down for complex areas, speed up for simple moves</li>
                </ul>

                <h3>Time-Based Analysis</h3>

                <h4>Machine Time Estimation</h4>
                <p>Digital Workshop calculates how long your program will take to run:</p>

                <ul>
                    <li><strong>Total Machining Time:</strong> Complete program duration</li>
                    <li><strong>Cutting Time:</strong> Time spent actually cutting</li>
                    <li><strong>Rapid Time:</strong> Time spent moving between cuts</li>
                    <li><strong>Tool Change Time:</strong> Time for automatic tool changes</li>
                    <li><strong>Breakdown by Tool:</strong> Time per cutting tool</li>
                </ul>

                <h4>Real-Time Updates</h4>
                <ul>
                    <li><strong>Current Position:</strong> Where the tool is at any moment</li>
                    <li><strong>Feed Rate Display:</strong> Current cutting speed</li>
                    <li><strong>Spindle Speed:</strong> Current RPM settings</li>
                    <li><strong>Next Action:</strong> What the machine will do next</li>
                </ul>

                <div class="workflow-step">
                    <h4>⏱️ Using Time Analysis Effectively</h4>
                    <ol>
                        <li>Run simulation to get total machining time estimate</li>
                        <li>Identify areas with long rapid moves for optimization</li>
                        <li>Check for excessive tool changes that add time</li>
                        <li>Verify that time estimates match your experience</li>
                        <li>Use time breakdown to identify bottlenecks</li>
                        <li>Plan material handling based on total cycle time</li>
                    </ol>
                </div>
            </div>

            <div class="section" id="analysis-tools">
                <h2>Analysis Tools</h2>

                <p>Digital Workshop's analysis tools examine your G-code for potential problems, efficiency opportunities, and quality concerns. Think of these as having an experienced CNC operator review your program before you run it on expensive material.</p>

                <div class="analysis-panel">
                    <h4>🔍 Analysis Categories</h4>
                    <p>Comprehensive review of your G-code program</p>
                </div>

                <h3>Collision Detection</h3>
                <p>Automatic detection of potential machine collisions:</p>

                <h4>Collision Types</h4>
                <ul>
                    <li><strong>Tool Collisions:</strong> Tool hitting workpiece or clamps</li>
                    <li><strong>Holder Collisions:</strong> Tool holder contacting material</li>
                    <li><strong>Machine Limits:</strong> Exceeding axis travel limits</li>
                    <li><strong>Z-Depth Errors:</strong> Cutting too deep or too shallow</li>
                </ul>

                <div class="warning">
                    <strong>⚠️ Collision Warning:</strong> Never run G-code without first checking for collisions. Machine crashes can damage expensive equipment and create dangerous situations. The collision detection system can identify most common problems, but manual review is still essential.
                </div>

                <h3>Feed Rate Analysis</h3>
                <p>Review cutting speeds for optimal machining:</p>

                <h4>Speed Verification</h4>
                <ul>
                    <li><strong>Recommended Speeds:</strong> Compare to tool manufacturer's specifications</li>
                    <li><strong>Material Compatibility:</strong> Verify speeds suit the material being cut</li>
                    <li><strong>Machine Capability:</strong> Ensure speeds are within machine limits</li>
                    <li><strong>Surface Finish:</strong> Adjust speeds for desired finish quality</li>
                </ul>

                <h4>Optimization Suggestions</h4>
                <ul>
                    <li><strong>Faster Cutting:</strong> Increase feed rates where safe</li>
                    <li><strong>Better Finish:</strong> Reduce speeds in visible areas</li>
                    <li><strong>Tool Life:</strong> Adjust speeds to extend tool life</li>
                    <li><strong>Efficiency:</strong> Eliminate unnecessary speed changes</li>
                </ul>

                <h3>Toolpath Efficiency</h3>
                <p>Analyze cutting patterns for optimal material removal:</p>

                <h4>Efficiency Metrics</h4>
                <ul>
                    <li><strong>Total Distance:</strong> Total tool travel distance</li>
                    <li><strong>Cutting Ratio:</strong> Percentage of time spent cutting vs. moving</li>
                    <li><strong>Direction Changes:</strong> Number of direction reversals</li>
                    <li><strong>Rapid Moves:</strong> Efficiency of non-cutting movements</li>
                </ul>

                <h4>Optimization Opportunities</h4>
                <ul>
                    <li><strong>Reduce Rapids:</strong> Minimize non-cutting travel distance</li>
                    <li><strong>Improve Direction:</strong> Better toolpath routing</li>
                    <li><strong>Cluster Operations:</strong> Group similar cuts together</li>
                    <li><strong>Optimize Entry/Exit:</strong> Better approach and retreat moves</li>
                </ul>

                <div class="tip">
                    <strong>💡 Efficiency Tip:</strong> An efficient toolpath often takes more time to program but runs much faster. The time invested in optimization is usually repaid through reduced machining time and better tool life.
                </div>

                <h3>Material Utilization</h3>
                <p>Calculate material usage and waste:</p>

                <ul>
                    <li><strong>Chip Volume:</strong> Total amount of material removed</li>
                    <li><strong>Cutting Time per Volume:</strong> Efficiency of material removal</li>
                    <li><strong>Waste Analysis:</strong> Amount of scrap material generated</li>
                    <li><strong>Optimal Depth:</strong> Best cutting depths for efficiency</li>
                </ul>
            </div>

            <div class="section" id="error-detection">
                <h2>Error Detection and Validation</h2>

                <p>Digital Workshop's error detection system serves as a quality control checkpoint, similar to having a experienced craftsman review your project plan before you begin cutting. It catches common mistakes that could ruin your project or damage your equipment.</p>

                <h3>Common G-Code Errors</h3>

                <h4>Syntax Errors</h4>
                <div class="gcode-example">
<span class="error-highlight">ERROR:</span> G01 X10 Y20 F1.00.0  (extra decimal point)<br>
<span class="error-highlight">ERROR:</span> M3 S100           (missing Z move)<br>
<span class="error-highlight">ERROR:</span> G01 X10           (no Y coordinate)<br>
<span class="error-highlight">ERROR:</span> F500             (no feed rate)<br>
<span class="error-highlight">ERROR:</span> G20 G21          (conflicting units)<br>
                </div>

                <h4>Logic Errors</h4>
                <ul>
                    <li><strong>Missing Tool Changes:</strong> Program calls for unloaded tools</li>
                    <li><strong>Incompatible Commands:</strong> Conflicting G-code instructions</li>
                    <li><strong>Unreachable Positions:</strong> Moves outside machine workspace</li>
                    <li><strong>Missing Safety Codes:</strong> Spindle or coolant control missing</li>
                </ul>

                <h4>Configuration Errors</h4>
                <ul>
                    <li><strong>Unit Inconsistencies:</strong> Mixed inch and millimeter commands</li>
                    <li><strong>Coordinate System Issues:</strong> Wrong work offset selection</li>
                    <li><strong>Tool Length Problems:</strong> Incorrect tool length compensation</li>
                    <li><strong>Material Thickness Mismatch:</strong> Cuts don't match material size</li>
                </ul>

                <h3>Validation Process</h3>

                <div class="workflow-step">
                    <h4>✅ Error Detection Workflow</h4>
                    <ol>
                        <li>Load G-code file into previewer</li>
                        <li>Run automatic error detection</li>
                        <li>Review flagged issues in order of severity</li>
                        <li>Fix syntax errors first</li>
                        <li>Verify logical consistency</li>
                        <li>Check material and tool compatibility</li>
                        <li>Validate against machine specifications</li>
                        <li>Re-run simulation to confirm fixes</li>
                    </ol>
                </div>

                <h3>Warning Categories</h3>

                <h4>Critical Errors</h4>
                <div class="note">
                    <strong>🔴 Critical:</strong> Must be fixed before running. Examples: missing safety codes, machine collisions, syntax errors that could cause crashes.
                </div>

                <h4>Warnings</h4>
                <div class="note">
                    <strong>🟡 Warning:</strong> Should be reviewed and addressed. Examples: inefficient toolpaths, aggressive feed rates, missing comments.
                </div>

                <h4>Suggestions</h4>
                <div class="note">
                    <strong>🔵 Suggestion:</strong> Optional improvements. Examples: add comments, optimize moves, improve organization.
                </div>
            </div>

            <div class="section" id="optimization">
                <h2>Toolpath Optimization</h2>

                <p>Optimization improves your G-code by reducing machining time, improving surface finish, extending tool life, and increasing overall efficiency. This is like refining your woodworking technique - you learn to work smarter, not just harder.</p>

                <h3>Automatic Optimization</h3>

                <h4>System-Provided Optimizations</h4>
                <ul>
                    <li><strong>Rapid Move Optimization:</strong> Shortest path between cuts</li>
                    <li><strong>Direction Changes:</strong> Minimize abrupt direction changes</li>
                    <li><strong>Entry/Exit Optimization:</strong> Smooth approach and retreat moves</li>
                    <li><strong>Tool Changes:</strong> Optimal tool change positions</li>
                </ul>

                <h4>Feed Rate Optimization</h4>
                <ul>
                    <li><strong>Constant Surface Speed:</strong> Maintain consistent cutting conditions</li>
                    <li><strong>Adaptive Feed Rates:</strong> Adjust speed based on tool engagement</li>
                    <li><strong>Acceleration Limiting:</strong> Smooth starts and stops</li>
                    <li><strong>Chord Tolerance:</strong> Balance accuracy vs. speed on arcs</li>
                </ul>

                <h3>Manual Optimization</h3>

                <h4>Toolpath Editing</h4>
                <ul>
                    <li><strong>Move Reordering:</strong> Change sequence of operations</li>
                    <li><strong>Path Smoothing:</strong> Eliminate unnecessary points</li>
                    <li><strong>Duplicate Removal:</strong> Delete redundant moves</li>
                    <li><strong>Coordinate Optimization:</strong> Use more efficient coordinate systems</li>
                </ul>

                <h4>Parameter Adjustment</h4>
                <ul>
                    <li><strong>Depth of Cut:</strong> Optimize for chip load and surface finish</li>
                    <li><strong>Step-over:</strong> Balance between efficiency and finish quality</li>
                    <li><strong>Feed Rates:</strong> Fine-tune for specific materials and tools</li>
                    <li><strong>Plunge Rates:</strong> Optimize vertical cutting speeds</li>
                </ul>

                <div class="image-placeholder">
                    [Image: optimization-comparison.png]
                    <br>Figure 3: Before and after optimization comparison showing efficiency gains
                </div>

                <h3>Optimization Results</h3>

                <h4>Measurable Improvements</h4>
                <ul>
                    <li><strong>Machining Time:</strong> Reduction in total program time</li>
                    <li><strong>Tool Life:</strong> Increased cutting tool lifespan</li>
                    <li><strong>Surface Finish:</strong> Improved part quality</li>
                    <li><strong>Material Usage:</strong> Reduced waste and better yields</li>
                </ul>

                <div class="tip">
                    <strong>💡 Optimization Tip:</strong> Start with automatic optimization, then fine-tune manually. Automatic optimization handles most efficiency issues, while manual adjustments allow you to optimize for your specific machines and materials.
                </div>
            </div>

            <div class="section" id="export-options">
                <h2>Export and Integration</h2>

                <p>Digital Workshop's G-Code Previewer integrates seamlessly with your CNC workflow, allowing you to export optimized code, generate reports, and share analysis with team members or clients.</p>

                <h3>Export Formats</h3>

                <h4>Standard Formats</h4>
                <ul>
                    <li><strong>G-Code (.nc, .tap):</strong> Standard CNC programming files</li>
                    <li><strong>CSV Reports:</strong> Spreadsheet-compatible analysis data</li>
                    <li><strong>PDF Documentation:</strong> Professional reports for clients</li>
                    <li><strong>Images:</strong> Visualization screenshots for presentations</li>
                </ul>

                <h4>Machine-Specific Exports</h4>
                <ul>
                    <li><strong>Post-Processor Output:</strong> Code formatted for specific machines</li>
                    <li><strong>Controller Settings:</strong> Optimal parameters for your control</li>
                    <li><strong>Tool Lists:</strong> Complete tool setup information</li>
                    <li><strong>Setup Sheets:</strong> Machine setup instructions</li>
                </ul>

                <h3>Documentation Generation</h3>

                <h4>Comprehensive Reports</h4>
                <div class="workflow-step">
                    <h4>📄 Generating G-Code Reports</h4>
                    <ol>
                        <li>Complete G-code analysis and optimization</li>
                        <li>Choose report type (summary, detailed, or client presentation)</li>
                        <li>Include analysis results and recommendations</li>
                        <li>Add machine setup information</li>
                        <li>Generate timing estimates and material requirements</li>
                        <li>Export in desired format</li>
                    </ol>
                </div>

                <h4>Report Contents</h4>
                <ul>
                    <li><strong>Program Summary:</strong> Total time, operations, tools used</li>
                    <li><strong>Analysis Results:</strong> Efficiency metrics and recommendations</li>
                    <li><strong>Tool List:</strong> Complete tooling information</li>
                    <li><strong>Setup Instructions:</strong> Machine setup and calibration details</li>
                    <li><strong>Safety Notes:</strong> Important safety considerations</li>
                </ul>

                <h3>Integration with CAM Software</h3>

                <h4>Common CAM Workflows</h4>
                <ul>
                    <li><strong>Import from CAM:</strong> Load G-code generated by CAM software</li>
                    <li><strong>Validation Only:</strong> Verify G-code before sending to machine</li>
                    <li><strong>Optimization Loop:</strong> Iterative improvement process</li>
                    <li><strong>Final Export:</strong> Optimized code ready for machining</li>
                </ul>

                <div class="note">
                    <strong>📋 Integration Best Practice:</strong> Use Digital Workshop as a validation and optimization step in your CAM workflow. Generate G-code in your CAM software, import it into Digital Workshop for analysis and optimization, then export the improved version for your CNC machine.
                </div>
            </div>

            <div class="section" id="troubleshooting-gcode">
                <h2>G-Code Troubleshooting</h2>

                <p>Even with careful planning, G-code issues can arise. Digital Workshop's troubleshooting tools help you identify and resolve problems quickly, minimizing downtime and preventing expensive mistakes.</p>

                <h3>Common Problems and Solutions</h3>

                <h4>Machine Won't Start</h4>
                <div class="analysis-panel">
                    <h4>🔧 Troubleshooting Steps</h4>
                    <ul>
                        <li>Check for critical errors in error detection</li>
                        <li>Verify machine limits aren't exceeded</li>
                        <li>Ensure all required safety codes are present</li>
                        <li>Confirm tool definitions are complete</li>
                        <li>Validate coordinate system setup</li>
                    </ul>
                </div>

                <h4>Unusual Machine Behavior</h4>
                <ul>
                    <li><strong>Jerkiness:</strong> Check for conflicting commands or rapid acceleration</li>
                    <li><strong>Wrong Directions:</strong> Verify coordinate system and machine configuration</li>
                    <li><strong>Speed Issues:</strong> Review feed rate settings and acceleration limits</li>
                    <li><strong>Tool Collisions:</strong> Re-run collision detection with updated geometry</li>
                </ul>

                <h4>Poor Surface Finish</h4>
                <ul>
                    <li><strong>Reduce Feed Rates:</strong> Slow down cutting speed in problem areas</li>
                    <li><strong>Check Tool Condition:</strong> Verify cutting tool is sharp and undamaged</li>
                    <li><strong>Adjust Step-over:</strong> Reduce step-over for smoother finish</li>
                    <li><strong>Improve Toolpath:</strong> Smooth corners and reduce direction changes</li>
                </ul>

                <h3>Debugging Techniques</h3>

                <h4>Step-by-Step Analysis</h4>
                <div class="workflow-step">
                    <h4>🔍 Systematic Debugging Process</h4>
                    <ol>
                        <li>Start simulation and watch for unusual behavior</li>
                        <li>Note the exact G-code line where problems occur</li>
                        <li>Use step controls to isolate problematic commands</li>
                        <li>Check machine configuration for that operation</li>
                        <li>Compare to working programs for similar operations</li>
                        <li>Test fixes in simulation before machine testing</li>
                    </ol>
                </div>

                <h4>Isolating Problems</h4>
                <ul>
                    <li><strong>Comment Out Sections:</strong> Temporarily disable parts of program</li>
                    <li><strong>Single Tool Test:</strong> Run only one tool to isolate issues</li>
                    <li><strong>Reduced Depth Test:</strong> Test with shallow cuts first</li>
                    <li><strong>Slow Speed Test:</strong> Run at reduced feed rates initially</li>
                </ul>

                <div class="warning">
                    <strong>⚠️ Safety First:</strong> Always test G-code with scrap material at reduced speeds before running on expensive stock. Use emergency stop procedures and never leave the machine unattended during initial testing.
                </div>

                <h3>Best Practices Summary</h3>

                <div class="note">
                    <strong>📋 G-Code Best Practices:</strong>
                    <ul>
                        <li>Always preview and analyze G-code before running on your machine</li>
                        <li>Use scrap material for initial testing of new programs</li>
                        <li>Start with conservative feed rates and speeds</li>
                        <li>Keep detailed notes about what works and what doesn't</li>
                        <li>Build a library of proven G-code snippets</li>
                        <li>Regularly backup your working G-code files</li>
                        <li>Test tool changes and probing cycles carefully</li>
                        <li>Document machine-specific settings and configurations</li>
                        <li>Use collision detection to prevent expensive crashes</li>
                        <li>Optimize programs for efficiency without sacrificing quality</li>
                    </ul>
                </div>

                <p>The G-Code Previewer transforms CNC programming from guesswork into a predictable, controlled process. By visualizing toolpaths, analyzing cutting strategies, and catching errors before they become expensive mistakes, you can approach CNC machining with the same confidence and precision that characterizes fine woodworking.</p>

                <p>Remember that the goal is not just to create working G-code, but to create optimal G-code that produces high-quality parts efficiently and safely. Take time to learn the visualization tools, practice with the analysis features, and develop a systematic approach to G-code validation and optimization.</p>

                <p>Like any skilled craft, mastering G-code programming takes practice and experience. Digital Workshop's previewer and analysis tools accelerate this learning process by providing immediate feedback and preventing costly errors. Use these capabilities to build your CNC programming skills while producing better results with less wasted time and material.</p>
            </div>

            <div style="text-align: center; margin-top: 50px;">
                <a href="index.html" class="btn back-link">← Back to Main Index</a>
                <a href="materials.html" class="btn">← Previous: Materials & Textures</a>
                <a href="cut-list.html" class="btn">Next: Cut List Optimizer →</a>
            </div>
        </div>
    </div>
</body>
</html>