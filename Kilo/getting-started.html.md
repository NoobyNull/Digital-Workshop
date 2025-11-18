<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Getting Started - Digital Workshop User Manual</title>
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
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Getting Started</h1>
            <p>Installation, Requirements, and First Steps</p>
        </div>

        <div class="content">
            <div class="toc">
                <h3>📋 Quick Navigation</h3>
                <ul>
                    <li><a href="#system-requirements">System Requirements</a></li>
                    <li><a href="#installation">Installation Process</a></li>
                    <li><a href="#first-run">First Run Setup</a></li>
                    <li><a href="#organizing-files">Keep Organized Method</a></li>
                    <li><a href="#tutorial-project">Your First Project</a></li>
                    <li><a href="#next-steps">Next Steps</a></li>
                </ul>
            </div>

            <div class="section">
                <p>Welcome to Digital Workshop! This guide will help you get started with your new 3D model management and CNC workflow system. Whether you're new to computer-aided design or looking to streamline your existing workflow, this section will walk you through everything you need to know to begin working effectively with your digital workshop tools.</p>

                <p>The key to success with Digital Workshop is staying organized from the start. As a 65-year-old craftsman, you understand the importance of having a well-organized workshop where every tool has its place. Digital Workshop works the same way - when you keep your files and projects organized from the beginning, you'll save time and avoid frustration later.</p>
            </div>

            <div class="section" id="system-requirements">
                <h2>System Requirements</h2>
                
                <p>Before installing Digital Workshop, it's important to ensure your computer meets the minimum requirements. Think of this like checking that your workshop has adequate lighting and power before setting up new equipment - you want everything to work smoothly from the start.</p>

                <h3>Minimum Hardware Requirements</h3>
                <ul>
                    <li><strong>Processor:</strong> Intel Core i5 or AMD equivalent (dual-core 2.5 GHz or better)</li>
                    <li><strong>Memory:</strong> 8 GB RAM (16 GB recommended for complex 3D models)</li>
                    <li><strong>Graphics:</strong> Dedicated graphics card with 2 GB VRAM (NVIDIA GTX 1060 or AMD RX 580 equivalent)</li>
                    <li><strong>Storage:</strong> 10 GB available disk space (SSD recommended for better performance)</li>
                    <li><strong>Display:</strong> 1920x1080 resolution (higher resolutions supported)</li>
                </ul>

                <h3>Supported Operating Systems</h3>
                <ul>
                    <li>Windows 10 (64-bit) or Windows 11</li>
                    <li>macOS 10.15 (Catalina) or later</li>
                    <li>Ubuntu 18.04 LTS or later (Linux)</li>
                </ul>

                <div class="note">
                    <strong>💡 Performance Tip:</strong> If you're working with large 3D models or planning to use AI analysis features, consider upgrading to 16 GB RAM and an SSD for optimal performance. Just like having a well-lit, organized workshop makes woodworking more enjoyable, having adequate computer resources makes digital design work much smoother.
                </div>

                <h3>Network Requirements</h3>
                <p>Digital Workshop can work entirely offline for basic functions, but you'll need an internet connection for:</p>
                <ul>
                    <li>AI analysis features (Gemini, OpenAI, or Anthropic integration)</li>
                    <li>Software updates and security patches</li>
                    <li>Material texture downloads</li>
                </ul>

                <div class="image-placeholder">
                    [Image: system-requirements-diagram.png]
                    <br>Figure 1: Visual representation of recommended system specifications
                </div>
            </div>

            <div class="section" id="installation">
                <h2>Installation Process</h2>

                <p>Installing Digital Workshop is designed to be as straightforward as setting up a new power tool in your workshop. The installer will guide you through each step, and the entire process typically takes 10-15 minutes depending on your internet connection speed.</p>

                <h3>Step 1: Download the Installer</h3>
                <p>Visit the official Digital Workshop website and download the installer appropriate for your operating system. The installer file will be named something like "DigitalWorkshop-Setup.exe" for Windows or "DigitalWorkshop.dmg" for Mac.</p>

                <h3>Step 2: Run the Installer</h3>
                <p>Double-click the downloaded installer file. You may see a security warning - this is normal. Click "Yes" or "Continue" to proceed. The installer will guide you through several screens:</p>

                <ol>
                    <li><strong>Welcome Screen:</strong> Introduction to Digital Workshop installation</li>
                    <li><strong>License Agreement:</strong> Terms of use (scroll through and accept)</li>
                    <li><strong>Installation Directory:</strong> Where to install the program (default is recommended)</li>
                    <li><strong>Components to Install:</strong> Choose which features to include</li>
                    <li><strong>Ready to Install:</strong> Review your selections</li>
                </ol>

                <h3>Step 3: Installation Options</h3>
                <p>The installer offers several components. For most users, we recommend selecting all components:</p>

                <ul>
                    <li><strong>Core Application:</strong> Main Digital Workshop program</li>
                    <li><strong>3D Viewer Engine:</strong> Advanced 3D visualization capabilities</li>
                    <li><strong>Sample Projects:</strong> Example files to help you learn</li>
                    <li><strong>Material Library:</strong> Wood species and texture files</li>
                    <li><strong>Tool Database:</strong> Feeds & speeds calculator data</li>
                    <li><strong>Documentation:</strong> This user manual and help files</li>
                </ul>

                <div class="warning">
                    <strong>⚠️ Important:</strong> Make sure you have at least 10 GB of free space before starting installation. If you're low on disk space, consider uninstalling unused programs first, just like clearing space in your physical workshop before adding new equipment.
                </div>

                <div class="image-placeholder">
                    [Image: installer-screenshots.png]
                    <br>Figure 2: Screenshots of the installation process
                </div>
            </div>

            <div class="section" id="first-run">
                <h2>First Run Setup</h2>

                <p>When you first launch Digital Workshop, you'll go through a setup wizard that personalizes the application for your specific needs. Think of this like setting up your workshop layout - you want everything arranged in a way that makes sense for your work style.</p>

                <h3>Step 1: Welcome and Setup Type</h3>
                <p>Choose between:</p>
                <ul>
                    <li><strong>Standard Setup (Recommended):</strong> Default settings optimized for most users</li>
                    <li><strong>Advanced Setup:</strong> Custom configuration for power users</li>
                </ul>

                <h3>Step 2: Workspace Preferences</h3>
                <p>Configure your default workspace settings:</p>
                <ul>
                    <li><strong>Default Units:</strong> Inches or millimeters (choose based on your preferred measurement system)</li>
                    <li><strong>File Save Location:</strong> Where your projects will be stored</li>
                    <li><strong>Auto-save Frequency:</strong> How often to automatically save your work</li>
                </ul>

                <h3>Step 3: Performance Settings</h3>
                <p>Optimize Digital Workshop for your computer:</p>
                <ul>
                    <li><strong>Graphics Quality:</strong> Auto-detect (recommended) or manual settings</li>
                    <li><strong>Memory Usage:</strong> Set maximum RAM usage for 3D rendering</li>
                    <li><strong>Preview Quality:</strong> Balance between visual quality and performance</li>
                </ul>

                <div class="image-placeholder">
                    [Image: first-run-wizard.png]
                    <br>Figure 3: The first-time setup wizard interface
                </div>
            </div>

            <div class="section" id="organizing-files">
                <h2>The "Keep Organized" Method</h2>

                <p>As someone who values organization in your physical workshop, you'll appreciate Digital Workshop's approach to file management. The "Keep Organized" method is designed to prevent the digital equivalent of a cluttered workshop - where tools and materials are scattered everywhere, making it impossible to find what you need when you need it.</p>

                <h3>Why Organization Matters</h3>
                <p>In woodworking, a well-organized workshop means you can find the right tool quickly, materials are stored properly, and your workspace is safe and efficient. The same principles apply to digital files:</p>

                <ul>
                    <li><strong>Efficiency:</strong> Find your files quickly instead of hunting through folders</li>
                    <li><strong>Safety:</strong> Avoid accidentally overwriting or deleting important work</li>
                    <li><strong>Scalability:</strong> As your project library grows, organization keeps everything manageable</li>
                    <li><strong>Collaboration:</strong> When sharing with others, organized files are easier to understand</li>
                </ul>

                <h3>Digital Workshop's Organization Features</h3>
                <p>Digital Workshop includes several built-in features to help you stay organized:</p>

                <h4>Project-Based Organization</h4>
                <p>Every design project gets its own folder structure, similar to how you might organize physical project materials:</p>
                <ul>
                    <li><strong>Project Name Folder:</strong> Main directory for your project</li>
                    <li><strong>3D Models:</strong> All imported and created 3D files</li>
                    <li><strong>G-Code:</strong> Generated toolpaths and CNC files</li>
                    <li><strong>Cut Lists:</strong> Optimized cutting plans and material lists</li>
                    <li><strong>Documentation:</strong> Estimates, notes, and project information</li>
                </ul>

                <h4>Smart Tagging System</h4>
                <p>Digital Workshop automatically tags your files with relevant information:</p>
                <ul>
                    <li><strong>Project Type:</strong> Furniture, cabinetry, decorative items, etc.</li>
                    <li><strong>Material Tags:</strong> Wood species, sheet goods, hardware</li>
                    <li><strong>Difficulty Level:</strong> Beginner, intermediate, advanced</li>
                    <li><strong>Completion Status:</strong> Planning, in-progress, completed</li>
                </ul>

                <div class="tip">
                    <strong>💡 Pro Tip:</strong> Spend 5 minutes organizing each new project immediately after creation. It's much easier to maintain organization from the start than to organize scattered files later. This is like putting tools back in their proper places after each use in your workshop.
                </div>

                <div class="image-placeholder">
                    [Image: organization-structure.png]
                    <br>Figure 4: Example folder structure for organized project management
                </div>
            </div>

            <div class="section" id="tutorial-project">
                <h2>Your First Project: A Simple Bookshelf</h2>

                <p>Let's walk through creating your first project to get comfortable with Digital Workshop's workflow. We'll design a simple bookshelf - a project that's complex enough to explore key features but simple enough to complete quickly.</p>

                <h3>Project Overview</h3>
                <p>Our bookshelf will be:</p>
                <ul>
                    <li>36 inches wide</li>
                    <li>72 inches tall</li>
                    <li>12 inches deep</li>
                    <li>Five adjustable shelves</li>
                    <li>Made from oak plywood</li>
                </ul>

                <h3>Step 1: Create New Project</h3>
                <ol>
                    <li>Click <strong>File → New Project</strong></li>
                    <li>Enter project name: "Bookshelf_Simple_Design"</li>
                    <li>Choose location for project files</li>
                    <li>Select project type: "Furniture"</li>
                </ol>

                <h3>Step 2: Import or Create Basic Components</h3>
                <p>For this tutorial, we'll import some basic 3D shapes that represent our bookshelf components:</p>
                <ul>
                    <li>Side panels (2 pieces)</li>
                    <li>Shelves (5 pieces)</li>
                    <li>Top and bottom panels (2 pieces)</li>
                    <li>Back panel (1 piece)</li>
                </ul>

                <h3>Step 3: Apply Materials</h3>
                <p>Digital Workshop includes a comprehensive library of wood materials. Let's apply oak finish to our bookshelf:</p>
                <ol>
                    <li>Select all bookshelf components</li>
                    <li>Right-click and choose <strong>Apply Material</strong></li>
                    <li>Navigate to <strong>Wood Species → Oak</strong></li>
                    <li>Choose "Oak Natural" texture</li>
                </ol>

                <h3>Step 4: Generate Cut List</h3>
                <p>The cut list optimizer will calculate exactly what materials you need:</p>
                <ol>
                    <li>Click <strong>Tools → Cut List Optimizer</strong></li>
                    <li>Review the generated material list</li>
                    <li>Note the total board feet required</li>
                    <li>Export cut list for your lumber yard</li>
                </ol>

                <div class="note">
                    <strong>📝 Learning Note:</strong> This tutorial project demonstrates the complete workflow: from initial concept to material planning. In your own projects, you can stop at any stage and return later. Digital Workshop automatically saves your work and maintains your project organization.
                </div>

                <div class="image-placeholder">
                    [Image: bookshelf-project-steps.png]
                    <br>Figure 5: Step-by-step progression of the bookshelf project
                </div>
            </div>

            <div class="section" id="next-steps">
                <h2>Next Steps</h2>

                <p>Congratulations! You've successfully installed Digital Workshop and completed your first project. Now it's time to explore the features that will transform how you plan and execute your woodworking projects.</p>

                <h3>Recommended Learning Path</h3>
                <p>Based on your experience level, here are the sections of this manual to explore next:</p>

                <div class="toc">
                    <h3>📚 Continue Your Learning</h3>
                    <ul>
                        <li><a href="interface-guide.html">Interface Guide</a> - Master the workspace layout</li>
                        <li><a href="model-management.html">Model Management</a> - Organize your 3D files</li>
                        <li><a href="3d-viewer.html">3D Model Viewer</a> - Explore your designs in detail</li>
                        <li><a href="materials.html">Materials & Textures</a> - Apply realistic finishes</li>
                        <li><a href="feeds-speeds.html">Feeds & Speeds Calculator</a> - Optimize your cutting parameters</li>
                    </ul>
                </div>

                <h3>Practice Projects</h3>
                <p>To build confidence with Digital Workshop, try these practice projects in order:</p>
                <ol>
                    <li><strong>Simple Box:</strong> Learn basic modeling and materials</li>
                    <li><strong>Picture Frame:</strong> Practice precise measurements and joins</li>
                    <li><strong>Cabinet Base:</strong> Explore complex assemblies</li>
                    <li><strong>Dining Table:</strong> Large-scale project planning</li>
                    <li><strong>Custom Furniture:</strong> Your own design challenges</li>
                </ol>

                <h3>Getting Help</h3>
                <p>If you encounter issues or have questions:</p>
                <ul>
                    <li><strong>Built-in Help:</strong> Press F1 or click Help in any menu</li>
                    <li><strong>This Manual:</strong> Comprehensive guides for every feature</li>
                    <li><strong>Troubleshooting Guide:</strong> Solutions for common problems</li>
                    <li><strong>Community Forums:</strong> Connect with other Digital Workshop users</li>
                </ul>

                <div class="tip">
                    <strong>💡 Success Tip:</strong> Take your time learning Digital Workshop. Like any new tool or technique in woodworking, proficiency comes with practice. Spend 15-30 minutes each day exploring different features, and you'll be amazed at how much you can accomplish.
                </div>

                <p>Welcome to the future of woodworking design. Digital Workshop combines the precision of computer-aided design with the practical knowledge of traditional craftsmanship. Whether you're planning your next furniture project or optimizing your workshop efficiency, you now have a powerful tool at your disposal.</p>

                <p>Remember the core principle: Keep Organized. Just as a well-organized workshop leads to better woodworking results, a well-organized digital workspace leads to better design outcomes. Take the time to set up your projects properly from the start, and Digital Workshop will serve you well for years to come.</p>
            </div>

            <div style="text-align: center; margin-top: 50px;">
                <a href="index.html" class="btn back-link">← Back to Main Index</a>
                <a href="interface-guide.html" class="btn">Next: Interface Guide →</a>
            </div>
        </div>
    </div>
</body>
</html>