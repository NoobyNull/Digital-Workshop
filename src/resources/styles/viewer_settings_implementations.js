/**
 * 3D Viewer Settings Implementation for 3D-MM Application
 * 
 * This JavaScript file demonstrates how to implement the 3D viewer settings panel
 * with controls for lighting, camera position, colors, and other settings.
 */

// ================================
// VIEWER SETTINGS MANAGER
// ================================

/**
 * Viewer settings manager for managing 3D viewer settings
 */
class ViewerSettingsManager {
    constructor(viewer) {
        this.viewer = viewer;
        this.settings = this.getDefaultSettings();
        this.callbacks = {};
        this.panel = null;
        this.isVisible = false;
    }
    
    /**
     * Get default viewer settings
     * @returns {Object} Default settings
     */
    getDefaultSettings() {
        return {
            // Lighting settings
            lighting: {
                ambientIntensity: 0.3,
                directionalIntensity: 0.7,
                directionalColor: '#ffffff',
                directionalPosition: { x: 1, y: 1, z: 1 },
                pointIntensity: 0.5,
                pointColor: '#ffffff',
                pointPosition: { x: 0, y: 5, z: 0 }
            },
            
            // Camera settings
            camera: {
                position: { x: 0, y: 0, z: 5 },
                target: { x: 0, y: 0, z: 0 },
                up: { x: 0, y: 1, z: 0 },
                fov: 45,
                near: 0.1,
                far: 1000
            },
            
            // Color settings
            colors: {
                background: '#f0f0f0',
                model: '#cccccc',
                wireframe: '#000000',
                selected: '#0078d4'
            },
            
            // Rendering settings
            rendering: {
                mode: 'solid', // solid, wireframe, points
                showAxes: true,
                showGrid: true,
                showBoundingBox: false,
                transparency: 1.0,
                opacity: 1.0
            },
            
            // Transform settings
            transform: {
                position: { x: 0, y: 0, z: 0 },
                rotation: { x: 0, y: 0, z: 0 },
                scale: { x: 1, y: 1, z: 1 }
            },
            
            // Visibility settings
            visibility: {
                ucs: true,
                axes: true,
                grid: true,
                boundingBox: false,
                wireframe: false
            }
        };
    }
    
    /**
     * Create settings panel
     * @param {HTMLElement} container - Container element
     * @returns {HTMLElement} Settings panel element
     */
    createSettingsPanel(container) {
        // Create panel element
        this.panel = document.createElement('div');
        this.panel.className = 'viewer-settings-panel';
        
        // Create header
        const header = this.createPanelHeader();
        this.panel.appendChild(header);
        
        // Create content
        const content = this.createPanelContent();
        this.panel.appendChild(content);
        
        // Add to container
        container.appendChild(this.panel);
        
        return this.panel;
    }
    
    /**
     * Create panel header
     * @returns {HTMLElement} Header element
     */
    createPanelHeader() {
        // Create header element
        const header = document.createElement('div');
        header.className = 'viewer-settings-header';
        
        // Create title
        const title = document.createElement('div');
        title.className = 'viewer-settings-title';
        title.textContent = 'Viewer Settings';
        header.appendChild(title);
        
        // Create toggle button
        const toggleButton = document.createElement('button');
        toggleButton.className = 'viewer-settings-toggle';
        toggleButton.innerHTML = '▼';
        toggleButton.setAttribute('aria-label', 'Toggle settings panel');
        toggleButton.addEventListener('click', () => {
            this.togglePanel();
        });
        header.appendChild(toggleButton);
        
        return header;
    }
    
    /**
     * Create panel content
     * @returns {HTMLElement} Content element
     */
    createPanelContent() {
        // Create content element
        const content = document.createElement('div');
        content.className = 'viewer-settings-content';
        
        // Create lighting section
        const lightingSection = this.createLightingSection();
        content.appendChild(lightingSection);
        
        // Create camera section
        const cameraSection = this.createCameraSection();
        content.appendChild(cameraSection);
        
        // Create colors section
        const colorsSection = this.createColorsSection();
        content.appendChild(colorsSection);
        
        // Create rendering section
        const renderingSection = this.createRenderingSection();
        content.appendChild(renderingSection);
        
        // Create visibility section
        const visibilitySection = this.createVisibilitySection();
        content.appendChild(visibilitySection);
        
        // Create transform section
        const transformSection = this.createTransformSection();
        content.appendChild(transformSection);
        
        // Create advanced settings section
        const advancedSection = this.createAdvancedSection();
        content.appendChild(advancedSection);
        
        return content;
    }
    
    /**
     * Create lighting section
     * @returns {HTMLElement} Lighting section element
     */
    createLightingSection() {
        // Create section element
        const section = document.createElement('div');
        section.className = 'settings-section';
        
        // Create header
        const header = document.createElement('div');
        header.className = 'settings-section-header';
        header.textContent = 'Lighting';
        section.appendChild(header);
        
        // Create content
        const content = document.createElement('div');
        content.className = 'settings-section-content';
        
        // Create ambient intensity control
        const ambientControl = this.createSliderControl(
            'Ambient Intensity',
            this.settings.lighting.ambientIntensity,
            0, 1, 0.01,
            (value) => {
                this.settings.lighting.ambientIntensity = value;
                this.updateLighting();
            }
        );
        content.appendChild(ambientControl);
        
        // Create directional intensity control
        const directionalControl = this.createSliderControl(
            'Directional Intensity',
            this.settings.lighting.directionalIntensity,
            0, 1, 0.01,
            (value) => {
                this.settings.lighting.directionalIntensity = value;
                this.updateLighting();
            }
        );
        content.appendChild(directionalControl);
        
        // Create directional color control
        const directionalColorControl = this.createColorControl(
            'Directional Color',
            this.settings.lighting.directionalColor,
            (color) => {
                this.settings.lighting.directionalColor = color;
                this.updateLighting();
            }
        );
        content.appendChild(directionalColorControl);
        
        // Create point intensity control
        const pointControl = this.createSliderControl(
            'Point Intensity',
            this.settings.lighting.pointIntensity,
            0, 1, 0.01,
            (value) => {
                this.settings.lighting.pointIntensity = value;
                this.updateLighting();
            }
        );
        content.appendChild(pointControl);
        
        // Create point color control
        const pointColorControl = this.createColorControl(
            'Point Color',
            this.settings.lighting.pointColor,
            (color) => {
                this.settings.lighting.pointColor = color;
                this.updateLighting();
            }
        );
        content.appendChild(pointColorControl);
        
        section.appendChild(content);
        
        return section;
    }
    
    /**
     * Create camera section
     * @returns {HTMLElement} Camera section element
     */
    createCameraSection() {
        // Create section element
        const section = document.createElement('div');
        section.className = 'settings-section';
        
        // Create header
        const header = document.createElement('div');
        header.className = 'settings-section-header';
        header.textContent = 'Camera';
        section.appendChild(header);
        
        // Create content
        const content = document.createElement('div');
        content.className = 'settings-section-content';
        
        // Create position controls
        const positionLabel = document.createElement('div');
        positionLabel.textContent = 'Position';
        positionLabel.style.fontWeight = 'bold';
        positionLabel.style.marginBottom = '4px';
        content.appendChild(positionLabel);
        
        // X position control
        const xPosControl = this.createSliderControl(
            'X',
            this.settings.camera.position.x,
            -10, 10, 0.1,
            (value) => {
                this.settings.camera.position.x = value;
                this.updateCamera();
            }
        );
        content.appendChild(xPosControl);
        
        // Y position control
        const yPosControl = this.createSliderControl(
            'Y',
            this.settings.camera.position.y,
            -10, 10, 0.1,
            (value) => {
                this.settings.camera.position.y = value;
                this.updateCamera();
            }
        );
        content.appendChild(yPosControl);
        
        // Z position control
        const zPosControl = this.createSliderControl(
            'Z',
            this.settings.camera.position.z,
            -10, 10, 0.1,
            (value) => {
                this.settings.camera.position.z = value;
                this.updateCamera();
            }
        );
        content.appendChild(zPosControl);
        
        // Create FOV control
        const fovControl = this.createSliderControl(
            'FOV',
            this.settings.camera.fov,
            10, 120, 1,
            (value) => {
                this.settings.camera.fov = value;
                this.updateCamera();
            }
        );
        content.appendChild(fovControl);
        
        // Create preset buttons
        const presetLabel = document.createElement('div');
        presetLabel.textContent = 'Presets';
        presetLabel.style.fontWeight = 'bold';
        presetLabel.style.marginTop = '8px';
        presetLabel.style.marginBottom = '4px';
        content.appendChild(presetLabel);
        
        const presetButtons = document.createElement('div');
        presetButtons.className = 'camera-preset-buttons';
        
        // Front preset
        const frontButton = document.createElement('button');
        frontButton.className = 'camera-preset-button';
        frontButton.textContent = 'Front';
        frontButton.addEventListener('click', () => {
            this.setCameraPreset('front');
        });
        presetButtons.appendChild(frontButton);
        
        // Back preset
        const backButton = document.createElement('button');
        backButton.className = 'camera-preset-button';
        backButton.textContent = 'Back';
        backButton.addEventListener('click', () => {
            this.setCameraPreset('back');
        });
        presetButtons.appendChild(backButton);
        
        // Left preset
        const leftButton = document.createElement('button');
        leftButton.className = 'camera-preset-button';
        leftButton.textContent = 'Left';
        leftButton.addEventListener('click', () => {
            this.setCameraPreset('left');
        });
        presetButtons.appendChild(leftButton);
        
        // Right preset
        const rightButton = document.createElement('button');
        rightButton.className = 'camera-preset-button';
        rightButton.textContent = 'Right';
        rightButton.addEventListener('click', () => {
            this.setCameraPreset('right');
        });
        presetButtons.appendChild(rightButton);
        
        // Top preset
        const topButton = document.createElement('button');
        topButton.className = 'camera-preset-button';
        topButton.textContent = 'Top';
        topButton.addEventListener('click', () => {
            this.setCameraPreset('top');
        });
        presetButtons.appendChild(topButton);
        
        // Bottom preset
        const bottomButton = document.createElement('button');
        bottomButton.className = 'camera-preset-button';
        bottomButton.textContent = 'Bottom';
        bottomButton.addEventListener('click', () => {
            this.setCameraPreset('bottom');
        });
        presetButtons.appendChild(bottomButton);
        
        // Isometric preset
        const isoButton = document.createElement('button');
        isoButton.className = 'camera-preset-button';
        isoButton.textContent = 'Isometric';
        isoButton.addEventListener('click', () => {
            this.setCameraPreset('isometric');
        });
        presetButtons.appendChild(isoButton);
        
        content.appendChild(presetButtons);
        
        section.appendChild(content);
        
        return section;
    }
    
