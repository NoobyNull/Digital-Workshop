/**
 * Responsive Design Implementation for 3D-MM Application
 * 
 * This JavaScript file demonstrates how to implement responsive design for different window sizes,
 * which can be translated to the Python/PySide6 application.
 */

// ================================
// RESPONSIVE MANAGER
// ================================

/**
 * Responsive manager for handling responsive design
 */
class ResponsiveManager {
    constructor() {
        this.breakpoints = {
            xs: 0,      // Extra small devices (phones)
            sm: 600,    // Small devices (portrait tablets and large phones)
            md: 768,    // Medium devices (landscape tablets)
            lg: 992,    // Large devices (laptops/desktops)
            xl: 1200    // Extra large devices (large laptops and desktops)
        };
        
        this.currentBreakpoint = this.getCurrentBreakpoint();
        this.orientation = this.getCurrentOrientation();
        this.aspectRatio = this.getAspectRatio();
        this.callbacks = {};
        
        this.setupEventListeners();
        this.applyResponsiveStyles();
    }
    
    /**
     * Get current breakpoint based on window width
     * @returns {string} Current breakpoint
     */
    getCurrentBreakpoint() {
        const width = window.innerWidth;
        
        if (width < this.breakpoints.sm) {
            return 'xs';
        } else if (width < this.breakpoints.md) {
            return 'sm';
        } else if (width < this.breakpoints.lg) {
            return 'md';
        } else if (width < this.breakpoints.xl) {
            return 'lg';
        } else {
            return 'xl';
        }
    }
    
    /**
     * Get current orientation
     * @returns {string} Current orientation
     */
    getCurrentOrientation() {
        return window.innerWidth > window.innerHeight ? 'landscape' : 'portrait';
    }
    
    /**
     * Get current aspect ratio
     * @returns {number} Current aspect ratio
     */
    getAspectRatio() {
        return window.innerWidth / window.innerHeight;
    }
    
    /**
     * Set up event listeners for window resize
     */
    setupEventListeners() {
        window.addEventListener('resize', () => {
            this.handleResize();
        });
        
        window.addEventListener('orientationchange', () => {
            this.handleOrientationChange();
        });
    }
    
    /**
     * Handle window resize
     */
    handleResize() {
        const newBreakpoint = this.getCurrentBreakpoint();
        const newOrientation = this.getCurrentOrientation();
        const newAspectRatio = this.getAspectRatio();
        
        // Check if breakpoint changed
        if (newBreakpoint !== this.currentBreakpoint) {
            const oldBreakpoint = this.currentBreakpoint;
            this.currentBreakpoint = newBreakpoint;
            
            // Trigger breakpoint change callbacks
            this.triggerCallbacks('breakpointChange', {
                old: oldBreakpoint,
                new: newBreakpoint
            });
        }
        
        // Check if orientation changed
        if (newOrientation !== this.orientation) {
            const oldOrientation = this.orientation;
            this.orientation = newOrientation;
            
            // Trigger orientation change callbacks
            this.triggerCallbacks('orientationChange', {
                old: oldOrientation,
                new: newOrientation
            });
        }
        
        // Check if aspect ratio changed significantly
        if (Math.abs(newAspectRatio - this.aspectRatio) > 0.1) {
            const oldAspectRatio = this.aspectRatio;
            this.aspectRatio = newAspectRatio;
            
            // Trigger aspect ratio change callbacks
            this.triggerCallbacks('aspectRatioChange', {
                old: oldAspectRatio,
                new: newAspectRatio
            });
        }
        
        // Apply responsive styles
        this.applyResponsiveStyles();
    }
    
    /**
     * Handle orientation change
     */
    handleOrientationChange() {
        // Apply responsive styles after orientation change
        setTimeout(() => {
            this.applyResponsiveStyles();
        }, 100);
    }
    
    /**
     * Apply responsive styles based on current state
     */
    applyResponsiveStyles() {
        // Update body classes
        document.body.className = document.body.className
            .replace(/breakpoint-\w+/g, '')
            .replace(/orientation-\w+/g, '')
            .replace(/aspect-ratio-\w+/g, '')
            .trim();
        
        document.body.classList.add(`breakpoint-${this.currentBreakpoint}`);
        document.body.classList.add(`orientation-${this.orientation}`);
        
        // Add aspect ratio class
        if (this.aspectRatio > 16/9) {
            document.body.classList.add('aspect-ratio-wide');
        } else if (this.aspectRatio < 9/16) {
            document.body.classList.add('aspect-ratio-tall');
        } else {
            document.body.classList.add('aspect-ratio-normal');
        }
        
        // Apply layout adjustments
        this.applyLayoutAdjustments();
        
        // Apply component adjustments
        this.applyComponentAdjustments();
    }
    
    /**
     * Apply layout adjustments based on current breakpoint
     */
    applyLayoutAdjustments() {
        // Get main window element
        const mainWindow = document.querySelector('.main-window');
        if (!mainWindow) return;
        
        // Apply styles based on breakpoint
        switch (this.currentBreakpoint) {
            case 'xs':
                // Extra small layout
                this.applyExtraSmallLayout(mainWindow);
                break;
            case 'sm':
                // Small layout
                this.applySmallLayout(mainWindow);
                break;
            case 'md':
                // Medium layout
                this.applyMediumLayout(mainWindow);
                break;
            case 'lg':
                // Large layout
                this.applyLargeLayout(mainWindow);
                break;
            case 'xl':
                // Extra large layout
                this.applyExtraLargeLayout(mainWindow);
                break;
        }
        
        // Apply orientation-specific adjustments
        if (this.orientation === 'portrait') {
            this.applyPortraitLayout(mainWindow);
        } else {
            this.applyLandscapeLayout(mainWindow);
        }
    }
    
