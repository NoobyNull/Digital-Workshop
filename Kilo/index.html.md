<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Digital Workshop - User Manual</title>
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
            font-size: 3rem;
            font-weight: 300;
            letter-spacing: 2px;
        }
        .header p {
            margin: 20px 0 0 0;
            font-size: 1.2rem;
            opacity: 0.9;
        }
        .nav-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            padding: 40px 30px;
        }
        .nav-card {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 25px;
            text-decoration: none;
            color: inherit;
            transition: all 0.3s ease;
            border-left: 4px solid #007bff;
            display: block;
        }
        .nav-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(0,0,0,0.1);
            border-left-color: #0056b3;
        }
        .nav-card h3 {
            margin: 0 0 15px 0;
            color: #2c3e50;
            font-size: 1.4rem;
        }
        .nav-card p {
            margin: 0;
            color: #6c757d;
            line-height: 1.5;
        }
        .nav-card .section-number {
            display: inline-block;
            background: #007bff;
            color: white;
            border-radius: 50%;
            width: 24px;
            height: 24px;
            text-align: center;
            line-height: 24px;
            font-size: 0.8rem;
            margin-right: 10px;
        }
        .footer {
            background: #f8f9fa;
            padding: 30px;
            text-align: center;
            border-top: 1px solid #e9ecef;
        }
        .quick-start {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .quick-start h2 {
            margin: 0 0 15px 0;
        }
        .quick-start p {
            margin: 0 0 20px 0;
            font-size: 1.1rem;
        }
        .btn-primary {
            display: inline-block;
            background: white;
            color: #28a745;
            padding: 12px 24px;
            border-radius: 6px;
            text-decoration: none;
            font-weight: bold;
            transition: transform 0.2s ease;
        }
        .btn-primary:hover {
            transform: scale(1.05);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Digital Workshop</h1>
            <p>Complete User Manual for 3D Model Management & CNC Workflow</p>
        </div>

        <div class="quick-start">
            <h2>🚀 Quick Start Guide</h2>
            <p>New to Digital Workshop? Start here to get up and running in minutes.</p>
            <a href="getting-started.html" class="btn-primary">Get Started Now</a>
        </div>

        <div class="nav-grid">
            <a href="getting-started.html" class="nav-card">
                <h3><span class="section-number">1</span> Getting Started</h3>
                <p>Installation, system requirements, and first-time setup. Everything you need to begin.</p>
            </a>

            <a href="interface-guide.html" class="nav-card">
                <h3><span class="section-number">2</span> Interface Guide</h3>
                <p>Learn the main window layout, dockable panels, and how to customize your workspace.</p>
            </a>

            <a href="model-management.html" class="nav-card">
                <h3><span class="section-number">3</span> Model Management</h3>
                <p>Import, organize, and search your 3D models with our comprehensive library system.</p>
            </a>

            <a href="3d-viewer.html" class="nav-card">
                <h3><span class="section-number">4</span> 3D Model Viewer</h3>
                <p>Master the 3D viewer with rendering modes, camera controls, and material application.</p>
            </a>

            <a href="materials.html" class="nav-card">
                <h3><span class="section-number">5</span> Materials & Textures</h3>
                <p>Apply realistic wood species and custom materials to bring your models to life.</p>
            </a>

            <a href="gcode-previewer.html" class="nav-card">
                <h3><span class="section-number">6</span> G-Code Previewer</h3>
                <p>Visualize CNC toolpaths, analyze feed rates, and optimize your machining operations.</p>
            </a>

            <a href="cut-list.html" class="nav-card">
                <h3><span class="section-number">7</span> Cut List Optimizer</h3>
                <p>Optimize material usage with advanced algorithms for maximum efficiency.</p>
            </a>

            <a href="feeds-speeds.html" class="nav-card">
                <h3><span class="section-number">8</span> Feeds & Speeds Calculator</h3>
                <p>Calculate optimal cutting parameters for your tools, materials, and projects.</p>
            </a>

            <a href="cost-estimator.html" class="nav-card">
                <h3><span class="section-number">9</span> Cost Estimator</h3>
                <p>Estimate project costs with comprehensive material, labor, and equipment tracking.</p>
            </a>

            <a href="ai-analysis.html" class="nav-card">
                <h3><span class="section-number">10</span> AI Analysis</h3>
                <p>Use artificial intelligence to automatically analyze models and generate metadata.</p>
            </a>

            <a href="troubleshooting.html" class="nav-card">
                <h3><span class="section-number">11</span> Troubleshooting</h3>
                <p>Resolve common issues and find solutions to problems you might encounter.</p>
            </a>
        </div>

        <div class="footer">
            <p><strong>Digital Workshop User Manual</strong></p>
            <p>Version 1.0 | Last Updated: November 2025</p>
            <p>For technical support and additional resources, visit our help section.</p>
        </div>
    </div>
</body>
</html>