    /**
     * Create colors section
     * @returns {HTMLElement} Colors section element
     */
    createColorsSection() {
        // Create section element
        const section = document.createElement('div');
        section.className = 'settings-section';
        
        // Create header
        const header = document.createElement('div');
        header.className = 'settings-section-header';
        header.textContent = 'Colors';
        section.appendChild(header);
        
        // Create content
        const content = document.createElement('div');
        content.className = 'settings-section-content';
        
        // Create background color control
        const backgroundColorControl = this.createColorControl(
            'Background',
            this.settings.colors.background,
            (color) => {
                this.settings.colors.background = color;
                this.updateColors();
            }
        );
        content.appendChild(backgroundColorControl);
        
        // Create model color control
        const modelColorControl = this.createColorControl(
            'Model',
            this.settings.colors.model,
            (color) => {
                this.settings.colors.model = color;
                this.updateColors();
            }
        );
        content.appendChild(modelColorControl);
        
        // Create wireframe color control
        const wireframeColorControl = this.createColorControl(
            'Wireframe',
            this.settings.colors.wireframe,
            (color) => {
                this.settings.colors.wireframe = color;
                this.updateColors();
            }
        );
        content.appendChild(wireframeColorControl);
        
        // Create selected color control
        const selectedColorControl = this.createColorControl(
            'Selected',
            this.settings.colors.selected,
            (color) => {
                this.settings.colors.selected = color;
                this.updateColors();
            }
        );
        content.appendChild(selectedColorControl);
        
        section.appendChild(content);
        
        return section;
    }
    
    /**
     * Create rendering section
     * @returns {HTMLElement} Rendering section element
     */
    createRenderingSection() {
        // Create section element
        const section = document.createElement('div');
        section.className = 'settings-section';
        
        // Create header
        const header = document.createElement('div');
        header.className = 'settings-section-header';
        header.textContent = 'Rendering';
        section.appendChild(header);
        
        // Create content
        const content = document.createElement('div');
        content.className = 'settings-section-content';
        
        // Create rendering mode selector
        const modeLabel = document.createElement('div');
        modeLabel.textContent = 'Mode';
        modeLabel.style.fontWeight = 'bold';
        modeLabel.style.marginBottom = '4px';
        content.appendChild(modeLabel);
        
        const modeSelector = document.createElement('div');
        modeSelector.className = 'rendering-mode-selector';
        
        // Solid mode
        const solidOption = document.createElement('div');
        solidOption.className = 'rendering-mode-option';
        
        const solidRadio = document.createElement('input');
        solidRadio.type = 'radio';
        solidRadio.name = 'rendering-mode';
        solidRadio.id = 'rendering-mode-solid';
        solidRadio.checked = this.settings.rendering.mode === 'solid';
        solidRadio.addEventListener('change', () => {
            this.settings.rendering.mode = 'solid';
            this.updateRendering();
        });
        solidOption.appendChild(solidRadio);
        
        const solidLabel = document.createElement('label');
        solidLabel.htmlFor = 'rendering-mode-solid';
        solidLabel.className = 'rendering-mode-label';
        solidLabel.textContent = 'Solid';
        solidOption.appendChild(solidLabel);
        
        modeSelector.appendChild(solidOption);
        
        // Wireframe mode
        const wireframeOption = document.createElement('div');
        wireframeOption.className = 'rendering-mode-option';
        
        const wireframeRadio = document.createElement('input');
        wireframeRadio.type = 'radio';
        wireframeRadio.name = 'rendering-mode';
        wireframeRadio.id = 'rendering-mode-wireframe';
        wireframeRadio.checked = this.settings.rendering.mode === 'wireframe';
        wireframeRadio.addEventListener('change', () => {
            this.settings.rendering.mode = 'wireframe';
            this.updateRendering();
        });
        wireframeOption.appendChild(wireframeRadio);
        
        const wireframeLabel = document.createElement('label');
        wireframeLabel.htmlFor = 'rendering-mode-wireframe';
        wireframeLabel.className = 'rendering-mode-label';
        wireframeLabel.textContent = 'Wireframe';
        wireframeOption.appendChild(wireframeLabel);
        
        modeSelector.appendChild(wireframeOption);
        
        // Points mode
        const pointsOption = document.createElement('div');
        pointsOption.className = 'rendering-mode-option';
        
        const pointsRadio = document.createElement('input');
        pointsRadio.type = 'radio';
        pointsRadio.name = 'rendering-mode';
        pointsRadio.id = 'rendering-mode-points';
        pointsRadio.checked = this.settings.rendering.mode === 'points';
        pointsRadio.addEventListener('change', () => {
            this.settings.rendering.mode = 'points';
            this.updateRendering();
        });
        pointsOption.appendChild(pointsRadio);
        
        const pointsLabel = document.createElement('label');
        pointsLabel.htmlFor = 'rendering-mode-points';
        pointsLabel.className = 'rendering-mode-label';
        pointsLabel.textContent = 'Points';
        pointsOption.appendChild(pointsLabel);
        
        modeSelector.appendChild(pointsOption);
        
        content.appendChild(modeSelector);
        
        // Create transparency control
        const transparencyControl = this.createSliderControl(
            'Transparency',
            this.settings.rendering.transparency,
            0, 1, 0.01,
            (value) => {
                this.settings.rendering.transparency = value;
                this.updateRendering();
            }
        );
        content.appendChild(transparencyControl);
        
        section.appendChild(content);
        
        return section;
    }
    
    /**
     * Create visibility section
     * @returns {HTMLElement} Visibility section element
     */
    createVisibilitySection() {
        // Create section element
        const section = document.createElement('div');
        section.className = 'settings-section';
        
        // Create header
        const header = document.createElement('div');
        header.className = 'settings-section-header';
        header.textContent = 'Visibility';
        section.appendChild(header);
        
        // Create content
        const content = document.createElement('div');
        content.className = 'settings-section-content';
        
        // Create UCS visibility control
        const ucsControl = this.createCheckboxControl(
            'UCS',
            this.settings.visibility.ucs,
            (checked) => {
                this.settings.visibility.ucs = checked;
                this.updateVisibility();
            }
        );
        content.appendChild(ucsControl);
        
        // Create axes visibility control
        const axesControl = this.createCheckboxControl(
            'Axes',
            this.settings.visibility.axes,
            (checked) => {
                this.settings.visibility.axes = checked;
                this.updateVisibility();
            }
        );
        content.appendChild(axesControl);
        
        // Create grid visibility control
        const gridControl = this.createCheckboxControl(
            'Grid',
            this.settings.visibility.grid,
            (checked) => {
                this.settings.visibility.grid = checked;
                this.updateVisibility();
            }
        );
        content.appendChild(gridControl);
        
        // Create bounding box visibility control
        const boundingBoxControl = this.createCheckboxControl(
            'Bounding Box',
            this.settings.visibility.boundingBox,
            (checked) => {
                this.settings.visibility.boundingBox = checked;
                this.updateVisibility();
            }
        );
        content.appendChild(boundingBoxControl);
        
        // Create wireframe visibility control
        const wireframeControl = this.createCheckboxControl(
            'Wireframe',
            this.settings.visibility.wireframe,
            (checked) => {
                this.settings.visibility.wireframe = checked;
                this.updateVisibility();
            }
        );
        content.appendChild(wireframeControl);
        
        section.appendChild(content);
        
        return section;
    }
    
    /**
     * Create transform section
     * @returns {HTMLElement} Transform section element
     */
    createTransformSection() {
        // Create section element
        const section = document.createElement('div');
        section.className = 'settings-section';
        
        // Create header
        const header = document.createElement('div');
        header.className = 'settings-section-header';
        header.textContent = 'Transform';
        section.appendChild(header);
        
        // Create content
        const content = document.createElement('div');
        content.className = 'settings-section-content';
        
        // Create position controls
        const positionLabel = document.createElement('div');
        positionLabel.textContent = 'Position';
        positionLabel.style.fontWeight = 'bold';
        positionLabel.style.marginBottom = '4px';
        content.appendChild(positionLabel);
        
        // X position control
        const xPosControl = this.createSliderControl(
            'X',
            this.settings.transform.position.x,
            -10, 10, 0.1,
            (value) => {
                this.settings.transform.position.x = value;
                this.updateTransform();
            }
        );
        content.appendChild(xPosControl);
        
        // Y position control
        const yPosControl = this.createSliderControl(
            'Y',
            this.settings.transform.position.y,
            -10, 10, 0.1,
            (value) => {
                this.settings.transform.position.y = value;
                this.updateTransform();
            }
        );
        content.appendChild(yPosControl);
        
        // Z position control
        const zPosControl = this.createSliderControl(
            'Z',
            this.settings.transform.position.z,
            -10, 10, 0.1,
            (value) => {
                this.settings.transform.position.z = value;
                this.updateTransform();
            }
        );
        content.appendChild(zPosControl);
        
        // Create rotation controls
        const rotationLabel = document.createElement('div');
        rotationLabel.textContent = 'Rotation';
        rotationLabel.style.fontWeight = 'bold';
        rotationLabel.style.marginTop = '8px';
        rotationLabel.style.marginBottom = '4px';
        content.appendChild(rotationLabel);
        
        // X rotation control
        const xRotControl = this.createSliderControl(
            'X',
            this.settings.transform.rotation.x,
            0, 360, 1,
            (value) => {
                this.settings.transform.rotation.x = value;
                this.updateTransform();
            }
        );
        content.appendChild(xRotControl);
        
        // Y rotation control
        const yRotControl = this.createSliderControl(
            'Y',
            this.settings.transform.rotation.y,
            0, 360, 1,
            (value) => {
                this.settings.transform.rotation.y = value;
                this.updateTransform();
            }
        );
        content.appendChild(yRotControl);
        
        // Z rotation control
        const zRotControl = this.createSliderControl(
            'Z',
            this.settings.transform.rotation.z,
            0, 360, 1,
            (value) => {
                this.settings.transform.rotation.z = value;
                this.updateTransform();
            }
        );
        content.appendChild(zRotControl);
        
        // Create scale controls
        const scaleLabel = document.createElement('div');
        scaleLabel.textContent = 'Scale';
        scaleLabel.style.fontWeight = 'bold';
        scaleLabel.style.marginTop = '8px';
        scaleLabel.style.marginBottom = '4px';
        content.appendChild(scaleLabel);
        
        // X scale control
        const xScaleControl = this.createSliderControl(
            'X',
            this.settings.transform.scale.x,
            0.1, 5, 0.1,
            (value) => {
                this.settings.transform.scale.x = value;
                this.updateTransform();
            }
        );
        content.appendChild(xScaleControl);
        
        // Y scale control
        const yScaleControl = this.createSliderControl(
            'Y',
            this.settings.transform.scale.y,
            0.1, 5, 0.1,
            (value) => {
                this.settings.transform.scale.y = value;
                this.updateTransform();
            }
        );
        content.appendChild(yScaleControl);
        
        // Z scale control
        const zScaleControl = this.createSliderControl(
            'Z',
            this.settings.transform.scale.z,
            0.1, 5, 0.1,
            (value) => {
                this.settings.transform.scale.z = value;
                this.updateTransform();
            }
        );
        content.appendChild(zScaleControl);
        
        // Create reset button
        const resetButton = document.createElement('button');
        resetButton.className = 'transform-reset-button';
        resetButton.textContent = 'Reset Transform';
        resetButton.addEventListener('click', () => {
            this.resetTransform();
        });
        content.appendChild(resetButton);
        
        section.appendChild(content);
        
        return section;
    }
    