    /**
     * Apply extra small layout
     * @param {HTMLElement} mainWindow - Main window element
     */
    applyExtraSmallLayout(mainWindow) {
        // Stack panels vertically
        mainWindow.style.flexDirection = 'column';
        
        // Adjust toolbar
        const toolbar = document.querySelector('.main-toolbar');
        if (toolbar) {
            toolbar.style.flexWrap = 'wrap';
            toolbar.style.padding = '2px';
        }
        
        // Hide toolbar group labels
        const groupLabels = document.querySelectorAll('.toolbar-group-label');
        groupLabels.forEach(label => {
            label.style.display = 'none';
        });
        
        // Hide toolbar button text
        const buttonTexts = document.querySelectorAll('.toolbar-button-text');
        buttonTexts.forEach(text => {
            text.style.display = 'none';
        });
        
        // Adjust model library
        const modelLibrary = document.querySelector('.model-library-widget');
        if (modelLibrary) {
            modelLibrary.style.flexDirection = 'column';
            modelLibrary.style.maxHeight = '200px';
        }
        
        // Adjust metadata editor
        const metadataEditor = document.querySelector('.metadata-editor-widget');
        if (metadataEditor) {
            metadataEditor.style.flexDirection = 'column';
            metadataEditor.style.maxHeight = '200px';
        }
        
        // Adjust viewer
        const viewer = document.querySelector('.viewer-widget');
        if (viewer) {
            viewer.style.minHeight = '300px';
        }
        
        // Adjust panels
        const panels = document.querySelectorAll('.dock-widget');
        panels.forEach(panel => {
            panel.style.position = 'relative';
            panel.style.width = '100%';
            panel.style.height = 'auto';
            panel.style.maxHeight = '200px';
        });
    }
    
    /**
     * Apply small layout
     * @param {HTMLElement} mainWindow - Main window element
     */
    applySmallLayout(mainWindow) {
        // Stack panels vertically
        mainWindow.style.flexDirection = 'column';
        
        // Adjust toolbar
        const toolbar = document.querySelector('.main-toolbar');
        if (toolbar) {
            toolbar.style.flexWrap = 'wrap';
            toolbar.style.padding = '3px';
        }
        
        // Show toolbar group labels
        const groupLabels = document.querySelectorAll('.toolbar-group-label');
        groupLabels.forEach(label => {
            label.style.display = 'block';
        });
        
        // Show toolbar button text
        const buttonTexts = document.querySelectorAll('.toolbar-button-text');
        buttonTexts.forEach(text => {
            text.style.display = 'block';
        });
        
        // Adjust model library
        const modelLibrary = document.querySelector('.model-library-widget');
        if (modelLibrary) {
            modelLibrary.style.flexDirection = 'column';
            modelLibrary.style.maxHeight = '250px';
        }
        
        // Adjust metadata editor
        const metadataEditor = document.querySelector('.metadata-editor-widget');
        if (metadataEditor) {
            metadataEditor.style.flexDirection = 'column';
            metadataEditor.style.maxHeight = '250px';
        }
        
        // Adjust viewer
        const viewer = document.querySelector('.viewer-widget');
        if (viewer) {
            viewer.style.minHeight = '350px';
        }
        
        // Adjust panels
        const panels = document.querySelectorAll('.dock-widget');
        panels.forEach(panel => {
            panel.style.position = 'relative';
            panel.style.width = '100%';
            panel.style.height = 'auto';
            panel.style.maxHeight = '250px';
        });
    }
    
    /**
     * Apply medium layout
     * @param {HTMLElement} mainWindow - Main window element
     */
    applyMediumLayout(mainWindow) {
        // Stack panels based on orientation
        if (this.orientation === 'portrait') {
            mainWindow.style.flexDirection = 'column';
        } else {
            mainWindow.style.flexDirection = 'row';
        }
        
        // Adjust toolbar
        const toolbar = document.querySelector('.main-toolbar');
        if (toolbar) {
            toolbar.style.flexWrap = 'nowrap';
            toolbar.style.padding = '4px';
        }
        
        // Show toolbar group labels
        const groupLabels = document.querySelectorAll('.toolbar-group-label');
        groupLabels.forEach(label => {
            label.style.display = 'block';
        });
        
        // Show toolbar button text
        const buttonTexts = document.querySelectorAll('.toolbar-button-text');
        buttonTexts.forEach(text => {
            text.style.display = 'block';
        });
        
        // Adjust model library
        const modelLibrary = document.querySelector('.model-library-widget');
        if (modelLibrary) {
            if (this.orientation === 'portrait') {
                modelLibrary.style.flexDirection = 'column';
                modelLibrary.style.maxHeight = '300px';
            } else {
                modelLibrary.style.flexDirection = 'row';
                modelLibrary.style.maxWidth = '300px';
                modelLibrary.style.maxHeight = 'none';
            }
        }
        
        // Adjust metadata editor
        const metadataEditor = document.querySelector('.metadata-editor-widget');
        if (metadataEditor) {
            if (this.orientation === 'portrait') {
                metadataEditor.style.flexDirection = 'column';
                metadataEditor.style.maxHeight = '300px';
            } else {
                metadataEditor.style.flexDirection = 'row';
                metadataEditor.style.maxWidth = '300px';
                metadataEditor.style.maxHeight = 'none';
            }
        }
        
        // Adjust viewer
        const viewer = document.querySelector('.viewer-widget');
        if (viewer) {
            if (this.orientation === 'portrait') {
                viewer.style.minHeight = '400px';
            } else {
                viewer.style.minHeight = '500px';
            }
        }
        
        // Adjust panels
        const panels = document.querySelectorAll('.dock-widget');
        panels.forEach(panel => {
            if (this.orientation === 'portrait') {
                panel.style.position = 'relative';
                panel.style.width = '100%';
                panel.style.height = 'auto';
                panel.style.maxHeight = '300px';
            } else {
                panel.style.position = 'absolute';
                panel.style.width = '300px';
                panel.style.height = 'auto';
                panel.style.maxHeight = 'none';
            }
        });
    }
    
