<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Materials & Textures - Digital Workshop User Manual</title>
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
        .wood-species-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .wood-card {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            transition: transform 0.2s ease;
        }
        .wood-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .wood-icon {
            font-size: 2.5rem;
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
        .material-preview {
            background: linear-gradient(45deg, #8B4513, #D2691E);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Materials & Textures</h1>
            <p>Wood Species, Custom Materials, and Realistic Finishing</p>
        </div>

        <div class="content">
            <div class="toc">
                <h3>📋 Quick Navigation</h3>
                <ul>
                    <li><a href="#material-system">Materials System Overview</a></li>
                    <li><a href="#wood-species">Wood Species Library</a></li>
                    <li><a href="#applying-materials">Applying Materials</a></li>
                    <li><a href="#custom-materials">Creating Custom Materials</a></li>
                    <li><a href="#surface-finishes">Surface Finishes</a></li>
                    <li><a href="#material-projection">Material Mapping</a></li>
                    <li><a href="#batch-application">Batch Material Application</a></li>
                    <li><a href="#material-library">Managing Material Library</a></li>
                </ul>
            </div>

            <div class="section">
                <p>Digital Workshop's materials system brings your digital designs to life by simulating the natural beauty and characteristics of real wood. Just as selecting the right wood species is crucial in your physical workshop, choosing appropriate digital materials helps you visualize how your finished piece will look and assists in making informed design decisions.</p>

                <p>Whether you're planning a dining table from oak, a cabinet from cherry, or a decorative piece from walnut, Digital Workshop's comprehensive material library lets you see exactly how different wood species will interact with your design. This preview capability helps you avoid expensive mistakes and ensures your finished piece matches your vision.</p>
            </div>

            <div class="section" id="material-system">
                <h2>Materials System Overview</h2>

                <p>The materials system in Digital Workshop is designed to be as intuitive as selecting lumber from your local sawmill. It combines realistic visual representation with practical information about wood characteristics, making it easier to plan your projects and communicate your vision to clients.</p>

                <div class="image-placeholder">
                    [Image: materials-system-interface.png]
                    <br>Figure 1: Complete materials system interface showing library and application tools
                </div>

                <h3>Material System Components</h3>

                <h4>Visual Representation</h4>
                <p>Digital Workshop uses high-quality texture mapping to recreate the appearance of real wood:</p>
                <ul>
                    <li><strong>Realistic Wood Grain:</strong> Authentic grain patterns based on actual wood samples</li>
                    <li><strong>Color Accuracy:</strong> True-to-life colors for each wood species</li>
                    <li><strong>Surface Texture:</strong> Visual representation of smooth, rough, and textured surfaces</li>
                    <li><strong>Grain Direction:</strong> Proper grain alignment for realistic appearance</li>
                </ul>

                <h4>Material Information</h4>
                <p>Each material includes practical information for planning and estimation:</p>
                <ul>
                    <li><strong>Wood Species:</strong> Common and botanical names</li>
                    <li><strong>Hardness Rating:</strong> Janka hardness scale for workability</li>
                    <li><strong>Typical Uses:</strong> Recommended applications for each species</li>
                    <li><strong>Cost Range:</strong> Estimated material costs for budgeting</li>
                    <li><strong>Availability:</strong> Common sizes and stock information</li>
                </ul>

                <h4>Technical Properties</h4>
                <ul>
                    <li><strong>Density:</strong> Weight calculations for project planning</li>
                    <li><strong>Shrinkage:</strong> Movement characteristics during drying</li>
                    <li><strong>Workability:</strong> How well the species machines and hand-tools</li>
                    <li><strong>Finishing Properties:</strong> How well different finishes adhere</li>
                </ul>

                <h3>Material Categories</h3>
                <p>Materials are organized in logical categories for easy navigation:</p>

                <div class="wood-species-grid">
                    <div class="wood-card">
                        <div class="wood-icon">🌳</div>
                        <h4>Hardwoods</h4>
                        <p>Oak, maple, cherry, walnut, and other durable wood species</p>
                    </div>
                    <div class="wood-card">
                        <div class="wood-icon">🌲</div>
                        <h4>Softwoods</h4>
                        <p>Pine, cedar, fir, and other coniferous species</p>
                    </div>
                    <div class="wood-card">
                        <div class="wood-icon">📦</div>
                        <h4>Sheet Goods</h4>
                        <p>Plywood, MDF, particleboard, and engineered materials</p>
                    </div>
                    <div class="wood-card">
                        <div class="wood-icon">🎨</div>
                        <h4>Finishes</h4>
                        <p>Stains, varnishes, paints, and surface treatments</p>
                    </div>
                </div>
            </div>

            <div class="section" id="wood-species">
                <h2>Wood Species Library</h2>

                <p>Digital Workshop includes a comprehensive library of wood species, each carefully researched and photographed to provide accurate representation. Think of this library as your digital lumberyard, where you can examine different wood species and see how they look in your specific designs.</p>

                <h3>Hardwood Species</h3>

                <h4>Oak (White Oak)</h4>
                <div class="workflow-step">
                    <h4>🌳 White Oak Characteristics</h4>
                    <ul>
                        <li><strong>Color:</strong> Light tan to medium brown with golden undertones</li>
                        <li><strong>Grain:</strong> Prominent, open grain with distinctive ray patterns</li>
                        <li><strong>Hardness:</strong> 1360 Janka (very hard)</li>
                        <li><strong>Best Uses:</strong> Dining tables, kitchen cabinets, flooring, outdoor furniture</li>
                        <li><strong>Finishing:</strong> Takes stain well, natural finish highlights grain</li>
                    </ul>
                </div>

                <h4>Maple (Hard Maple)</h4>
                <div class="workflow-step">
                    <h4>🌳 Hard Maple Characteristics</h4>
                    <ul>
                        <li><strong>Color:</strong> Light cream to pale reddish-white</li>
                        <li><strong>Grain:</strong> Fine, even grain with subtle figure</li>
                        <li><strong>Hardness:</strong> 1450 Janka (very hard)</li>
                        <li><strong>Best Uses:</strong> Cutting boards, butcher blocks, fine furniture, musical instruments</li>
                        <li><strong>Finishing:</strong> Excellent for painted or stained finishes, takes clear coats beautifully</li>
                    </ul>
                </div>

                <h4>Cherry (Black Cherry)</h4>
                <div class="workflow-step">
                    <h4>🌳 Black Cherry Characteristics</h4>
                    <ul>
                        <li><strong>Color:</strong> Rich reddish-brown that deepens with age</li>
                        <li><strong>Grain:</strong> Fine, smooth grain with attractive figure</li>
                        <li><strong>Hardness:</strong> 950 Janka (moderately hard)</li>
                        <li><strong>Best Uses:</strong> Fine furniture, cabinetry, decorative accents</li>
                        <li><strong>Finishing:</strong> Beautiful with natural finish, darkens with UV exposure</li>
                    </ul>
                </div>

                <h4>Walnut (Black Walnut)</h4>
                <div class="workflow-step">
                    <h4>🌳 Black Walnut Characteristics</h4>
                    <ul>
                        <li><strong>Color:</strong> Rich chocolate brown with purple undertones</li>
                        <li><strong>Grain:</strong> Straight to wavy grain with interesting figure</li>
                        <li><strong>Hardness:</strong> 1010 Janka (moderately hard)</li>
                        <li><strong>Best Uses:</strong> Accent pieces, gunstocks, fine furniture, veneers</li>
                        <li><strong>Finishing:</strong> Stunning with natural oil finishes, takes stain well</li>
                    </ul>
                </div>

                <div class="tip">
                    <strong>💡 Wood Selection Tip:</strong> Consider the wood's natural characteristics when choosing species. Open-grained woods like oak show grain fillers prominently, while fine-grained woods like maple provide a smoother appearance. This affects both the visual impact and the amount of finishing work required.
                </div>

                <h3>Softwood Species</h3>

                <h4>Pine (Eastern White Pine)</h4>
                <ul>
                    <li><strong>Color:</strong> Creamy white to pale yellow</li>
                    <li><strong>Grain:</strong> Straight, even grain with minimal figure</li>
                    <li><strong>Hardness:</strong> 380 Janka (soft)</li>
                    <li><strong>Best Uses:</strong> Carving, millwork, painted furniture, rustic pieces</li>
                    <li><strong>Finishing:</strong> Excellent for painted finishes, takes stain with conditioning</li>
                </ul>

                <h4>Cedar (Eastern Red Cedar)</h4>
                <ul>
                    <li><strong>Color:</strong> Rich reddish-brown with golden highlights</li>
                    <li><strong>Grain:</strong> Straight grain with aromatic properties</li>
                    <li><strong>Hardness:</strong> 900 Janka (moderately hard)</li>
                    <li><strong>Best Uses:</strong> Outdoor furniture, chests, closet linings, shingles</li>
                    <li><strong>Finishing:</strong> Natural oils provide protection, clear finishes enhance color</li>
                </ul>

                <h3>Engineered Materials</h3>

                <h4>Plywood</h4>
                <ul>
                    <li><strong>Types:</strong> Baltic birch, furniture-grade, cabinet-grade plywood</li>
                    <li><strong>Advantages:</strong> Dimensional stability, strength, cost-effective</li>
                    <li><strong>Best Uses:</strong> Cabinet cases, furniture backs, structural applications</li>
                    <li><strong>Finishing:</strong> Veneer species dictate appearance, edge banding often used</li>
                </ul>

                <h4>MDF (Medium Density Fiberboard)</h4>
                <ul>
                    <li><strong>Characteristics:</strong> Smooth, uniform surface, excellent for machining</li>
                    <li><strong>Advantages:</strong> No grain pattern, takes paint exceptionally well</li>
                    <li><strong>Best Uses:</strong> Painted cabinet doors, molding, decorative panels</li>
                    <li><strong>Finishing:</strong> Primarily painted, can be veneered for premium look</li>
                </ul>

                <div class="image-placeholder">
                    [Image: wood-species-comparison.png]
                    <br>Figure 2: Side-by-side comparison of major wood species
                </div>
            </div>

            <div class="section" id="applying-materials">
                <h2>Applying Materials to Models</h2>

                <p>Applying materials in Digital Workshop is as simple as selecting a wood species from your lumber pile and applying it to your workpiece. The system automatically handles texture mapping, grain direction, and material properties, giving you realistic results with minimal effort.</p>

                <h3>Basic Material Application</h3>

                <div class="workflow-step">
                    <h4>🎨 How to Apply Materials</h4>
                    <ol>
                        <li>Select one or more objects in your 3D model</li>
                        <li>Open the Materials panel (View → Materials)</li>
                        <li>Browse the wood species library or search for specific species</li>
                        <li>Click on the desired material to preview it</li>
                        <li>Click "Apply" to apply the material to selected objects</li>
                        <li>The 3D viewer updates immediately to show the new material</li>
                    </ol>
                </div>

                <h3>Selection Methods</h3>
                <p>Digital Workshop supports multiple selection methods for applying materials:</p>

                <h4>Single Object Selection</h4>
                <ul>
                    <li><strong>Click Selection:</strong> Click directly on any object to select it</li>
                    <li><strong>Double-click:</strong> Select object and open material properties</li>
                    <li><strong>Shift-click:</strong> Add individual objects to your selection</li>
                </ul>

                <h4>Multiple Object Selection</h4>
                <ul>
                    <li><strong>Drag Selection:</strong> Draw a selection box around multiple objects</li>
                    <li><strong>Ctrl-click:</strong> Add or remove objects from selection</li>
                    <li><strong>Select All:</strong> Apply material to entire assembly</li>
                    <li><strong>Filter Selection:</strong> Select objects by material, size, or type</li>
                </ul>

                <h4>Smart Selection</h4>
                <ul>
                    <li><strong>By Material:</strong> Select all objects currently using a specific material</li>
                    <li><strong>By Wood Species:</strong> Select objects made from particular wood type</li>
                    <li><strong>By Project Phase:</strong> Select objects designated for specific finishing</li>
                    <li><strong>By Assembly Group:</strong> Select related components automatically</li>
                </ul>

                <div class="note">
                    <strong>📋 Selection Best Practice:</strong> Group related objects before applying materials. For example, select all tabletop pieces together and all leg pieces together. This ensures consistent material application and makes it easier to manage materials throughout your project.
                </div>

                <h3>Material Preview and Testing</h3>

                <h4>Live Preview</h4>
                <p>Before committing to a material, you can preview how it looks on your specific model:</p>

                <ul>
                    <li><strong>Hover Preview:</strong> Move cursor over materials to see instant preview</li>
                    <li><strong>Full Preview:</strong> Click material name to apply temporary preview</li>
                    <li><strong>Comparison View:</strong> See multiple materials side-by-side</li>
                    <li><strong>A/B Testing:</strong> Toggle between two materials for comparison</li>
                </ul>

                <h4>Preview Settings</h4>
                <ul>
                    <li><strong>Lighting Conditions:</strong> See how material looks in different lighting</li>
                    <li><strong>Viewing Angles:</strong> Test materials from different perspectives</li>
                    <li><strong>Scale Settings:</strong> Adjust material scale for optimal appearance</li>
                    <li><strong>Texture Detail:</strong> Vary texture resolution for performance vs. quality</li>
                </ul>
            </div>

            <div class="section" id="custom-materials">
                <h2>Creating Custom Materials</h2>

                <p>While Digital Workshop's library includes most commonly used wood species, you may want to create custom materials for specific projects or to match existing lumber. This is like mixing your own stains or creating custom color combinations in your workshop.</p>

                <h3>Material Creation Process</h3>

                <div class="workflow-step">
                    <h4>🛠️ Creating Custom Materials</h4>
                    <ol>
                        <li>Open Materials panel and click "Create New Material"</li>
                        <li>Choose base material type (wood, finish, or composite)</li>
                        <li>Set basic properties (color, hardness, workability)</li>
                        <li>Upload or select texture images</li>
                        <li>Adjust mapping settings for proper appearance</li>
                        <li>Save material with descriptive name</li>
                        <li>Test material on sample objects</li>
                    </ol>
                </div>

                <h3>Material Properties</h3>

                <h4>Visual Properties</h4>
                <ul>
                    <li><strong>Base Color:</strong> Primary color tone of the material</li>
                    <li><strong>Grain Pattern:</strong> Size and frequency of grain features</li>
                    <li><strong>Surface Texture:</strong> Smooth, textured, or rough surface appearance</li>
                    <li><strong>Reflectivity:</strong> How shiny or matte the surface appears</li>
                    <li><strong>Transparency:</strong> For clear finishes or translucent materials</li>
                </ul>

                <h4>Physical Properties</h4>
                <ul>
                    <li><strong>Hardness:</strong> Janka hardness rating for workability</li>
                    <li><strong>Density:</strong> Weight per unit volume for calculations</li>
                    <li><strong>Grain Direction:</strong> Primary grain orientation</li>
                    <li><strong>Shrinkage Rate:</strong> Movement characteristics during drying</li>
                    <li><strong>Finishing Compatibility:</strong> How well different finishes work</li>
                </ul>

                <h3>Texture Creation and Import</h3>

                <h4>Texture Sources</h4>
                <ul>
                    <li><strong>Photographs:</strong> High-resolution photos of actual wood samples</li>
                    <li><strong>Scanned Surfaces:</strong> Digitized textures from physical wood pieces</li>
                    <li><strong>Generated Textures:</strong> Computer-generated patterns and effects</li>
                    <li><strong>Stock Libraries:</strong> Professional texture libraries</li>
                </ul>

                <h4>Texture Requirements</h4>
                <ul>
                    <li><strong>Resolution:</strong> Minimum 1024x1024 pixels, 2048x2048 recommended</li>
                    <li><strong>Format:</strong> PNG, JPEG, or TIFF formats supported</li>
                    <li><strong>Color Depth:</strong> 24-bit color for best quality</li>
                    <li><strong>File Size:</strong> Less than 10 MB per texture file</li>
                </ul>

                <h4>Texture Optimization</h4>
                <ul>
                    <li><strong>Seamless Tiling:</strong> Textures that repeat without visible seams</li>
                    <li><strong>Color Correction:</strong> Adjust brightness, contrast, and saturation</li>
                    <li><strong>Grain Alignment:</strong> Ensure grain runs consistently</li>
                    <li><strong>Detail Enhancement:</strong> Enhance subtle grain features</li>
                </ul>

                <div class="tip">
                    <strong>💡 Texture Tip:</strong> When photographing wood for textures, use diffused lighting to avoid harsh shadows. Take multiple shots at different angles and distances, then choose the best image that represents the wood's typical appearance. Avoid extreme lighting conditions that create strong shadows or reflections.
                </div>
            </div>

            <div class="section" id="surface-finishes">
                <h2>Surface Finishes and Treatments</h2>

                <p>Digital Workshop doesn't just show raw wood - it also includes a comprehensive range of finishes and surface treatments. This allows you to see exactly how different stains, varnishes, paints, and other finishes will look on your chosen wood species.</p>

                <h3>Finish Categories</h3>

                <h4>Natural Finishes</h4>
                <div class="wood-species-grid">
                    <div class="wood-card">
                        <div class="wood-icon">🛢️</div>
                        <h4>Oil Finishes</h4>
                        <p>Tung oil, boiled linseed oil, Danish oil - enhance natural wood beauty</p>
                    </div>
                    <div class="wood-card">
                        <div class="wood-icon">✨</div>
                        <h4>Shellac</h4>
                        <p>Natural resin finish, excellent for detailed work and restoration</p>
                    </div>
                    <div class="wood-card">
                        <div class="wood-icon">💧</div>
                        <h4>Water-Based Finishes</h4>
                        <p>Clear coats, low odor, quick drying options</p>
                    </div>
                    <div class="wood-card">
                        <div class="wood-icon">🖌️</div>
                        <h4>Polyurethane</h4>
                        <p>Durable synthetic finishes for high-wear surfaces</p>
                    </div>
                </div>

                <h4>Stained Finishes</h4>
                <ul>
                    <li><strong>Wood Stains:</strong> Enhance natural color or change wood hue</li>
                    <li><strong>Gel Stains:</strong> Thick stains for even color on difficult woods</li>
                    <li><strong>Water-Based Stains:</strong> Low odor, quick drying options</li>
                    <li><strong>Oil-Based Stains:</strong> Deep penetration and rich color</li>
                </ul>

                <h4>Painted Finishes</h4>
                <ul>
                    <li><strong>Milk Paint:</strong> Traditional, matte finish with authentic look</li>
                    <li><strong>Latex Paint:</strong> Modern water-based paints in various sheens</li>
                    <li><strong>Enamel Paint:</strong> Hard, durable finish for kitchen cabinets</li>
                    <li><strong>Chalk Paint:</strong> Matte finish perfect for distressed looks</li>
                </ul>

                <h3>Finish Application</h3>

                <div class="workflow-step">
                    <h4>🎨 Applying Finishes</h4>
                    <ol>
                        <li>Select objects with base wood material applied</li>
                        <li>Open Finish Library in Materials panel</li>
                        <li>Browse finish categories or search for specific finishes</li>
                        <li>Preview finish over base wood material</li>
                        <li>Adjust finish intensity and transparency if needed</li>
                        <li>Apply finish to selected objects</li>
                        <li>Review result in 3D viewer under different lighting</li>
                    </ol>
                </div>

                <h3>Finish Properties</h3>

                <h4>Visual Properties</h4>
                <ul>
                    <li><strong>Gloss Level:</strong> Matte, satin, semi-gloss, or high-gloss</li>
                    <li><strong>Color Enhancement:</strong> How finish affects base wood color</li>
                    <li><strong>Transparency:</strong> Allows base wood grain to show through</li>
                    <li><strong>Surface Texture:</strong> Smooth, textured, or patterned appearance</li>
                </ul>

                <h4>Performance Properties</h4>
                <ul>
                    <li><strong>Durability:</strong> Resistance to wear, moisture, and chemicals</li>
                    <li><strong>UV Resistance:</strong> Protection against sun damage and fading</li>
                    <li><strong>Application Difficulty:</strong> Ease of application for DIY users</li>
                    <li><strong>Recoat Time:</strong> Time between coats for best results</li>
                </ul>

                <div class="image-placeholder">
                    [Image: finishes-comparison.png]
                    <br>Figure 3: Different finishes applied to the same wood species
                </div>
            </div>

            <div class="section" id="material-projection">
                <h2>Material Mapping and Projection</h2>

                <p>Material mapping controls how textures are applied to your 3D objects. Proper mapping ensures that wood grain appears realistic and scaled appropriately, just as proper wood selection and grain direction affect the appearance of your physical projects.</p>

                <h3>Mapping Types</h3>

                <h4>Planar Mapping</h4>
                <p>Projects material flat onto surfaces, similar to wrapping paper:</p>
                <ul>
                    <li><strong>Best for:</strong> Flat surfaces, panels, tabletops</li>
                    <li><strong>Grain Direction:</strong> Consistent across entire surface</li>
                    <li><strong>Scaling:</strong> Easy to control grain size and repetition</li>
                </ul>

                <h4>Cylindrical Mapping</h4>
                <p>Wraps material around curved surfaces:</p>
                <ul>
                    <li><strong>Best for:</strong> Round legs, cylinders, curved elements</li>
                    <li><strong>Seam Placement:</strong> Control where material edges meet</li>
                    <li><strong>Rotation:</strong> Adjust grain direction around circumference</li>
                </ul>

                <h4>Box Mapping</h4>
                <p>Projects material from six directions simultaneously:</p>
                <ul>
                    <li><strong>Best for:</strong> Box-like objects, cabinets, drawers</li>
                    <li><strong>Consistency:</strong> Maintains grain direction across edges</li>
                    <li><strong>Corner Treatment:</strong> How material appears at corners</li>
                </ul>

                <h3>Advanced Mapping Controls</h3>

                <h4>Texture Scaling</h4>
                <ul>
                    <li><strong>X Scale:</strong> Grain frequency left-to-right</li>
                    <li><strong>Y Scale:</strong> Grain frequency front-to-back</li>
                    <li><strong>Z Scale:</strong> Grain frequency top-to-bottom (for 3D mapping)</li>
                    <li><strong>Lock Aspect:</strong> Maintain proportional scaling</li>
                </ul>

                <h4>Texture Offset</h4>
                <ul>
                    <li><strong>Position Offset:</strong> Move texture position on surface</li>
                    <li><strong>Rotation Offset:</strong> Rotate texture orientation</li>
                    <li><strong>Tiling:</strong> Repeat texture pattern across surface</li>
                    <li><strong>Mirror:</strong> Flip texture orientation</li>
                </ul>

                <div class="note">
                    <strong>📐 Mapping Best Practice:</strong> Test material mapping on simple objects before applying to complex assemblies. Adjust scaling and rotation until grain appears natural and appropriately sized. Remember that different viewing distances may require different texture scales.
                </div>

                <h3>Grain Direction Guidelines</h3>
                <p>Proper grain direction enhances realism and matches physical woodworking practices:</p>

                <ul>
                    <li><strong>Tabletops:</strong> Grain typically runs lengthwise</li>
                    <li><strong>Vertical Elements:</strong> Grain runs vertically for visual appeal</li>
                    <li><strong>Frame Members:</strong> Grain aligns with longest dimension</li>
                    <li><strong>Decorative Elements:</strong> Grain can run in any direction for effect</li>
                </ul>

                <div class="tip">
                    <strong>💡 Grain Direction Tip:</strong> Match your digital grain direction to how you would arrange lumber in the physical build. This consistency helps with both visualization and material planning.
                </div>
            </div>

            <div class="section" id="batch-application">
                <h2>Batch Material Application</h2>

                <p>When working on complex projects with many components, Digital Workshop provides efficient tools for applying materials to multiple objects simultaneously. This is like using lumber templates or jigs in your workshop - it ensures consistency and saves time.</p>

                <h3>Bulk Material Operations</h3>

                <h4>Multi-Object Selection</h4>
                <div class="workflow-step">
                    <h4>⚡ Batch Application Process</h4>
                    <ol>
                        <li>Select all objects that should receive the same material</li>
                        <li>Open Materials panel and choose desired material</li>
                        <li>Click "Apply to Selection" or use context menu</li>
                        <li>Review results and adjust if necessary</li>
                        <li>Save material settings for future use</li>
                    </ol>
                </div>

                <h4>Smart Grouping</h4>
                <ul>
                    <li><strong>By Function:</strong> All legs, all shelves, all doors</li>
                    <li><strong>By Material Type:</strong> All hardwood pieces, all sheet goods</li>
                    <li><strong>By Project Phase:</strong> Materials for different construction stages</li>
                    <li><strong>By Finish Schedule:</strong> Objects receiving same finish treatment</li>
                </ul>

                <h3>Material Templates</h3>

                <h4>Creating Templates</h4>
                <p>Save material combinations for reuse across projects:</p>
                <ul>
                    <li><strong>Complete Finish Schedules:</strong> Base material plus final finish</li>
                    <li><strong>Species Combinations:</strong> Multiple woods used together</li>
                    <li><strong>Project-Specific Sets:</strong> Materials for specific project types</li>
                    <li><strong>Client Preferences:</strong> Material sets for different customers</li>
                </ul>

                <h4>Template Management</h4>
                <ul>
                    <li><strong>Organization:</strong> Folder structure for easy template access</li>
                    <li><strong>Version Control:</strong> Track template changes over time</li>
                    <li><strong>Sharing:</strong> Export templates to share with collaborators</li>
                    <li><strong>Backup:</strong> Regular backups of custom templates</li>
                </ul>

                <div class="warning">
                    <strong>⚠️ Batch Application Caution:</strong> Always preview material changes before applying to large selections. Test on a few objects first, especially when working with new materials or complex models. Batch changes affect multiple objects and can be difficult to undo.
                </div>
            </div>

            <div class="section" id="material-library">
                <h2>Managing Your Material Library</h2>

                <p>As you work on various projects, you'll build a collection of materials that you use frequently. Digital Workshop provides tools to organize, maintain, and expand your material library, keeping it as well-organized as your physical lumber storage.</p>

                <h3>Library Organization</h3>

                <h4>Folder Structure</h4>
                <div class="workflow-step">
                    <h4>📁 Organizing Your Material Library</h4>
                    <ol>
                        <li>Create main categories (Hardwoods, Softwoods, Finishes, etc.)</li>
                        <li>Subdivide by species or finish type</li>
                        <li>Add project-specific folders for special materials</li>
                        <li>Organize frequently used materials at top level</li>
                        <li>Archive rarely used materials to deeper folders</li>
                    </ol>
                </div>

                <h4>Material Naming Conventions</h4>
                <p>Consistent naming makes materials easy to find and use:</p>
                <ul>
                    <li><strong>Wood Species:</strong> "Oak_White_Natural" or "Cherry_Black_Oil_Finish"</li>
                    <li><strong>Finish Type:</strong> Include finish type in name</li>
                    <li><strong>Project Specific:</strong> "Project_Kitchen_Cabinet_Oak"</li>
                    <li><strong>Custom Variations:</strong> "Oak_White_Dark_Stain_v2"</li>
                </ul>

                <h3>Library Maintenance</h3>

                <h4>Regular Maintenance Tasks</h4>
                <ul>
                    <li><strong>Remove Duplicates:</strong> Delete redundant materials</li>
                    <li><strong>Update Materials:</strong> Refresh materials with improved textures</li>
                    <li><strong>Archive Old:</strong> Move deprecated materials to archive folder</li>
                    <li><strong>Backup Library:</strong> Regular backups of custom materials</li>
                    <li><strong>Update Properties:</strong> Keep cost and availability information current</li>
                </ul>

                <h4>Quality Control</h4>
                <ul>
                    <li><strong>Texture Quality:</strong> Ensure all textures are high resolution</li>
                    <li><strong>Accurate Colors:</strong> Verify material colors match real-world equivalents</li>
                    <li><strong>Consistent Properties:</strong> Maintain accurate hardness and cost data</li>
                    <li><strong>Complete Information:</strong> Add missing descriptions and usage notes</li>
                </ul>

                <h3>Sharing and Collaboration</h3>

                <h4>Material Sharing</h4>
                <ul>
                    <li><strong>Export Materials:</strong> Share custom materials with colleagues</li>
                    <li><strong>Import Libraries:</strong> Use materials from other users</li>
                    <li><strong>Version Control:</strong> Track changes to shared materials</li>
                    <li><strong>Community Resources:</strong> Access public material libraries</li>
                </ul>

                <h4>Project Material Documentation</h4>
                <ul>
                    <li><strong>Material Lists:</strong> Generate complete material lists for projects</li>
                    <li><strong>Cost Estimates:</strong> Calculate material costs using library pricing</li>
                    <li><strong>Supplier Information:</strong> Track where materials can be sourced</li>
                    <li><strong>Lead Times:</strong> Note material availability and ordering requirements</li>
                </ul>

                <div class="image-placeholder">
                    [Image: material-library-organization.png]
                    <br>Figure 4: Well-organized material library structure
                </div>

                <h3>Best Practices for Material Management</h3>

                <div class="note">
                    <strong>📋 Material Management Best Practices:</strong>
                    <ul>
                        <li>Start with Digital Workshop's built-in materials before creating custom ones</li>
                        <li>Use consistent naming conventions to make materials easy to find</li>
                        <li>Organize materials in logical folders that match your workflow</li>
                        <li>Preview materials thoroughly before applying to important projects</li>
                        <li>Keep frequently used materials easily accessible</li>
                        <li>Document custom materials with notes about usage and properties</li>
                        <li>Regularly backup your custom material library</li>
                        <li>Share useful materials with the Digital Workshop community</li>
                        <li>Update material properties as you learn more about different species</li>
                        <li>Use material templates for consistent application across projects</li>
                    </ul>
                </div>

                <p>Digital Workshop's materials system transforms your digital designs from simple geometric shapes into realistic representations of your intended finished pieces. By carefully selecting and applying materials, you can visualize how different wood species and finishes will interact with your designs, make informed material choices, and confidently plan your projects.</p>

                <p>Just as selecting the right lumber is crucial to successful woodworking, choosing appropriate digital materials is essential for effective project planning and visualization. Take time to explore the material library, experiment with different combinations, and build a collection of materials that reflects your design preferences and typical project requirements.</p>

                <p>Remember that the goal of the materials system is to help you create better physical pieces. Use it to explore wood combinations, test different finishes, and plan material purchases more effectively. The time you invest in understanding and organizing your digital material library will be repaid through improved design quality, better client communication, and more efficient project execution.</p>
            </div>

            <div style="text-align: center; margin-top: 50px;">
                <a href="index.html" class="btn back-link">← Back to Main Index</a>
                <a href="3d-viewer.html" class="btn">← Previous: 3D Model Viewer</a>
                <a href="gcode-previewer.html" class="btn">Next: G-Code Previewer →</a>
            </div>
        </div>
    </div>
</body>
</html>