    /**
     * Create advanced section
     * @returns {HTMLElement} Advanced section element
     */
    createAdvancedSection() {
        // Create section element
        const section = document.createElement('div');
        section.className = 'settings-section';
        
        // Create toggle
        const toggle = document.createElement('div');
        toggle.className = 'advanced-settings-toggle';
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = 'advanced-settings-toggle';
        checkbox.addEventListener('change', () => {
            const content = section.querySelector('.advanced-settings-content');
            if (checkbox.checked) {
                content.classList.add('show');
            } else {
                content.classList.remove('show');
            }
        });
        toggle.appendChild(checkbox);
        
        const label = document.createElement('label');
        label.htmlFor = 'advanced-settings-toggle';
        label.className = 'advanced-settings-label';
        label.textContent = 'Advanced Settings';
        toggle.appendChild(label);
        
        section.appendChild(toggle);
        
        // Create content
        const content = document.createElement('div');
        content.className = 'advanced-settings-content';
        
        // Add advanced settings here
        // For example, performance settings, debug options, etc.
        
        section.appendChild(content);
        
        return section;
    }
    
    /**
     * Create slider control
     * @param {string} label - Control label
     * @param {number} value - Initial value
     * @param {number} min - Minimum value
     * @param {number} max - Maximum value
     * @param {number} step - Step value
     * @param {Function} callback - Change callback
     * @returns {HTMLElement} Control element
     */
    createSliderControl(label, value, min, max, step, callback) {
        // Create control element
        const control = document.createElement('div');
        control.className = 'lighting-control';
        
        // Create label
        const labelElement = document.createElement('div');
        labelElement.className = 'lighting-control-label';
        labelElement.textContent = label;
        control.appendChild(labelElement);
        
        // Create slider
        const slider = document.createElement('input');
        slider.type = 'range';
        slider.min = min;
        slider.max = max;
        slider.step = step;
        slider.value = value;
        slider.className = 'lighting-control-slider';
        slider.addEventListener('input', () => {
            valueElement.textContent = parseFloat(slider.value).toFixed(2);
            callback(parseFloat(slider.value));
        });
        control.appendChild(slider);
        
        // Create value display
        const valueElement = document.createElement('div');
        valueElement.className = 'lighting-control-value';
        valueElement.textContent = value.toFixed(2);
        control.appendChild(valueElement);
        
        return control;
    }
    
    /**
     * Create color control
     * @param {string} label - Control label
     * @param {string} color - Initial color
     * @param {Function} callback - Change callback
     * @returns {HTMLElement} Control element
     */
    createColorControl(label, color, callback) {
        // Create control element
        const control = document.createElement('div');
        control.className = 'lighting-control';
        
        // Create label
        const labelElement = document.createElement('div');
        labelElement.className = 'lighting-control-label';
        labelElement.textContent = label;
        control.appendChild(labelElement);
        
        // Create color picker
        const colorPicker = document.createElement('input');
        colorPicker.type = 'color';
        colorPicker.value = color;
        colorPicker.className = 'color-picker';
        colorPicker.addEventListener('input', () => {
            callback(colorPicker.value);
        });
        control.appendChild(colorPicker);
        
        return control;
    }
    
    /**
     * Create checkbox control
     * @param {string} label - Control label
     * @param {boolean} checked - Initial checked state
     * @param {Function} callback - Change callback
     * @returns {HTMLElement} Control element
     */
    createCheckboxControl(label, checked, callback) {
        // Create control element
        const control = document.createElement('div');
        control.className = 'visibility-control';
        
        // Create label
        const labelElement = document.createElement('div');
        labelElement.className = 'visibility-control-label';
        labelElement.textContent = label;
        control.appendChild(labelElement);
        
        // Create checkbox
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.checked = checked;
        checkbox.className = 'visibility-control-checkbox';
        checkbox.addEventListener('change', () => {
            callback(checkbox.checked);
        });
        control.appendChild(checkbox);
        
        return control;
    }
    
    /**
     * Toggle panel visibility
     */
    togglePanel() {
        if (!this.panel) return;
        
        this.isVisible = !this.isVisible;
        
        const content = this.panel.querySelector('.viewer-settings-content');
        const toggleButton = this.panel.querySelector('.viewer-settings-toggle');
        
        if (this.isVisible) {
            content.style.display = 'flex';
            toggleButton.innerHTML = '▼';
        } else {
            content.style.display = 'none';
            toggleButton.innerHTML = '▶';
        }
    }
    
    /**
     * Set camera preset
     * @param {string} preset - Preset name
     */
    setCameraPreset(preset) {
        switch (preset) {
            case 'front':
                this.settings.camera.position = { x: 0, y: 0, z: 5 };
                this.settings.camera.target = { x: 0, y: 0, z: 0 };
                break;
            case 'back':
                this.settings.camera.position = { x: 0, y: 0, z: -5 };
                this.settings.camera.target = { x: 0, y: 0, z: 0 };
                break;
            case 'left':
                this.settings.camera.position = { x: -5, y: 0, z: 0 };
                this.settings.camera.target = { x: 0, y: 0, z: 0 };
                break;
            case 'right':
                this.settings.camera.position = { x: 5, y: 0, z: 0 };
                this.settings.camera.target = { x: 0, y: 0, z: 0 };
                break;
            case 'top':
                this.settings.camera.position = { x: 0, y: 5, z: 0 };
                this.settings.camera.target = { x: 0, y: 0, z: 0 };
                break;
            case 'bottom':
                this.settings.camera.position = { x: 0, y: -5, z: 0 };
                this.settings.camera.target = { x: 0, y: 0, z: 0 };
                break;
            case 'isometric':
                this.settings.camera.position = { x: 5, y: 5, z: 5 };
                this.settings.camera.target = { x: 0, y: 0, z: 0 };
                break;
        }
        
        this.updateCamera();
        this.updateCameraControls();
    }
    
    /**
     * Reset transform
     */
    resetTransform() {
        this.settings.transform = {
            position: { x: 0, y: 0, z: 0 },
            rotation: { x: 0, y: 0, z: 0 },
            scale: { x: 1, y: 1, z: 1 }
        };
        
        this.updateTransform();
        this.updateTransformControls();
    }
    
    /**
     * Update lighting
     */
    updateLighting() {
        // In a real implementation, this would update the lighting in the 3D viewer
        console.log('Updating lighting:', this.settings.lighting);
        
        // Trigger callback
        if (this.callbacks.lightingChange) {
            this.callbacks.lightingChange(this.settings.lighting);
        }
    }
    
    /**
     * Update camera
     */
    updateCamera() {
        // In a real implementation, this would update the camera in the 3D viewer
        console.log('Updating camera:', this.settings.camera);
        
        // Trigger callback
        if (this.callbacks.cameraChange) {
            this.callbacks.cameraChange(this.settings.camera);
        }
    }
    
    /**
     * Update colors
     */
    updateColors() {
        // In a real implementation, this would update the colors in the 3D viewer
        console.log('Updating colors:', this.settings.colors);
        
        // Trigger callback
        if (this.callbacks.colorsChange) {
            this.callbacks.colorsChange(this.settings.colors);
        }
    }
    
    /**
     * Update rendering
     */
    updateRendering() {
        // In a real implementation, this would update the rendering in the 3D viewer
        console.log('Updating rendering:', this.settings.rendering);
        
        // Trigger callback
        if (this.callbacks.renderingChange) {
            this.callbacks.renderingChange(this.settings.rendering);
        }
    }
    
    /**
     * Update visibility
     */
    updateVisibility() {
        // In a real implementation, this would update the visibility in the 3D viewer
        console.log('Updating visibility:', this.settings.visibility);
        
        // Trigger callback
        if (this.callbacks.visibilityChange) {
            this.callbacks.visibilityChange(this.settings.visibility);
        }
    }
    
    /**
     * Update transform
     */
    updateTransform() {
        // In a real implementation, this would update the transform in the 3D viewer
        console.log('Updating transform:', this.settings.transform);
        
        // Trigger callback
        if (this.callbacks.transformChange) {
            this.callbacks.transformChange(this.settings.transform);
        }
    }
    