    /**
     * Apply large layout
     * @param {HTMLElement} mainWindow - Main window element
     */
    applyLargeLayout(mainWindow) {
        // Stack panels horizontally
        mainWindow.style.flexDirection = 'row';
        
        // Adjust toolbar
        const toolbar = document.querySelector('.main-toolbar');
        if (toolbar) {
            toolbar.style.flexWrap = 'nowrap';
            toolbar.style.padding = '5px';
        }
        
        // Show toolbar group labels
        const groupLabels = document.querySelectorAll('.toolbar-group-label');
        groupLabels.forEach(label => {
            label.style.display = 'block';
        });
        
        // Show toolbar button text
        const buttonTexts = document.querySelectorAll('.toolbar-button-text');
        buttonTexts.forEach(text => {
            text.style.display = 'block';
        });
        
        // Adjust model library
        const modelLibrary = document.querySelector('.model-library-widget');
        if (modelLibrary) {
            modelLibrary.style.flexDirection = 'column';
            modelLibrary.style.maxWidth = '350px';
            modelLibrary.style.maxHeight = 'none';
        }
        
        // Adjust metadata editor
        const metadataEditor = document.querySelector('.metadata-editor-widget');
        if (metadataEditor) {
            metadataEditor.style.flexDirection = 'column';
            metadataEditor.style.maxWidth = '350px';
            metadataEditor.style.maxHeight = 'none';
        }
        
        // Adjust viewer
        const viewer = document.querySelector('.viewer-widget');
        if (viewer) {
            viewer.style.minHeight = '600px';
        }
        
        // Adjust panels
        const panels = document.querySelectorAll('.dock-widget');
        panels.forEach(panel => {
            panel.style.position = 'absolute';
            panel.style.width = '350px';
            panel.style.height = 'auto';
            panel.style.maxHeight = 'none';
        });
    }
    
    /**
     * Apply extra large layout
     * @param {HTMLElement} mainWindow - Main window element
     */
    applyExtraLargeLayout(mainWindow) {
        // Stack panels horizontally
        mainWindow.style.flexDirection = 'row';
        
        // Adjust toolbar
        const toolbar = document.querySelector('.main-toolbar');
        if (toolbar) {
            toolbar.style.flexWrap = 'nowrap';
            toolbar.style.padding = '6px';
        }
        
        // Show toolbar group labels
        const groupLabels = document.querySelectorAll('.toolbar-group-label');
        groupLabels.forEach(label => {
            label.style.display = 'block';
        });
        
        // Show toolbar button text
        const buttonTexts = document.querySelectorAll('.toolbar-button-text');
        buttonTexts.forEach(text => {
            text.style.display = 'block';
        });
        
        // Adjust model library
        const modelLibrary = document.querySelector('.model-library-widget');
        if (modelLibrary) {
            modelLibrary.style.flexDirection = 'column';
            modelLibrary.style.maxWidth = '400px';
            modelLibrary.style.maxHeight = 'none';
        }
        
        // Adjust metadata editor
        const metadataEditor = document.querySelector('.metadata-editor-widget');
        if (metadataEditor) {
            metadataEditor.style.flexDirection = 'column';
            metadataEditor.style.maxWidth = '400px';
            metadataEditor.style.maxHeight = 'none';
        }
        
        // Adjust viewer
        const viewer = document.querySelector('.viewer-widget');
        if (viewer) {
            viewer.style.minHeight = '700px';
        }
        
        // Adjust panels
        const panels = document.querySelectorAll('.dock-widget');
        panels.forEach(panel => {
            panel.style.position = 'absolute';
            panel.style.width = '400px';
            panel.style.height = 'auto';
            panel.style.maxHeight = 'none';
        });
    }
    
    /**
     * Apply portrait layout
     * @param {HTMLElement} mainWindow - Main window element
     */
    applyPortraitLayout(mainWindow) {
        // Stack panels vertically
        mainWindow.style.flexDirection = 'column';
        
        // Adjust toolbar
        const toolbar = document.querySelector('.main-toolbar');
        if (toolbar) {
            toolbar.style.flexWrap = 'wrap';
        }
        
        // Adjust model library
        const modelLibrary = document.querySelector('.model-library-widget');
        if (modelLibrary) {
            modelLibrary.style.flexDirection = 'column';
            modelLibrary.style.maxHeight = '200px';
        }
        
        // Adjust metadata editor
        const metadataEditor = document.querySelector('.metadata-editor-widget');
        if (metadataEditor) {
            metadataEditor.style.flexDirection = 'column';
            metadataEditor.style.maxHeight = '200px';
        }
        
        // Adjust viewer
        const viewer = document.querySelector('.viewer-widget');
        if (viewer) {
            viewer.style.minHeight = '300px';
        }
    }
    
    /**
     * Apply landscape layout
     * @param {HTMLElement} mainWindow - Main window element
     */
    applyLandscapeLayout(mainWindow) {
        // Stack panels horizontally for larger screens
        if (this.currentBreakpoint === 'md' || this.currentBreakpoint === 'lg' || this.currentBreakpoint === 'xl') {
            mainWindow.style.flexDirection = 'row';
        } else {
            mainWindow.style.flexDirection = 'column';
        }
        
        // Adjust toolbar
        const toolbar = document.querySelector('.main-toolbar');
        if (toolbar) {
            toolbar.style.flexWrap = 'nowrap';
        }
        
        // Adjust model library
        const modelLibrary = document.querySelector('.model-library-widget');
        if (modelLibrary) {
            if (this.currentBreakpoint === 'md' || this.currentBreakpoint === 'lg' || this.currentBreakpoint === 'xl') {
                modelLibrary.style.flexDirection = 'column';
                modelLibrary.style.maxWidth = '300px';
                modelLibrary.style.maxHeight = 'none';
            } else {
                modelLibrary.style.flexDirection = 'column';
                modelLibrary.style.maxHeight = '200px';
            }
        }
        
        // Adjust metadata editor
        const metadataEditor = document.querySelector('.metadata-editor-widget');
        if (metadataEditor) {
            if (this.currentBreakpoint === 'md' || this.currentBreakpoint === 'lg' || this.currentBreakpoint === 'xl') {
                metadataEditor.style.flexDirection = 'column';
                metadataEditor.style.maxWidth = '300px';
                metadataEditor.style.maxHeight = 'none';
            } else {
                metadataEditor.style.flexDirection = 'column';
                metadataEditor.style.maxHeight = '200px';
            }
        }
        
        // Adjust viewer
        const viewer = document.querySelector('.viewer-widget');
        if (viewer) {
            viewer.style.minHeight = '400px';
        }
    }
    
    /**
     * Apply component adjustments based on current breakpoint
     */
    applyComponentAdjustments() {
        // Adjust font sizes
        this.adjustFontSizes();
        
        // Adjust spacing
        this.adjustSpacing();
        
        // Adjust touch targets
        this.adjustTouchTargets();
        
        // Adjust images
        this.adjustImages();
    }
    
    /**
     * Adjust font sizes based on current breakpoint
     */
    adjustFontSizes() {
        // Base font size
        let baseFontSize = '12px';
        
        switch (this.currentBreakpoint) {
            case 'xs':
                baseFontSize = '10px';
                break;
            case 'sm':
                baseFontSize = '11px';
                break;
            case 'md':
                baseFontSize = '12px';
                break;
            case 'lg':
                baseFontSize = '13px';
                break;
            case 'xl':
                baseFontSize = '14px';
                break;
        }
        
        document.documentElement.style.fontSize = baseFontSize;
    }
    
    /**
     * Adjust spacing based on current breakpoint
     */
    adjustSpacing() {
        // Base spacing
        let baseSpacing = '8px';
        
        switch (this.currentBreakpoint) {
            case 'xs':
                baseSpacing = '4px';
                break;
            case 'sm':
                baseSpacing = '6px';
                break;
            case 'md':
                baseSpacing = '8px';
                break;
            case 'lg':
                baseSpacing = '10px';
                break;
            case 'xl':
                baseSpacing = '12px';
                break;
        }
        
        // Apply spacing to main container
        const mainWindow = document.querySelector('.main-window');
        if (mainWindow) {
            mainWindow.style.gap = baseSpacing;
        }
    }
    
    /**
     * Adjust touch targets based on current breakpoint
     */
    adjustTouchTargets() {
        // Minimum touch target size
        let minTouchSize = '44px';
        
        // Only adjust for touch devices
        if (!this.isTouchDevice()) return;
        
        // Adjust buttons
        const buttons = document.querySelectorAll('button, .toolbar-button, .menu-bar-item');
        buttons.forEach(button => {
            button.style.minWidth = minTouchSize;
            button.style.minHeight = minTouchSize;
        });
        
        // Adjust inputs
        const inputs = document.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.style.minHeight = minTouchSize;
        });
        
        // Adjust links
        const links = document.querySelectorAll('a');
        links.forEach(link => {
            link.style.minHeight = minTouchSize;
            link.style.display = 'inline-flex';
            link.style.alignItems = 'center';
        });
    }
    
    /**
     * Adjust images based on current breakpoint
     */
    adjustImages() {
        // Get all images
        const images = document.querySelectorAll('img');
        
        images.forEach(img => {
            // Make images responsive
            img.style.maxWidth = '100%';
            img.style.height = 'auto';
            
            // Adjust based on breakpoint
            switch (this.currentBreakpoint) {
                case 'xs':
                    img.style.width = '100%';
                    break;
                case 'sm':
                    img.style.width = '100%';
                    break;
                case 'md':
                    img.style.width = 'auto';
                    break;
                case 'lg':
                    img.style.width = 'auto';
                    break;
                case 'xl':
                    img.style.width = 'auto';
                    break;
            }
        });
    }
    
    /**
     * Check if device is a touch device
     * @returns {boolean} Whether device is a touch device
     */
    isTouchDevice() {
        return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    }
    
    /**
     * Add a callback for responsive events
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
     * Remove a callback for responsive events
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
     * Trigger callbacks for an event
     * @param {string} event - Event name
     * @param {Object} data - Event data
     */
    triggerCallbacks(event, data) {
        if (this.callbacks[event]) {
            this.callbacks[event].forEach(callback => {
                callback(data);
            });
        }
    }
    
    /**
     * Get current responsive state
     * @returns {Object} Current responsive state
     */
    getCurrentState() {
        return {
            breakpoint: this.currentBreakpoint,
            orientation: this.orientation,
            aspectRatio: this.aspectRatio,
            width: window.innerWidth,
            height: window.innerHeight,
            isTouch: this.isTouchDevice()
        };
    }
}