    /**
     * Update camera controls
     */
    updateCameraControls() {
        if (!this.panel) return;
        
        // Update position sliders
        const xPosSlider = this.panel.querySelector('input[data-control="camera-x"]');
        if (xPosSlider) {
            xPosSlider.value = this.settings.camera.position.x;
            const valueElement = xPosSlider.nextElementSibling;
            if (valueElement) {
                valueElement.textContent = this.settings.camera.position.x.toFixed(1);
            }
        }
        
        const yPosSlider = this.panel.querySelector('input[data-control="camera-y"]');
        if (yPosSlider) {
            yPosSlider.value = this.settings.camera.position.y;
            const valueElement = yPosSlider.nextElementSibling;
            if (valueElement) {
                valueElement.textContent = this.settings.camera.position.y.toFixed(1);
            }
        }
        
        const zPosSlider = this.panel.querySelector('input[data-control="camera-z"]');
        if (zPosSlider) {
            zPosSlider.value = this.settings.camera.position.z;
            const valueElement = zPosSlider.nextElementSibling;
            if (valueElement) {
                valueElement.textContent = this.settings.camera.position.z.toFixed(1);
            }
        }
        
        // Update FOV slider
        const fovSlider = this.panel.querySelector('input[data-control="camera-fov"]');
        if (fovSlider) {
            fovSlider.value = this.settings.camera.fov;
            const valueElement = fovSlider.nextElementSibling;
            if (valueElement) {
                valueElement.textContent = this.settings.camera.fov.toFixed(0);
            }
        }
    }
    
    /**
     * Update transform controls
     */
    updateTransformControls() {
        if (!this.panel) return;
        
        // Update position sliders
        const xPosSlider = this.panel.querySelector('input[data-control="transform-x"]');
        if (xPosSlider) {
            xPosSlider.value = this.settings.transform.position.x;
            const valueElement = xPosSlider.nextElementSibling;
            if (valueElement) {
                valueElement.textContent = this.settings.transform.position.x.toFixed(1);
            }
        }
        
        const yPosSlider = this.panel.querySelector('input[data-control="transform-y"]');
        if (yPosSlider) {
            yPosSlider.value = this.settings.transform.position.y;
            const valueElement = yPosSlider.nextElementSibling;
            if (valueElement) {
                valueElement.textContent = this.settings.transform.position.y.toFixed(1);
            }
        }
        
        const zPosSlider = this.panel.querySelector('input[data-control="transform-z"]');
        if (zPosSlider) {
            zPosSlider.value = this.settings.transform.position.z;
            const valueElement = zPosSlider.nextElementSibling;
            if (valueElement) {
                valueElement.textContent = this.settings.transform.position.z.toFixed(1);
            }
        }
        
        // Update rotation sliders
        const xRotSlider = this.panel.querySelector('input[data-control="transform-rot-x"]');
        if (xRotSlider) {
            xRotSlider.value = this.settings.transform.rotation.x;
            const valueElement = xRotSlider.nextElementSibling;
            if (valueElement) {
                valueElement.textContent = this.settings.transform.rotation.x.toFixed(0);
            }
        }
        
        const yRotSlider = this.panel.querySelector('input[data-control="transform-rot-y"]');
        if (yRotSlider) {
            yRotSlider.value = this.settings.transform.rotation.y;
            const valueElement = yRotSlider.nextElementSibling;
            if (valueElement) {
                valueElement.textContent = this.settings.transform.rotation.y.toFixed(0);
            }
        }
        
        const zRotSlider = this.panel.querySelector('input[data-control="transform-rot-z"]');
        if (zRotSlider) {
            zRotSlider.value = this.settings.transform.rotation.z;
            const valueElement = zRotSlider.nextElementSibling;
            if (valueElement) {
                valueElement.textContent = this.settings.transform.rotation.z.toFixed(0);
            }
        }
        
        // Update scale sliders
        const xScaleSlider = this.panel.querySelector('input[data-control="transform-scale-x"]');
        if (xScaleSlider) {
            xScaleSlider.value = this.settings.transform.scale.x;
            const valueElement = xScaleSlider.nextElementSibling;
            if (valueElement) {
                valueElement.textContent = this.settings.transform.scale.x.toFixed(1);
            }
        }
        
        const yScaleSlider = this.panel.querySelector('input[data-control="transform-scale-y"]');
        if (yScaleSlider) {
            yScaleSlider.value = this.settings.transform.scale.y;
            const valueElement = yScaleSlider.nextElementSibling;
            if (valueElement) {
                valueElement.textContent = this.settings.transform.scale.y.toFixed(1);
            }
        }
        
        const zScaleSlider = this.panel.querySelector('input[data-control="transform-scale-z"]');
        if (zScaleSlider) {
            zScaleSlider.value = this.settings.transform.scale.z;
            const valueElement = zScaleSlider.nextElementSibling;
            if (valueElement) {
                valueElement.textContent = this.settings.transform.scale.z.toFixed(1);
            }
        }
    }
    
    /**
     * Add a callback for settings changes
     * @param {string} event - Event name
     * @param {Function} callback - Callback function
     */
    addCallback(event, callback) {
        if (!this.callbacks[event]) {
            this.callbacks[event] = [];
        }
        this.callbacks[event].push(callback);
    }
    
    /**
     * Remove a callback for settings changes
     * @param {string} event - Event name
     * @param {Function} callback - Callback function
     */
    removeCallback(event, callback) {
        if (this.callbacks[event]) {
            const index = this.callbacks[event].indexOf(callback);
            if (index > -1) {
                this.callbacks[event].splice(index, 1);
            }
        }
    }
    
    /**
     * Get current settings
     * @returns {Object} Current settings
     */
    getSettings() {
        return { ...this.settings };
    }
    
    /**
     * Set settings
     * @param {Object} settings - New settings
     */
    setSettings(settings) {
        // Merge settings
        this.settings = this.mergeSettings(this.settings, settings);
        
        // Update all controls
        this.updateCameraControls();
        this.updateTransformControls();
        
        // Apply settings
        this.updateLighting();
        this.updateCamera();
        this.updateColors();
        this.updateRendering();
        this.updateVisibility();
        this.updateTransform();
    }
    
    /**
     * Merge settings
     * @param {Object} target - Target settings
     * @param {Object} source - Source settings
     * @returns {Object} Merged settings
     */
    mergeSettings(target, source) {
        const result = { ...target };
        
        for (const key in source) {
            if (typeof source[key] === 'object' && source[key] !== null) {
                result[key] = this.mergeSettings(result[key] || {}, source[key]);
            } else {
                result[key] = source[key];
            }
        }
        
        return result;
    }
}

// Create global viewer settings manager
const viewerSettingsManager = new ViewerSettingsManager();

// ================================
// PYTHON IMPLEMENTATION NOTES
// ================================