// Create global responsive manager
const responsiveManager = new ResponsiveManager();

// ================================
// FLUID GRID MANAGER
// ================================

/**
 * Fluid grid manager for creating responsive grids
 */
class FluidGridManager {
    constructor() {
        this.grids = {};
    }
    
    /**
     * Create a fluid grid
     * @param {string} id - Grid ID
     * @param {HTMLElement} container - Container element
     * @param {Object} options - Grid options
     * @returns {HTMLElement} Grid element
     */
    createFluidGrid(id, container, options = {}) {
        // Create grid element
        const grid = document.createElement('div');
        grid.className = 'fluid-grid';
        grid.id = id;
        
        // Set grid options
        const minColumnWidth = options.minColumnWidth || 200;
        const gap = options.gap || 10;
        
        // Apply grid styles
        grid.style.display = 'grid';
        grid.style.gridTemplateColumns = `repeat(auto-fit, minmax(${minColumnWidth}px, 1fr))`;
        grid.style.gap = `${gap}px`;
        grid.style.width = '100%';
        
        // Add to container
        container.appendChild(grid);
        
        // Store grid
        this.grids[id] = {
            element: grid,
            options
        };
        
        return grid;
    }
    
    /**
     * Add an item to a fluid grid
     * @param {string} gridId - Grid ID
     * @param {HTMLElement} item - Item element
     * @param {Object} options - Item options
     */
    addGridItem(gridId, item, options = {}) {
        const grid = this.grids[gridId];
        if (!grid) return;
        
        // Set item options
        const columnSpan = options.columnSpan || 1;
        const rowSpan = options.rowSpan || 1;
        
        // Apply item styles
        item.style.gridColumn = `span ${columnSpan}`;
        item.style.gridRow = `span ${rowSpan}`;
        
        // Add to grid
        grid.element.appendChild(item);
    }
    
    /**
     * Remove an item from a fluid grid
     * @param {string} gridId - Grid ID
     * @param {HTMLElement} item - Item element
     */
    removeGridItem(gridId, item) {
        const grid = this.grids[gridId];
        if (!grid) return;
        
        // Remove from grid
        grid.element.removeChild(item);
    }
    
    /**
     * Update grid options
     * @param {string} gridId - Grid ID
     * @param {Object} options - New grid options
     */
    updateGridOptions(gridId, options) {
        const grid = this.grids[gridId];
        if (!grid) return;
        
        // Update options
        Object.assign(grid.options, options);
        
        // Apply new styles
        const minColumnWidth = grid.options.minColumnWidth || 200;
        const gap = grid.options.gap || 10;
        
        grid.element.style.gridTemplateColumns = `repeat(auto-fit, minmax(${minColumnWidth}px, 1fr))`;
        grid.element.style.gap = `${gap}px`;
    }
}

// Create global fluid grid manager
const fluidGridManager = new FluidGridManager();

// ================================
// RESPONSIVE IMAGE MANAGER
// ================================

/**
 * Responsive image manager for handling responsive images
 */
class ResponsiveImageManager {
    constructor() {
        this.images = {};
        this.setupIntersectionObserver();
    }
    
    /**
     * Set up intersection observer for lazy loading
     */
    setupIntersectionObserver() {
        // Create intersection observer
        this.intersectionObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.loadImage(entry.target);
                    this.intersectionObserver.unobserve(entry.target);
                }
            });
        }, {
            rootMargin: '50px'
        });
    }
    
    /**
     * Create a responsive image
     * @param {string} id - Image ID
     * @param {HTMLElement} container - Container element
     * @param {Object} options - Image options
     * @returns {HTMLElement} Image element
     */
    createResponsiveImage(id, container, options = {}) {
        // Create image container
        const imageContainer = document.createElement('div');
        imageContainer.className = 'responsive-image-container';
        imageContainer.id = id;
        
        // Set aspect ratio
        const aspectRatio = options.aspectRatio || '16/9';
        const [width, height] = aspectRatio.split('/').map(Number);
        const paddingBottom = (height / width) * 100;
        
        imageContainer.style.paddingBottom = `${paddingBottom}%`;
        imageContainer.style.position = 'relative';
        imageContainer.style.overflow = 'hidden';
        
        // Create image element
        const img = document.createElement('img');
        img.className = 'responsive-image';
        img.style.position = 'absolute';
        img.style.top = '0';
        img.style.left = '0';
        img.style.width = '100%';
        img.style.height = '100%';
        img.style.objectFit = options.objectFit || 'contain';
        
        // Set alt text
        img.alt = options.alt || '';
        
        // Add to container
        imageContainer.appendChild(img);
        
        // Add to main container
        container.appendChild(imageContainer);
        
        // Store image
        this.images[id] = {
            container: imageContainer,
            img,
            options
        };
        
        // Load image if not lazy loading
        if (!options.lazy) {
            this.loadImage(img);
        } else {
            // Add to intersection observer for lazy loading
            this.intersectionObserver.observe(img);
        }
        
        return imageContainer;
    }
    
    /**
     * Load an image
     * @param {HTMLImageElement} img - Image element
     */
    loadImage(img) {
        // Get image data
        const imageData = this.findImageData(img);
        if (!imageData) return;
        
        // Set src based on current breakpoint
        const breakpoint = responsiveManager.getCurrentBreakpoint();
        const src = this.getImageSrc(imageData, breakpoint);
        
        if (src) {
            img.src = src;
        }
    }
    
    /**
     * Find image data
     * @param {HTMLImageElement} img - Image element
     * @returns {Object|null} Image data
     */
    findImageData(img) {
        for (const id in this.images) {
            if (this.images[id].img === img) {
                return this.images[id];
            }
        }
        return null;
    }
    
    /**
     * Get image src based on breakpoint
     * @param {Object} imageData - Image data
     * @param {string} breakpoint - Current breakpoint
     * @returns {string|null} Image src
     */
    getImageSrc(imageData, breakpoint) {
        const options = imageData.options;
        
        // Check for specific breakpoint src
        if (options.srcs && options.srcs[breakpoint]) {
            return options.srcs[breakpoint];
        }
        
        // Check for default src
        if (options.src) {
            return options.src;
        }
        
        return null;
    }
    
    /**
     * Update image sources
     * @param {string} id - Image ID
     * @param {Object} srcs - New image sources
     */
    updateImageSources(id, srcs) {
        const imageData = this.images[id];
        if (!imageData) return;
        
        // Update options
        imageData.options.srcs = srcs;
        
        // Reload image
        this.loadImage(imageData.img);
    }
}

// Create global responsive image manager
const responsiveImageManager = new ResponsiveImageManager();

// ================================
// RESPONSIVE NAVIGATION MANAGER
// ================================

/**
 * Responsive navigation manager for handling responsive navigation
 */
class ResponsiveNavigationManager {
    constructor() {
        this.navigations = {};
        this.setupEventListeners();
    }
    
    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // Add breakpoint change callback
        responsiveManager.addCallback('breakpointChange', (data) => {
            this.handleBreakpointChange(data);
        });
    }
    
    /**
     * Create a responsive navigation
     * @param {string} id - Navigation ID
     * @param {HTMLElement} container - Container element
     * @param {Object} options - Navigation options
     * @returns {HTMLElement} Navigation element
     */
    createResponsiveNavigation(id, container, options = {}) {
        // Create navigation container
        const nav = document.createElement('nav');
        nav.className = 'responsive-nav';
        nav.id = id;
        
        // Create hamburger menu
        const hamburger = document.createElement('div');
        hamburger.className = 'hamburger-menu';
        hamburger.innerHTML = '☰';
        hamburger.setAttribute('aria-label', 'Toggle navigation');
        hamburger.setAttribute('role', 'button');
        hamburger.setAttribute('tabindex', '0');
        
        // Create menu container
        const menuContainer = document.createElement('div');
        menuContainer.className = 'nav-menu';
        menuContainer.style.display = 'none';
        
        // Add to navigation
        nav.appendChild(hamburger);
        nav.appendChild(menuContainer);
        
        // Add to main container
        container.appendChild(nav);
        
        // Set up event listeners
        hamburger.addEventListener('click', () => {
            this.toggleMenu(menuContainer);
        });
        
        hamburger.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                this.toggleMenu(menuContainer);
            }
        });
        
        // Store navigation
        this.navigations[id] = {
            element: nav,
            hamburger,
            menuContainer,
            options
        };
        
        // Apply initial styles
        this.applyNavigationStyles(id);
        
        return nav;
    }
    
    /**
     * Add a navigation item
     * @param {string} navId - Navigation ID
     * @param {string} itemId - Item ID
     * @param {string} text - Item text
     * @param {Function} callback - Click callback
     * @param {Object} options - Item options
     * @returns {HTMLElement} Item element
     */
    addNavigationItem(navId, itemId, text, callback, options = {}) {
        const nav = this.navigations[navId];
        if (!nav) return null;
        
        // Create item
        const item = document.createElement('div');
        item.className = 'nav-item';
        item.id = itemId;
        item.textContent = text;
        
        // Set up click handler
        item.addEventListener('click', () => {
            if (callback) callback();
            
            // Close menu on small screens
            if (responsiveManager.getCurrentBreakpoint() === 'xs') {
                nav.menuContainer.style.display = 'none';
            }
        });
        
        // Add to menu container
        nav.menuContainer.appendChild(item);
        
        return item;
    }
    
    /**
     * Toggle menu visibility
     * @param {HTMLElement} menuContainer - Menu container element
     */
    toggleMenu(menuContainer) {
        if (menuContainer.style.display === 'none') {
            menuContainer.style.display = 'flex';
            menuContainer.setAttribute('aria-expanded', 'true');
        } else {
            menuContainer.style.display = 'none';
            menuContainer.setAttribute('aria-expanded', 'false');
        }
    }
    
    /**
     * Handle breakpoint change
     * @param {Object} data - Breakpoint change data
     */
    handleBreakpointChange(data) {
        // Update all navigations
        Object.keys(this.navigations).forEach(id => {
            this.applyNavigationStyles(id);
        });
    }
    
    /**
     * Apply navigation styles based on current breakpoint
     * @param {string} navId - Navigation ID
     */
    applyNavigationStyles(navId) {
        const nav = this.navigations[navId];
        if (!nav) return;
        
        const breakpoint = responsiveManager.getCurrentBreakpoint();
        
        // Apply styles based on breakpoint
        if (breakpoint === 'xs') {
            // Show hamburger menu
            nav.hamburger.style.display = 'block';
            
            // Hide menu by default
            if (nav.menuContainer.style.display !== 'flex') {
                nav.menuContainer.style.display = 'none';
            }
            
            // Stack items vertically
            nav.menuContainer.style.flexDirection = 'column';
            nav.menuContainer.style.gap = '0';
            
            // Style items
            const items = nav.menuContainer.querySelectorAll('.nav-item');
            items.forEach(item => {
                item.style.width = '100%';
                item.style.padding = '12px';
                item.style.borderBottom = '1px solid #e0e0e0';
            });
        } else {
            // Hide hamburger menu
            nav.hamburger.style.display = 'none';
            
            // Show menu
            nav.menuContainer.style.display = 'flex';
            nav.menuContainer.setAttribute('aria-expanded', 'false');
            
            // Stack items horizontally
            nav.menuContainer.style.flexDirection = 'row';
            nav.menuContainer.style.gap = '5px';
            
            // Style items
            const items = nav.menuContainer.querySelectorAll('.nav-item');
            items.forEach(item => {
                item.style.width = 'auto';
                item.style.padding = '8px 16px';
                item.style.borderBottom = 'none';
            });
        }
    }
}