/*
Below are notes on how to implement these viewer settings features in Python/PySide6:

1. Viewer Settings Manager:
```python
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QPushButton, QColorDialog, QCheckBox, QRadioButton, QButtonGroup, QGroupBox, QSpinBox, QDoubleSpinBox
from PySide6.QtCore import Qt, Signal, QObject

class ViewerSettingsManager(QObject):
    lighting_changed = Signal(dict)
    camera_changed = Signal(dict)
    colors_changed = Signal(dict)
    rendering_changed = Signal(dict)
    visibility_changed = Signal(dict)
    transform_changed = Signal(dict)
    
    def __init__(self, viewer=None):
        super().__init__()
        self.viewer = viewer
        self.settings = self.get_default_settings()
        self.callbacks = {}
        self.panel = None
        self.is_visible = False
    
    def get_default_settings(self):
        return {
            # Lighting settings
            'lighting': {
                'ambient_intensity': 0.3,
                'directional_intensity': 0.7,
                'directional_color': '#ffffff',
                'directional_position': {'x': 1, 'y': 1, 'z': 1},
                'point_intensity': 0.5,
                'point_color': '#ffffff',
                'point_position': {'x': 0, 'y': 5, 'z': 0}
            },
            
            # Camera settings
            'camera': {
                'position': {'x': 0, 'y': 0, 'z': 5},
                'target': {'x': 0, 'y': 0, 'z': 0},
                'up': {'x': 0, 'y': 1, 'z': 0},
                'fov': 45,
                'near': 0.1,
                'far': 1000
            },
            
            # Color settings
            'colors': {
                'background': '#f0f0f0',
                'model': '#cccccc',
                'wireframe': '#000000',
                'selected': '#0078d4'
            },
            
            # Rendering settings
            'rendering': {
                'mode': 'solid',  # solid, wireframe, points
                'show_axes': True,
                'show_grid': True,
                'show_bounding_box': False,
                'transparency': 1.0,
                'opacity': 1.0
            },
            
            # Transform settings
            'transform': {
                'position': {'x': 0, 'y': 0, 'z': 0},
                'rotation': {'x': 0, 'y': 0, 'z': 0},
                'scale': {'x': 1, 'y': 1, 'z': 1}
            },
            
            # Visibility settings
            'visibility': {
                'ucs': True,
                'axes': True,
                'grid': True,
                'bounding_box': False,
                'wireframe': False
            }
        }
    
    def create_settings_panel(self, parent):
        # Create panel widget
        self.panel = QWidget(parent)
        self.panel.setObjectName("viewer_settings_panel")
        
        # Create layout
        layout = QVBoxLayout(self.panel)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Create header
        header = self.create_panel_header()
        layout.addWidget(header)
        
        # Create content
        content = self.create_panel_content()
        layout.addWidget(content)
        
        return self.panel
    
    def create_panel_header(self):
        # Create header widget
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create title
        title = QLabel("Viewer Settings")
        title.setObjectName("viewer_settings_title")
        header_layout.addWidget(title)
        
        # Add stretch
        header_layout.addStretch()
        
        # Create toggle button
        toggle_button = QPushButton("▼")
        toggle_button.setObjectName("viewer_settings_toggle")
        toggle_button.setFixedSize(16, 16)
        toggle_button.clicked.connect(self.toggle_panel)
        header_layout.addWidget(toggle_button)
        
        return header
    
    def create_panel_content(self):
        # Create content widget
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)
        
        # Create lighting section
        lighting_section = self.create_lighting_section()
        content_layout.addWidget(lighting_section)
        
        # Create camera section
        camera_section = self.create_camera_section()
        content_layout.addWidget(camera_section)
        
        # Create colors section
        colors_section = self.create_colors_section()
        content_layout.addWidget(colors_section)
        
        # Create rendering section
        rendering_section = self.create_rendering_section()
        content_layout.addWidget(rendering_section)
        
        # Create visibility section
        visibility_section = self.create_visibility_section()
        content_layout.addWidget(visibility_section)
        
        # Create transform section
        transform_section = self.create_transform_section()
        content_layout.addWidget(transform_section)
        
        # Create advanced settings section
        advanced_section = self.create_advanced_section()
        content_layout.addWidget(advanced_section)
        
        return content
    
    def create_lighting_section(self):
        # Create group box
        section = QGroupBox("Lighting")
        section.setObjectName("settings_section")
        
        # Create layout
        layout = QVBoxLayout(section)
        layout.setSpacing(4)
        
        # Create ambient intensity control
        ambient_control = self.create_slider_control(
            "Ambient Intensity",
            self.settings['lighting']['ambient_intensity'],
            0, 1, 0.01,
            lambda value: self.update_setting('lighting.ambient_intensity', value)
        )
        layout.addWidget(ambient_control)
        
        # Create directional intensity control
        directional_control = self.create_slider_control(
            "Directional Intensity",
            self.settings['lighting']['directional_intensity'],
            0, 1, 0.01,
            lambda value: self.update_setting('lighting.directional_intensity', value)
        )
        layout.addWidget(directional_control)
        
        # Create directional color control
        directional_color_control = self.create_color_control(
            "Directional Color",
            self.settings['lighting']['directional_color'],
            lambda color: self.update_setting('lighting.directional_color', color)
        )
        layout.addWidget(directional_color_control)
        
        return section
    
    def create_slider_control(self, label, value, min_val, max_val, step, callback):
        # Create widget
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create label
        label_widget = QLabel(label)
        label_widget.setObjectName("lighting_control_label")
        layout.addWidget(label_widget)
        
        # Create slider
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(int(min_val * 100))
        slider.setMaximum(int(max_val * 100))
        slider.setSingleStep(int(step * 100))
        slider.setValue(int(value * 100))
        slider.valueChanged.connect(lambda v: callback(v / 100.0))
        layout.addWidget(slider)
        
        # Create value display
        value_widget = QLabel(f"{value:.2f}")
        value_widget.setObjectName("lighting_control_value")
        value_widget.setMinimumWidth(30)
        value_widget.setAlignment(Qt.AlignRight)
        slider.valueChanged.connect(lambda v: value_widget.setText(f"{v/100.0:.2f}"))
        layout.addWidget(value_widget)
        
        return widget
    
    def create_color_control(self, label, color, callback):
        # Create widget
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create label
        label_widget = QLabel(label)
        label_widget.setObjectName("lighting_control_label")
        layout.addWidget(label_widget)
        
        # Create color button
        color_button = QPushButton()
        color_button.setObjectName("color_picker")
        color_button.setStyleSheet(f"background-color: {color}; border: 1px solid #d0d0d0;")
        color_button.setFixedHeight(24)
        color_button.clicked.connect(lambda: self.pick_color(color_button, callback))
        layout.addWidget(color_button)
        
        return widget
    
    def pick_color(self, button, callback):
        # Open color dialog
        color = QColorDialog.getColor()
        if color.isValid():
            # Update button color
            button.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #d0d0d0;")
            
            # Call callback
            callback(color.name())
    
    def update_setting(self, key, value):
        # Parse key
        keys = key.split('.')
        
        # Get target object
        target = self.settings
        for k in keys[:-1]:
            target = target[k]
        
        # Update value
        target[keys[-1]] = value
        
        # Update relevant component
        if keys[0] == 'lighting':
            self.update_lighting()
        elif keys[0] == 'camera':
            self.update_camera()
        elif keys[0] == 'colors':
            self.update_colors()
        elif keys[0] == 'rendering':
            self.update_rendering()
        elif keys[0] == 'visibility':
            self.update_visibility()
        elif keys[0] == 'transform':
            self.update_transform()
    
    def update_lighting(self):
        # In a real implementation, this would update the lighting in the 3D viewer
        print(f"Updating lighting: {self.settings['lighting']}")
        
        # Emit signal
        self.lighting_changed.emit(self.settings['lighting'])
    
    def update_camera(self):
        # In a real implementation, this would update the camera in the 3D viewer
        print(f"Updating camera: {self.settings['camera']}")
        
        # Emit signal
        self.camera_changed.emit(self.settings['camera'])
    
    def update_colors(self):
        # In a real implementation, this would update the colors in the 3D viewer
        print(f"Updating colors: {self.settings['colors']}")
        
        # Emit signal
        self.colors_changed.emit(self.settings['colors'])
    
    def update_rendering(self):
        # In a real implementation, this would update the rendering in the 3D viewer
        print(f"Updating rendering: {self.settings['rendering']}")
        
        # Emit signal
        self.rendering_changed.emit(self.settings['rendering'])
    
    def update_visibility(self):
        # In a real implementation, this would update the visibility in the 3D viewer
        print(f"Updating visibility: {self.settings['visibility']}")
        
        # Emit signal
        self.visibility_changed.emit(self.settings['visibility'])
    
    def update_transform(self):
        # In a real implementation, this would update the transform in the 3D viewer
        print(f"Updating transform: {self.settings['transform']}")
        
        # Emit signal
        self.transform_changed.emit(self.settings['transform'])
```

2. Complete Viewer Settings Widget:
```python
import os
import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSlider, QPushButton, QColorDialog, QCheckBox, QRadioButton,
    QButtonGroup, QGroupBox, QSpinBox, QDoubleSpinBox, QComboBox,
    QTabWidget, QScrollArea, QFrame
)
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QColor

class ViewerSettingsWidget(QWidget):
    """
    A comprehensive 3D viewer settings widget with controls for:
    - Lighting (ambient, directional, point lights)
    - Camera (position, FOV, presets)
    - Colors (background, model, wireframe, selected)
    - Rendering (mode, transparency)
    - Visibility (axes, grid, bounding box, wireframe)
    - Transform (position, rotation, scale)
    """
    
    # Signals for when settings change
    lighting_changed = Signal(dict)
    camera_changed = Signal(dict)
    colors_changed = Signal(dict)
    rendering_changed = Signal(dict)
    visibility_changed = Signal(dict)
    transform_changed = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("viewer_settings_panel")
        
        # Initialize settings
        self.settings = self.get_default_settings()
        
        # Setup UI
        self.setup_ui()
        
        # Apply settings
        self.apply_settings()
    
    def get_default_settings(self):
        """Get default viewer settings"""
        return {
            # Lighting settings
            'lighting': {
                'ambient_intensity': 0.3,
                'directional_intensity': 0.7,
                'directional_color': '#ffffff',
                'directional_position': {'x': 1, 'y': 1, 'z': 1},
                'point_intensity': 0.5,
                'point_color': '#ffffff',
                'point_position': {'x': 0, 'y': 5, 'z': 0}
            },
            
            # Camera settings
            'camera': {
                'position': {'x': 0, 'y': 0, 'z': 5},
                'target': {'x': 0, 'y': 0, 'z': 0},
                'up': {'x': 0, 'y': 1, 'z': 0},
                'fov': 45,
                'near': 0.1,
                'far': 1000
            },
            
            # Color settings
            'colors': {
                'background': '#f0f0f0',
                'model': '#cccccc',
                'wireframe': '#000000',
                'selected': '#0078d4'
            },
            
            # Rendering settings
            'rendering': {
                'mode': 'solid',  # solid, wireframe, points
                'show_axes': True,
                'show_grid': True,
                'show_bounding_box': False,
                'transparency': 1.0,
                'opacity': 1.0
            },
            
            # Transform settings
            'transform': {
                'position': {'x': 0, 'y': 0, 'z': 0},
                'rotation': {'x': 0, 'y': 0, 'z': 0},
                'scale': {'x': 1, 'y': 1, 'z': 1}
            },
            
            # Visibility settings
            'visibility': {
                'ucs': True,
                'axes': True,
                'grid': True,
                'bounding_box': False,
                'wireframe': False
            }
        }
    
    def setup_ui(self):
        """Setup the user interface"""
        # Create main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        # Create header
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Create scroll area for content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Create content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)
        
        # Create tab widget for organized settings
        tab_widget = QTabWidget()
        
        # Create tabs
        lighting_tab = self.create_lighting_tab()
        camera_tab = self.create_camera_tab()
        colors_tab = self.create_colors_tab()
        rendering_tab = self.create_rendering_tab()
        visibility_tab = self.create_visibility_tab()
        transform_tab = self.create_transform_tab()
        
        # Add tabs to widget
        tab_widget.addTab(lighting_tab, "Lighting")
        tab_widget.addTab(camera_tab, "Camera")
        tab_widget.addTab(colors_tab, "Colors")
        tab_widget.addTab(rendering_tab, "Rendering")
        tab_widget.addTab(visibility_tab, "Visibility")
        tab_widget.addTab(transform_tab, "Transform")
        
        content_layout.addWidget(tab_widget)
        
        # Set scroll area content
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
        # Set minimum width
        self.setMinimumWidth(300)
    
    def create_header(self):
        """Create the header widget"""
        header = QFrame()
        header.setFrameStyle(QFrame.StyledPanel)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(4, 4, 4, 4)
        
        # Create title
        title = QLabel("Viewer Settings")
        title.setObjectName("viewer_settings_title")
        title.setStyleSheet("font-weight: bold; font-size: 12pt;")
        header_layout.addWidget(title)
        
        # Add stretch
        header_layout.addStretch()
        
        # Create reset button
        reset_button = QPushButton("Reset All")
        reset_button.clicked.connect(self.reset_all_settings)
        header_layout.addWidget(reset_button)
        
        return header
    
    def create_lighting_tab(self):
        """Create the lighting settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(8)
        
        # Ambient lighting
        ambient_group = QGroupBox("Ambient Lighting")
        ambient_layout = QVBoxLayout(ambient_group)
        
        ambient_control = self.create_slider_control(
            "Intensity",
            self.settings['lighting']['ambient_intensity'],
            0, 1, 0.01,
            lambda value: self.update_setting('lighting.ambient_intensity', value)
        )
        ambient_layout.addWidget(ambient_control)
        layout.addWidget(ambient_group)
        
        # Directional lighting
        directional_group = QGroupBox("Directional Lighting")
        directional_layout = QVBoxLayout(directional_group)
        
        # Intensity
        intensity_control = self.create_slider_control(
            "Intensity",
            self.settings['lighting']['directional_intensity'],
            0, 1, 0.01,
            lambda value: self.update_setting('lighting.directional_intensity', value)
        )
        directional_layout.addWidget(intensity_control)
        
        # Color
        color_control = self.create_color_control(
            "Color",
            self.settings['lighting']['directional_color'],
            lambda color: self.update_setting('lighting.directional_color', color)
        )
        directional_layout.addWidget(color_control)
        
        # Position
        pos_layout = QHBoxLayout()
        pos_layout.addWidget(QLabel("Position:"))
        
        # X position
        x_control = self.create_slider_control(
            "X",
            self.settings['lighting']['directional_position']['x'],
            -5, 5, 0.1,
            lambda value: self.update_setting('lighting.directional_position.x', value)
        )
        pos_layout.addWidget(x_control)
        
        # Y position
        y_control = self.create_slider_control(
            "Y",
            self.settings['lighting']['directional_position']['y'],
            -5, 5, 0.1,
            lambda value: self.update_setting('lighting.directional_position.y', value)
        )
        pos_layout.addWidget(y_control)
        
        # Z position
        z_control = self.create_slider_control(
            "Z",
            self.settings['lighting']['directional_position']['z'],
            -5, 5, 0.1,
            lambda value: self.update_setting('lighting.directional_position.z', value)
        )
        pos_layout.addWidget(z_control)
        
        directional_layout.addLayout(pos_layout)
        layout.addWidget(directional_group)
        
        # Point lighting
        point_group = QGroupBox("Point Lighting")
        point_layout = QVBoxLayout(point_group)
        
        # Intensity
        point_intensity_control = self.create_slider_control(
            "Intensity",
            self.settings['lighting']['point_intensity'],
            0, 1, 0.01,
            lambda value: self.update_setting('lighting.point_intensity', value)
        )
        point_layout.addWidget(point_intensity_control)
        
        # Color
        point_color_control = self.create_color_control(
            "Color",
            self.settings['lighting']['point_color'],
            lambda color: self.update_setting('lighting.point_color', color)
        )
        point_layout.addWidget(point_color_control)
        
        # Position
        point_pos_layout = QHBoxLayout()
        point_pos_layout.addWidget(QLabel("Position:"))
        
        # X position
        point_x_control = self.create_slider_control(
            "X",
            self.settings['lighting']['point_position']['x'],
            -5, 5, 0.1,
            lambda value: self.update_setting('lighting.point_position.x', value)
        )
        point_pos_layout.addWidget(point_x_control)
        
        # Y position
        point_y_control = self.create_slider_control(
            "Y",
            self.settings['lighting']['point_position']['y'],
            -5, 5, 0.1,
            lambda value: self.update_setting('lighting.point_position.y', value)
        )
        point_pos_layout.addWidget(point_y_control)
        
        # Z position
        point_z_control = self.create_slider_control(
            "Z",
            self.settings['lighting']['point_position']['z'],
            -5, 5, 0.1,
            lambda value: self.update_setting('lighting.point_position.z', value)
        )
        point_pos_layout.addWidget(point_z_control)
        
        point_layout.addLayout(point_pos_layout)
        layout.addWidget(point_group)
        
        # Add stretch
        layout.addStretch()
        
        return tab
    
    def create_camera_tab(self):
        """Create the camera settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(8)
        
        # Position
        position_group = QGroupBox("Position")
        position_layout = QVBoxLayout(position_group)
        
        # X position
        x_control = self.create_slider_control(
            "X",
            self.settings['camera']['position']['x'],
            -10, 10, 0.1,
            lambda value: self.update_setting('camera.position.x', value)
        )
        position_layout.addWidget(x_control)
        
        # Y position
        y_control = self.create_slider_control(
            "Y",
            self.settings['camera']['position']['y'],
            -10, 10, 0.1,
            lambda value: self.update_setting('camera.position.y', value)
        )
        position_layout.addWidget(y_control)
        
        # Z position
        z_control = self.create_slider_control(
            "Z",
            self.settings['camera']['position']['z'],
            -10, 10, 0.1,
            lambda value: self.update_setting('camera.position.z', value)
        )
        position_layout.addWidget(z_control)
        
        layout.addWidget(position_group)
        
        # FOV
        fov_control = self.create_slider_control(
            "Field of View",
            self.settings['camera']['fov'],
            10, 120, 1,
            lambda value: self.update_setting('camera.fov', value)
        )
        layout.addWidget(fov_control)
        
        # Presets
        presets_group = QGroupBox("Camera Presets")
        presets_layout = QVBoxLayout(presets_group)
        
        # Create preset buttons layout
        buttons_layout = QHBoxLayout()
        
        # Front preset
        front_button = QPushButton("Front")
        front_button.clicked.connect(lambda: self.set_camera_preset('front'))
        buttons_layout.addWidget(front_button)
        
        # Back preset
        back_button = QPushButton("Back")
        back_button.clicked.connect(lambda: self.set_camera_preset('back'))
        buttons_layout.addWidget(back_button)
        
        # Left preset
        left_button = QPushButton("Left")
        left_button.clicked.connect(lambda: self.set_camera_preset('left'))
        buttons_layout.addWidget(left_button)
        
        # Right preset
        right_button = QPushButton("Right")
        right_button.clicked.connect(lambda: self.set_camera_preset('right'))
        buttons_layout.addWidget(right_button)
        
        presets_layout.addLayout(buttons_layout)
        
        # Create second row of preset buttons
        buttons_layout2 = QHBoxLayout()
        
        # Top preset
        top_button = QPushButton("Top")
        top_button.clicked.connect(lambda: self.set_camera_preset('top'))
        buttons_layout2.addWidget(top_button)
        
        # Bottom preset
        bottom_button = QPushButton("Bottom")
        bottom_button.clicked.connect(lambda: self.set_camera_preset('bottom'))
        buttons_layout2.addWidget(bottom_button)
        
        # Isometric preset
        iso_button = QPushButton("Isometric")
        iso_button.clicked.connect(lambda: self.set_camera_preset('isometric'))
        buttons_layout2.addWidget(iso_button)
        
        presets_layout.addLayout(buttons_layout2)
        
        layout.addWidget(presets_group)
        
        # Add stretch
        layout.addStretch()
        
        return tab
    
    def create_colors_tab(self):
        """Create the colors settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(8)
        
        # Background color
        bg_control = self.create_color_control(
            "Background",
            self.settings['colors']['background'],
            lambda color: self.update_setting('colors.background', color)
        )
        layout.addWidget(bg_control)
        
        # Model color
        model_control = self.create_color_control(
            "Model",
            self.settings['colors']['model'],
            lambda color: self.update_setting('colors.model', color)
        )
        layout.addWidget(model_control)
        
        # Wireframe color
        wireframe_control = self.create_color_control(
            "Wireframe",
            self.settings['colors']['wireframe'],
            lambda color: self.update_setting('colors.wireframe', color)
        )
        layout.addWidget(wireframe_control)
        
        # Selected color
        selected_control = self.create_color_control(
            "Selected",
            self.settings['colors']['selected'],
            lambda color: self.update_setting('colors.selected', color)
        )
        layout.addWidget(selected_control)
        
        # Add stretch
        layout.addStretch()
        
        return tab
    
    def create_rendering_tab(self):
        """Create the rendering settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(8)
        
        # Rendering mode
        mode_group = QGroupBox("Rendering Mode")
        mode_layout = QVBoxLayout(mode_group)
        
        # Create radio buttons
        self.solid_radio = QRadioButton("Solid")
        self.solid_radio.setChecked(self.settings['rendering']['mode'] == 'solid')
        self.solid_radio.toggled.connect(lambda checked: checked and self.update_setting('rendering.mode', 'solid'))
        mode_layout.addWidget(self.solid_radio)
        
        self.wireframe_radio = QRadioButton("Wireframe")
        self.wireframe_radio.setChecked(self.settings['rendering']['mode'] == 'wireframe')
        self.wireframe_radio.toggled.connect(lambda checked: checked and self.update_setting('rendering.mode', 'wireframe'))
        mode_layout.addWidget(self.wireframe_radio)
        
        self.points_radio = QRadioButton("Points")
        self.points_radio.setChecked(self.settings['rendering']['mode'] == 'points')
        self.points_radio.toggled.connect(lambda checked: checked and self.update_setting('rendering.mode', 'points'))
        mode_layout.addWidget(self.points_radio)
        
        layout.addWidget(mode_group)
        
        # Transparency
        transparency_control = self.create_slider_control(
            "Transparency",
            self.settings['rendering']['transparency'],
            0, 1, 0.01,
            lambda value: self.update_setting('rendering.transparency', value)
        )
        layout.addWidget(transparency_control)
        
        # Add stretch
        layout.addStretch()
        
        return tab
    
    def create_visibility_tab(self):
        """Create the visibility settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(8)
        
        # UCS visibility
        ucs_control = self.create_checkbox_control(
            "UCS",
            self.settings['visibility']['ucs'],
            lambda checked: self.update_setting('visibility.ucs', checked)
        )
        layout.addWidget(ucs_control)
        
        # Axes visibility
        axes_control = self.create_checkbox_control(
            "Axes",
            self.settings['visibility']['axes'],
            lambda checked: self.update_setting('visibility.axes', checked)
        )
        layout.addWidget(axes_control)
        
        # Grid visibility
        grid_control = self.create_checkbox_control(
            "Grid",
            self.settings['visibility']['grid'],
            lambda checked: self.update_setting('visibility.grid', checked)
        )
        layout.addWidget(grid_control)
        
        # Bounding box visibility
        bbox_control = self.create_checkbox_control(
            "Bounding Box",
            self.settings['visibility']['bounding_box'],
            lambda checked: self.update_setting('visibility.bounding_box', checked)
        )
        layout.addWidget(bbox_control)
        
        # Wireframe visibility
        wireframe_control = self.create_checkbox_control(
            "Wireframe Overlay",
            self.settings['visibility']['wireframe'],
            lambda checked: self.update_setting('visibility.wireframe', checked)
        )
        layout.addWidget(wireframe_control)
        
        # Add stretch
        layout.addStretch()
        
        return tab
    
    def create_transform_tab(self):
        """Create the transform settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(8)
        
        # Position
        position_group = QGroupBox("Position")
        position_layout = QVBoxLayout(position_group)
        
        # X position
        x_control = self.create_slider_control(
            "X",
            self.settings['transform']['position']['x'],
            -10, 10, 0.1,
            lambda value: self.update_setting('transform.position.x', value)
        )
        position_layout.addWidget(x_control)
        
        # Y position
        y_control = self.create_slider_control(
            "Y",
            self.settings['transform']['position']['y'],
            -10, 10, 0.1,
            lambda value: self.update_setting('transform.position.y', value)
        )
        position_layout.addWidget(y_control)
        
        # Z position
        z_control = self.create_slider_control(
            "Z",
            self.settings['transform']['position']['z'],
            -10, 10, 0.1,
            lambda value: self.update_setting('transform.position.z', value)
        )
        position_layout.addWidget(z_control)
        
        layout.addWidget(position_group)
        
        # Rotation
        rotation_group = QGroupBox("Rotation")
        rotation_layout = QVBoxLayout(rotation_group)
        
        # X rotation
        x_rot_control = self.create_slider_control(
            "X",
            self.settings['transform']['rotation']['x'],
            0, 360, 1,
            lambda value: self.update_setting('transform.rotation.x', value)
        )
        rotation_layout.addWidget(x_rot_control)
        
        # Y rotation
        y_rot_control = self.create_slider_control(
            "Y",
            self.settings['transform']['rotation']['y'],
            0, 360, 1,
            lambda value: self.update_setting('transform.rotation.y', value)
        )
        rotation_layout.addWidget(y_rot_control)
        
        # Z rotation
        z_rot_control = self.create_slider_control(
            "Z",
            self.settings['transform']['rotation']['z'],
            0, 360, 1,
            lambda value: self.update_setting('transform.rotation.z', value)
        )
        rotation_layout.addWidget(z_rot_control)
        
        layout.addWidget(rotation_group)
        
        # Scale
        scale_group = QGroupBox("Scale")
        scale_layout = QVBoxLayout(scale_group)
        
        # X scale
        x_scale_control = self.create_slider_control(
            "X",
            self.settings['transform']['scale']['x'],
            0.1, 5, 0.1,
            lambda value: self.update_setting('transform.scale.x', value)
        )
        scale_layout.addWidget(x_scale_control)
        
        # Y scale
        y_scale_control = self.create_slider_control(
            "Y",
            self.settings['transform']['scale']['y'],
            0.1, 5, 0.1,
            lambda value: self.update_setting('transform.scale.y', value)
        )
        scale_layout.addWidget(y_scale_control)
        
        # Z scale
        z_scale_control = self.create_slider_control(
            "Z",
            self.settings['transform']['scale']['z'],
            0.1, 5, 0.1,
            lambda value: self.update_setting('transform.scale.z', value)
        )
        scale_layout.addWidget(z_scale_control)
        
        layout.addWidget(scale_group)
        
        # Reset button
        reset_button = QPushButton("Reset Transform")
        reset_button.clicked.connect(self.reset_transform)
        layout.addWidget(reset_button)
        
        # Add stretch
        layout.addStretch()
        
        return tab
    
    def create_slider_control(self, label, value, min_val, max_val, step, callback):
        """Create a slider control with label and value display"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create label
        label_widget = QLabel(label)
        label_widget.setMinimumWidth(80)
        layout.addWidget(label_widget)
        
        # Create slider
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(int(min_val * 100))
        slider.setMaximum(int(max_val * 100))
        slider.setSingleStep(int(step * 100))
        slider.setValue(int(value * 100))
        slider.valueChanged.connect(lambda v: callback(v / 100.0))
        layout.addWidget(slider)
        
        # Create value display
        value_widget = QLabel(f"{value:.2f}")
        value_widget.setMinimumWidth(50)
        value_widget.setAlignment(Qt.AlignRight)
        slider.valueChanged.connect(lambda v: value_widget.setText(f"{v/100.0:.2f}"))
        layout.addWidget(value_widget)
        
        return widget
    
    def create_color_control(self, label, color, callback):
        """Create a color control with label and color picker"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create label
        label_widget = QLabel(label)
        label_widget.setMinimumWidth(80)
        layout.addWidget(label_widget)
        
        # Create color button
        color_button = QPushButton()
        color_button.setObjectName("color_picker")
        color_button.setStyleSheet(f"background-color: {color}; border: 1px solid #d0d0d0;")
        color_button.setFixedHeight(24)
        color_button.clicked.connect(lambda: self.pick_color(color_button, callback))
        layout.addWidget(color_button)
        
        # Create color value label
        value_widget = QLabel(color)
        value_widget.setMinimumWidth(80)
        layout.addWidget(value_widget)
        
        # Store color value label reference for updating
        color_button.value_widget = value_widget
        
        return widget
    
    def create_checkbox_control(self, label, checked, callback):
        """Create a checkbox control with label"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create checkbox
        checkbox = QCheckBox(label)
        checkbox.setChecked(checked)
        checkbox.stateChanged.connect(lambda state: callback(state == Qt.Checked))
        layout.addWidget(checkbox)
        
        # Add stretch
        layout.addStretch()
        
        return widget
    
    def pick_color(self, button, callback):
        """Open color dialog and handle color selection"""
        # Get current color
        current_color = button.value_widget.text()
        color = QColor(current_color)
        
        # Open color dialog
        color = QColorDialog.getColor(color, self, "Select Color")
        
        if color.isValid():
            # Update button color
            button.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #d0d0d0;")
            
            # Update color value label
            button.value_widget.setText(color.name())
            
            # Call callback
            callback(color.name())
    
    def set_camera_preset(self, preset):
        """Set camera position to a preset"""
        if preset == 'front':
            self.settings['camera']['position'] = {'x': 0, 'y': 0, 'z': 5}
            self.settings['camera']['target'] = {'x': 0, 'y': 0, 'z': 0}
        elif preset == 'back':
            self.settings['camera']['position'] = {'x': 0, 'y': 0, 'z': -5}
            self.settings['camera']['target'] = {'x': 0, 'y': 0, 'z': 0}
        elif preset == 'left':
            self.settings['camera']['position'] = {'x': -5, 'y': 0, 'z': 0}
            self.settings['camera']['target'] = {'x': 0, 'y': 0, 'z': 0}
        elif preset == 'right':
            self.settings['camera']['position'] = {'x': 5, 'y': 0, 'z': 0}
            self.settings['camera']['target'] = {'x': 0, 'y': 0, 'z': 0}
        elif preset == 'top':
            self.settings['camera']['position'] = {'x': 0, 'y': 5, 'z': 0}
            self.settings['camera']['target'] = {'x': 0, 'y': 0, 'z': 0}
        elif preset == 'bottom':
            self.settings['camera']['position'] = {'x': 0, 'y': -5, 'z': 0}
            self.settings['camera']['target'] = {'x': 0, 'y': 0, 'z': 0}
        elif preset == 'isometric':
            self.settings['camera']['position'] = {'x': 5, 'y': 5, 'z': 5}
            self.settings['camera']['target'] = {'x': 0, 'y': 0, 'z': 0}
        
        # Update camera
        self.update_camera()
    
    def reset_transform(self):
        """Reset transform to default values"""
        self.settings['transform'] = {
            'position': {'x': 0, 'y': 0, 'z': 0},
            'rotation': {'x': 0, 'y': 0, 'z': 0},
            'scale': {'x': 1, 'y': 1, 'z': 1}
        }
        
        # Update transform
        self.update_transform()
        
        # Update UI controls
        self.update_transform_controls()
    
    def reset_all_settings(self):
        """Reset all settings to default values"""
        # Reset settings
        self.settings = self.get_default_settings()
        
        # Apply settings
        self.apply_settings()
    
    def update_setting(self, key, value):
        """Update a setting value and emit appropriate signal"""
        # Parse key
        keys = key.split('.')
        
        # Get target object
        target = self.settings
        for k in keys[:-1]:
            target = target[k]
        
        # Update value
        target[keys[-1]] = value
        
        # Update relevant component
        if keys[0] == 'lighting':
            self.update_lighting()
        elif keys[0] == 'camera':
            self.update_camera()
        elif keys[0] == 'colors':
            self.update_colors()
        elif keys[0] == 'rendering':
            self.update_rendering()
        elif keys[0] == 'visibility':
            self.update_visibility()
        elif keys[0] == 'transform':
            self.update_transform()
    
    def update_lighting(self):
        """Emit lighting changed signal"""
        self.lighting_changed.emit(self.settings['lighting'])
    
    def update_camera(self):
        """Emit camera changed signal"""
        self.camera_changed.emit(self.settings['camera'])
    
    def update_colors(self):
        """Emit colors changed signal"""
        self.colors_changed.emit(self.settings['colors'])
    
    def update_rendering(self):
        """Emit rendering changed signal"""
        self.rendering_changed.emit(self.settings['rendering'])
    
    def update_visibility(self):
        """Emit visibility changed signal"""
        self.visibility_changed.emit(self.settings['visibility'])
    
    def update_transform(self):
        """Emit transform changed signal"""
        self.transform_changed.emit(self.settings['transform'])
    
    def update_transform_controls(self):
        """Update transform controls to match current settings"""
        # This would update the UI controls to reflect the current settings
        # In a real implementation, you would need to store references to the controls
        # and update their values here
        pass
    
    def apply_settings(self):
        """Apply all settings and emit signals"""
        self.update_lighting()
        self.update_camera()
        self.update_colors()
        self.update_rendering()
        self.update_visibility()
        self.update_transform()
    
    def get_settings(self):
        """Get current settings"""
        return self.settings.copy()
    
    def set_settings(self, settings):
        """Set settings and apply them"""
        # Merge settings
        self.settings = self.merge_settings(self.settings, settings)
        
        # Apply settings
        self.apply_settings()
    
    def merge_settings(self, target, source):
        """Merge source settings into target settings"""
        result = target.copy()
        
        for key in source:
            if isinstance(source[key], dict) and source[key] is not None:
                result[key] = self.merge_settings(result.get(key, {}), source[key])
            else:
                result[key] = source[key]
        
        return result


# Example usage:
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Create main window
    window = QWidget()
    window.setWindowTitle("3D Viewer Settings")
    window.resize(400, 600)
    
    # Create layout
    layout = QVBoxLayout(window)
    
    # Create viewer settings widget
    settings_widget = ViewerSettingsWidget()
    layout.addWidget(settings_widget)
    
    # Connect signals
    settings_widget.lighting_changed.connect(lambda settings: print(f"Lighting changed: {settings}"))
    settings_widget.camera_changed.connect(lambda settings: print(f"Camera changed: {settings}"))
    settings_widget.colors_changed.connect(lambda settings: print(f"Colors changed: {settings}"))
    settings_widget.rendering_changed.connect(lambda settings: print(f"Rendering changed: {settings}"))
    settings_widget.visibility_changed.connect(lambda settings: print(f"Visibility changed: {settings}"))
    settings_widget.transform_changed.connect(lambda settings: print(f"Transform changed: {settings}"))
    
    window.show()
    sys.exit(app.exec())
```

3. Integration with VTK 3D Viewer:
```python
import vtk
from PySide6.QtWidgets import QVTKOpenGLNativeWidget

class ViewerWidget(QVTKOpenGLNativeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create renderer
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(0.95, 0.95, 0.95)
        
        # Create render window
        self.render_window = self.GetRenderWindow()
        self.render_window.AddRenderer(self.renderer)
        
        # Create interactor
        self.interactor = vtk.vtkRenderWindowInteractor()
        self.interactor.SetRenderWindow(self.render_window)
        
        # Create default lighting
        self.setup_default_lighting()
        
        # Create axes actor
        self.setup_axes()
        
        # Create grid actor
        self.setup_grid()
        
        # Store actors
        self.model_actor = None
        self.wireframe_actor = None
        self.points_actor = None
        
        # Store settings manager
        self.settings_manager = ViewerSettingsManager(self)
        self.settings_manager.addCallback('lighting_change', self.update_lighting)
        self.settings_manager.addCallback('camera_change', self.update_camera)
        self.settings_manager.addCallback('colors_change', self.update_colors)
        self.settings_manager.addCallback('rendering_change', self.update_rendering)
        self.settings_manager.addCallback('visibility_change', self.update_visibility)
        self.settings_manager.addCallback('transform_change', self.update_transform)
    
    def setup_default_lighting(self):
        # Create ambient light
        ambient_light = vtk.vtkLight()
        ambient_light.SetLightTypeToAmbient()
        ambient_light.SetIntensity(0.3)
        self.renderer.AddLight(ambient_light)
        
        # Create directional light
        directional_light = vtk.vtkLight()
        directional_light.SetLightTypeToSceneLight()
        directional_light.SetPosition(1, 1, 1)
        directional_light.SetFocalPoint(0, 0, 0)
        directional_light.SetIntensity(0.7)
        directional_light.SetColor(1, 1, 1)
        self.renderer.AddLight(directional_light)
        
        # Create point light
        point_light = vtk.vtkLight()
        point_light.SetLightTypeToPointLight()
        point_light.SetPosition(0, 5, 0)
        point_light.SetIntensity(0.5)
        point_light.SetColor(1, 1, 1)
        point_light.SetConeAngle(30)
        self.renderer.AddLight(point_light)
    
    def setup_axes(self):
        # Create axes actor
        self.axes = vtk.vtkAxesActor()
        self.renderer.AddActor(self.axes)
    
    def setup_grid(self):
        # Create grid actor
        self.grid = vtk.vtkCubeAxesActor()
        self.grid.SetBounds(-5, 5, -5, 5, -5, 5)
        self.grid.SetXTitle("X")
        self.grid.SetYTitle("Y")
        self.grid.SetZTitle("Z")
        self.renderer.AddActor(self.grid)
    
    def set_model(self, poly_data):
        # Create mapper
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(poly_data)
        
        # Create actor
        self.model_actor = vtk.vtkActor()
        self.model_actor.SetMapper(mapper)
        self.renderer.AddActor(self.model_actor)
        
        # Create wireframe actor
        wireframe_mapper = vtk.vtkPolyDataMapper()
        wireframe_mapper.SetInputData(poly_data)
        wireframe_mapper.SetResolveCoincidentTopologyToPolygonOffset()
        
        self.wireframe_actor = vtk.vtkActor()
        self.wireframe_actor.SetMapper(wireframe_mapper)
        self.wireframe_actor.GetProperty().SetRepresentationToWireframe()
        self.wireframe_actor.GetProperty().SetColor(0, 0, 0)
        self.wireframe_actor.VisibilityOff()
        self.renderer.AddActor(self.wireframe_actor)
        
        # Create points actor
        points_mapper = vtk.vtkPolyDataMapper()
        points_mapper.SetInputData(poly_data)
        
        self.points_actor = vtk.vtkActor()
        self.points_actor.SetMapper(points_mapper)
        self.points_actor.GetProperty().SetRepresentationToPoints()
        self.points_actor.GetProperty().SetPointSize(5)
        self.points_actor.VisibilityOff()
        self.renderer.AddActor(self.points_actor)
        
        # Reset camera
        self.renderer.ResetCamera()
        
        # Render
        self.render_window.Render()
    
    def update_lighting(self, lighting):
        # Update lights
        lights = self.renderer.GetLights()
        
        # Update ambient light
        ambient_light = lights.GetItemAsObject(0)
        ambient_light.SetIntensity(lighting['ambient_intensity'])
        
        # Update directional light
        directional_light = lights.GetItemAsObject(1)
        directional_light.SetIntensity(lighting['directional_intensity'])
        
        # Convert color from hex to RGB
        color = self.hex_to_rgb(lighting['directional_color'])
        directional_light.SetColor(color[0], color[1], color[2])
        
        # Update position
        pos = lighting['directional_position']
        directional_light.SetPosition(pos['x'], pos['y'], pos['z'])
        
        # Update point light
        point_light = lights.GetItemAsObject(2)
        point_light.SetIntensity(lighting['point_intensity'])
        
        # Convert color from hex to RGB
        color = self.hex_to_rgb(lighting['point_color'])
        point_light.SetColor(color[0], color[1], color[2])
        
        # Update position
        pos = lighting['point_position']
        point_light.SetPosition(pos['x'], pos['y'], pos['z'])
        
        # Render
        self.render_window.Render()
    
    def update_camera(self, camera):
        # Get camera
        cam = self.renderer.GetActiveCamera()
        
        # Update position
        pos = camera['position']
        cam.SetPosition(pos['x'], pos['y'], pos['z'])
        
        # Update target
        target = camera['target']
        cam.SetFocalPoint(target['x'], target['y'], target['z'])
        
        # Update up vector
        up = camera['up']
        cam.SetViewUp(up['x'], up['y'], up['z'])
        
        # Update FOV
        cam.SetViewAngle(camera['fov'])
        
        # Update clipping
        cam.SetClippingRange(camera['near'], camera['far'])
        
        # Render
        self.render_window.Render()
    
    def update_colors(self, colors):
        # Update background color
        bg_color = self.hex_to_rgb(colors['background'])
        self.renderer.SetBackground(bg_color[0], bg_color[1], bg_color[2])
        
        # Update model color
        if self.model_actor:
            model_color = self.hex_to_rgb(colors['model'])
            self.model_actor.GetProperty().SetColor(model_color[0], model_color[1], model_color[2])
        
        # Update wireframe color
        if self.wireframe_actor:
            wireframe_color = self.hex_to_rgb(colors['wireframe'])
            self.wireframe_actor.GetProperty().SetColor(wireframe_color[0], wireframe_color[1], wireframe_color[2])
        
        # Render
        self.render_window.Render()
    
    def update_rendering(self, rendering):
        # Update rendering mode
        if rendering['mode'] == 'solid':
            if self.model_actor:
                self.model_actor.VisibilityOn()
            if self.wireframe_actor:
                self.wireframe_actor.VisibilityOff()
            if self.points_actor:
                self.points_actor.VisibilityOff()
        elif rendering['mode'] == 'wireframe':
            if self.model_actor:
                self.model_actor.VisibilityOff()
            if self.wireframe_actor:
                self.wireframe_actor.VisibilityOn()
            if self.points_actor:
                self.points_actor.VisibilityOff()
        elif rendering['mode'] == 'points':
            if self.model_actor:
                self.model_actor.VisibilityOff()
            if self.wireframe_actor:
                self.wireframe_actor.VisibilityOff()
            if self.points_actor:
                self.points_actor.VisibilityOn()
        
        # Update transparency
        if self.model_actor:
            self.model_actor.GetProperty().SetOpacity(rendering['transparency'])
        
        # Render
        self.render_window.Render()
    
    def update_visibility(self, visibility):
        # Update axes visibility
        if self.axes:
            self.axes.SetVisibility(visibility['axes'])
        
        # Update grid visibility
        if self.grid:
            self.grid.SetVisibility(visibility['grid'])
        
        # Update wireframe visibility
        if self.wireframe_actor:
            self.wireframe_actor.SetVisibility(visibility['wireframe'])
        
        # Render
        self.render_window.Render()
    
    def update_transform(self, transform):
        # Update model transform
        if self.model_actor:
            # Create transform
            transform_filter = vtk.vtkTransform()
            
            # Set position
            pos = transform['position']
            transform_filter.Translate(pos['x'], pos['y'], pos['z'])
            
            # Set rotation
            rot = transform['rotation']
            transform_filter.RotateX(rot['x'])
            transform_filter.RotateY(rot['y'])
            transform_filter.RotateZ(rot['z'])
            
            # Set scale
            scale = transform['scale']
            transform_filter.Scale(scale['x'], scale['y'], scale['z'])
            
            # Apply transform
            self.model_actor.SetUserTransform(transform_filter)
            
            if self.wireframe_actor:
                self.wireframe_actor.SetUserTransform(transform_filter)
            
            if self.points_actor:
                self.points_actor.SetUserTransform(transform_filter)
        
        # Render
        self.render_window.Render()
    
    def hex_to_rgb(self, hex_color):
        # Remove # if present
        hex_color = hex_color.lstrip('#')
        
        # Parse hex
        if len(hex_color) == 3:
            r = int(hex_color[0] * 2, 16)
            g = int(hex_color[1] * 2, 16)
            b = int(hex_color[2] * 2, 16)
        else:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
        
        # Normalize to 0-1 range
        return [r / 255.0, g / 255.0, b / 255.0]
```
*/