// Create global responsive navigation manager
const responsiveNavigationManager = new ResponsiveNavigationManager();

// ================================
// PYTHON IMPLEMENTATION NOTES
// ================================

/*
Below are notes on how to implement these responsive design features in Python/PySide6:

1. Responsive Manager:
```python
from PySide6.QtCore import QObject, Signal, QTimer, QSize
from PySide6.QtWidgets import QApplication, QWidget

class ResponsiveManager(QObject):
    breakpoint_changed = Signal(str, str)  # old, new
    orientation_changed = Signal(str, str)  # old, new
    aspect_ratio_changed = Signal(float, float)  # old, new
    
    def __init__(self):
        super().__init__()
        self.breakpoints = {
            'xs': 0,      # Extra small devices (phones)
            'sm': 600,    # Small devices (portrait tablets and large phones)
            'md': 768,    # Medium devices (landscape tablets)
            'lg': 992,    # Large devices (laptops/desktops)
            'xl': 1200    # Extra large devices (large laptops and desktops)
        }
        
        self.current_breakpoint = self.get_current_breakpoint()
        self.orientation = self.get_current_orientation()
        self.aspect_ratio = self.get_aspect_ratio()
        self.callbacks = {}
        
        self.setup_event_listeners()
        self.apply_responsive_styles()
    
    def get_current_breakpoint(self):
        width = QApplication.primaryScreen().size().width()
        
        if width < self.breakpoints['sm']:
            return 'xs'
        elif width < self.breakpoints['md']:
            return 'sm'
        elif width < self.breakpoints['lg']:
            return 'md'
        elif width < self.breakpoints['xl']:
            return 'lg'
        else:
            return 'xl'
    
    def get_current_orientation(self):
        size = QApplication.primaryScreen().size()
        return 'landscape' if size.width() > size.height() else 'portrait'
    
    def get_aspect_ratio(self):
        size = QApplication.primaryScreen().size()
        return size.width() / size.height()
    
    def setup_event_listeners(self):
        # In PySide6, we need to use a timer to check for window size changes
        self.resize_timer = QTimer()
        self.resize_timer.timeout.connect(self.check_resize)
        self.resize_timer.start(500)  # Check every 500ms
    
    def check_resize(self):
        new_breakpoint = self.get_current_breakpoint()
        new_orientation = self.get_current_orientation()
        new_aspect_ratio = self.get_aspect_ratio()
        
        # Check if breakpoint changed
        if new_breakpoint != self.current_breakpoint:
            old_breakpoint = self.current_breakpoint
            self.current_breakpoint = new_breakpoint
            
            # Emit signal
            self.breakpoint_changed.emit(old_breakpoint, new_breakpoint)
        
        # Check if orientation changed
        if new_orientation != self.orientation:
            old_orientation = self.orientation
            self.orientation = new_orientation
            
            # Emit signal
            self.orientation_changed.emit(old_orientation, new_orientation)
        
        # Check if aspect ratio changed significantly
        if abs(new_aspect_ratio - self.aspect_ratio) > 0.1:
            old_aspect_ratio = self.aspect_ratio
            self.aspect_ratio = new_aspect_ratio
            
            # Emit signal
            self.aspect_ratio_changed.emit(old_aspect_ratio, new_aspect_ratio)
        
        # Apply responsive styles
        self.apply_responsive_styles()
    
    def apply_responsive_styles(self):
        # Get main window
        main_window = QApplication.instance().mainWindow
        if not main_window:
            return
        
        # Apply styles based on breakpoint
        if self.current_breakpoint == 'xs':
            self.apply_extra_small_layout(main_window)
        elif self.current_breakpoint == 'sm':
            self.apply_small_layout(main_window)
        elif self.current_breakpoint == 'md':
            self.apply_medium_layout(main_window)
        elif self.current_breakpoint == 'lg':
            self.apply_large_layout(main_window)
        elif self.current_breakpoint == 'xl':
            self.apply_extra_large_layout(main_window)
        
        # Apply orientation-specific adjustments
        if self.orientation == 'portrait':
            self.apply_portrait_layout(main_window)
        else:
            self.apply_landscape_layout(main_window)
```

2. Fluid Grid Manager:
```python
from PySide6.QtWidgets import QGridLayout, QWidget, QSizePolicy

class FluidGridWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.grid_layout = QGridLayout(self)
        self.grid_layout.setSpacing(10)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        
        # Set size policy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    
    def add_widget(self, widget, column_span=1, row_span=1):
        # Find next available position
        row, col = self.find_next_position()
        
        # Add widget to grid
        self.grid_layout.addWidget(widget, row, col, row_span, column_span)
        
        # Set stretch factors
        for i in range(column_span):
            self.grid_layout.setColumnStretch(col + i, 1)
        
        for i in range(row_span):
            self.grid_layout.setRowStretch(row + i, 1)
    
    def find_next_position(self):
        # Find next available position in grid
        row = 0
        col = 0
        
        while True:
            # Check if position is occupied
            item = self.grid_layout.itemAtPosition(row, col)
            if not item:
                return row, col
            
            # Move to next position
            col += 1
            if col >= 12:  # Maximum columns
                col = 0
                row += 1
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        
        # Adjust grid based on available width
        width = self.width()
        
        # Calculate number of columns based on width
        if width < 600:
            columns = 1
        elif width < 900:
            columns = 2
        elif width < 1200:
            columns = 3
        else:
            columns = 4
        
        # Rearrange widgets if needed
        self.rearrange_widgets(columns)
    
    def rearrange_widgets(self, columns):
        # Get all widgets
        widgets = []
        for i in range(self.grid_layout.count()):
            item = self.grid_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    widgets.append(widget)
        
        # Clear layout
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    self.grid_layout.removeWidget(widget)
        
        # Re-add widgets in new arrangement
        for i, widget in enumerate(widgets):
            row = i // columns
            col = i % columns
            self.grid_layout.addWidget(widget, row, col)
```

3. Responsive Image Manager:
```python
from PySide6.QtWidgets import QLabel, QSizePolicy
from PySide6.QtCore import Qt, QUrl, QTimer
from PySide6.QtGui import QPixmap, QMovie

class ResponsiveImageLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.aspect_ratio = 16 / 9  # Default aspect ratio
        self.object_fit = Qt.KeepAspectRatio
        self.srcs = {}  # Sources for different breakpoints
        self.current_src = None
        
        # Set size policy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Set alignment
        self.setAlignment(Qt.AlignCenter)
        
        # Set minimum size
        self.setMinimumSize(100, 100)
    
    def set_aspect_ratio(self, width, height):
        self.aspect_ratio = width / height
        self.updateGeometry()
    
    def set_object_fit(self, fit):
        self.object_fit = fit
        self.update_pixmap()
    
    def set_src(self, src, breakpoint=None):
        if breakpoint:
            self.srcs[breakpoint] = src
        else:
            self.srcs['default'] = src
        
        # Update image if current breakpoint matches
        current_breakpoint = self.get_current_breakpoint()
        if breakpoint == current_breakpoint or (not breakpoint and current_breakpoint not in self.srcs):
            self.load_image(src)
    
    def get_current_breakpoint(self):
        # Get current breakpoint from responsive manager
        from .responsive_manager import responsiveManager
        return responsiveManager.get_current_breakpoint()
    
    def load_image(self, src):
        # Load image from src
        self.current_src = src
        
        # In a real implementation, you would load the image here
        # For now, just set a placeholder text
        self.setText(f"Image: {src}")
        
        # Update pixmap
        self.update_pixmap()
    
    def update_pixmap(self):
        # In a real implementation, you would update the pixmap here
        pass
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        
        # Update geometry to maintain aspect ratio
        width = self.width()
        height = int(width / self.aspect_ratio)
        
        if height != self.height():
            self.setFixedHeight(height)
```

4. Responsive Navigation Manager:
```python
from PySide6.QtWidgets import QToolBar, QAction, QToolButton, QMenu, QWidget, QVBoxLayout, QHBoxLayout

class ResponsiveNavigationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        # Create main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Create toolbar
        self.toolbar = QToolBar()
        self.toolbar.setMovable(False)
        
        # Create hamburger menu button
        self.hamburger_button = QToolButton()
        self.hamburger_button.setText("☰")
        self.hamburger_button.setCheckable(True)
        self.hamburger_button.setStyleSheet("""
            QToolButton {
                border: none;
                padding: 8px;
                font-size: 16px;
            }
            QToolButton:checked {
                background-color: #e0e0e0;
            }
        """)
        
        # Create menu
        self.menu = QMenu()
        
        # Add to toolbar
        self.toolbar.addWidget(self.hamburger_button)
        self.toolbar.addAction(self.menu.menuAction())
        
        # Create menu container
        self.menu_container = QWidget()
        self.menu_container.setLayout(QVBoxLayout())
        self.menu_container.layout().setContentsMargins(0, 0, 0, 0)
        self.menu_container.layout().setSpacing(0)
        self.menu_container.hide()
        
        # Add to main layout
        self.main_layout.addWidget(self.toolbar)
        self.main_layout.addWidget(self.menu_container)
    
    def setup_connections(self):
        # Connect hamburger button
        self.hamburger_button.toggled.connect(self.toggle_menu)
        
        # Connect to responsive manager
        from .responsive_manager import responsiveManager
        responsiveManager.breakpoint_changed.connect(self.apply_navigation_styles)
    
    def toggle_menu(self, checked):
        if checked:
            self.menu_container.show()
        else:
            self.menu_container.hide()
    
    def add_action(self, text, callback, icon=None):
        # Create action
        action = QAction(text, self)
        
        # Set icon if provided
        if icon:
            action.setIcon(icon)
        
        # Connect callback
        if callback:
            action.triggered.connect(callback)
        
        # Add to menu
        self.menu.addAction(action)
        
        # Add to toolbar for larger screens
        from .responsive_manager import responsiveManager
        if responsiveManager.get_current_breakpoint() != 'xs':
            self.toolbar.addAction(action)
        
        return action
    
    def apply_navigation_styles(self, old_breakpoint, new_breakpoint):
        if new_breakpoint == 'xs':
            # Show hamburger menu
            self.hamburger_button.show()
            
            # Remove actions from toolbar
            for action in self.menu.actions():
                self.toolbar.removeAction(action)
            
            # Add menu action
            self.toolbar.addAction(self.menu.menuAction())
        else:
            # Hide hamburger menu
            self.hamburger_button.hide()
            self.menu_container.hide()
            
            # Add actions to toolbar
            for action in self.menu.actions():
                self.toolbar.addAction(action)
            
            # Remove menu action
            self.toolbar.removeAction(self.menu.menuAction())
```
*/