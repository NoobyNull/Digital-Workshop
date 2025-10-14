/**
 * Status Indicators Implementation for 3D-MM Application
 * 
 * This JavaScript file demonstrates how to implement status indicators for system health,
 * which can be translated to the Python/PySide6 application.
 */

// ================================
// SYSTEM STATUS MONITOR
// ================================

/**
 * System status monitor for monitoring system health
 */
class SystemStatusMonitor {
    constructor() {
        this.statusIndicators = {};
        this.updateInterval = 1000; // ms
        this.isMonitoring = false;
        this.callbacks = {};
        this.performanceMode = this.detectPerformanceMode();
        this.setupPerformanceMonitoring();
    }
    
    /**
     * Detect performance mode to adjust update frequency
     * @returns {string} Performance mode
     */
    detectPerformanceMode() {
        // Check device capabilities
        const memory = this.getDeviceMemory();
        const cores = this.getCPUCores();
        
        if (memory > 4 && cores > 4) {
            return 'high';
        } else if (memory > 2 && cores > 2) {
            return 'medium';
        } else {
            return 'low';
        }
    }
    
    /**
     * Set up performance monitoring based on performance mode
     */
    setupPerformanceMonitoring() {
        switch (this.performanceMode) {
            case 'high':
                this.updateInterval = 500; // Update more frequently
                break;
            case 'medium':
                this.updateInterval = 1000; // Standard update frequency
                break;
            case 'low':
                this.updateInterval = 2000; // Update less frequently
                break;
        }
    }
    
    /**
     * Create a status indicator
     * @param {string} id - Indicator ID
     * @param {string} type - Indicator type
     * @param {HTMLElement} container - Container element
     * @param {Object} options - Indicator options
     * @returns {HTMLElement} Status indicator element
     */
    createStatusIndicator(id, type, container, options = {}) {
        // Create status indicator element
        const indicator = document.createElement('div');
        indicator.className = 'status-indicator';
        indicator.id = id;
        
        // Add icon
        const icon = document.createElement('div');
        icon.className = 'status-indicator-icon';
        indicator.appendChild(icon);
        
        // Add text
        const text = document.createElement('div');
        text.className = 'status-indicator-text';
        text.textContent = options.text || '';
        indicator.appendChild(text);
        
        // Add to container
        container.appendChild(indicator);
        
        // Store indicator
        this.statusIndicators[id] = {
            element: indicator,
            icon,
            text,
            type,
            options
        };
        
        return indicator;
    }
    
    /**
     * Create a memory usage indicator
     * @param {string} id - Indicator ID
     * @param {HTMLElement} container - Container element
     * @param {Object} options - Indicator options
     * @returns {HTMLElement} Memory usage indicator element
     */
    createMemoryUsageIndicator(id, container, options = {}) {
        // Create memory usage indicator element
        const indicator = document.createElement('div');
        indicator.className = 'memory-usage-indicator';
        indicator.id = id;
        
        // Create usage bar
        const bar = document.createElement('div');
        bar.className = 'memory-usage-bar';
        
        const barFill = document.createElement('div');
        barFill.className = 'memory-usage-bar-fill';
        bar.appendChild(barFill);
        indicator.appendChild(bar);
        
        // Add text
        const text = document.createElement('div');
        text.className = 'memory-usage-text';
        text.textContent = '0%';
        indicator.appendChild(text);
        
        // Add to container
        container.appendChild(indicator);
        
        // Store indicator
        this.statusIndicators[id] = {
            element: indicator,
            bar,
            barFill,
            text,
            type: 'memory',
            options
        };
        
        return indicator;
    }
    
    /**
     * Create a CPU usage indicator
     * @param {string} id - Indicator ID
     * @param {HTMLElement} container - Container element
     * @param {Object} options - Indicator options
     * @returns {HTMLElement} CPU usage indicator element
     */
    createCPUUsageIndicator(id, container, options = {}) {
        // Create CPU usage indicator element
        const indicator = document.createElement('div');
        indicator.className = 'cpu-usage-indicator';
        indicator.id = id;
        
        // Create usage bar
        const bar = document.createElement('div');
        bar.className = 'cpu-usage-bar';
        
        const barFill = document.createElement('div');
        barFill.className = 'cpu-usage-bar-fill';
        bar.appendChild(barFill);
        indicator.appendChild(bar);
        
        // Add text
        const text = document.createElement('div');
        text.className = 'cpu-usage-text';
        text.textContent = '0%';
        indicator.appendChild(text);
        
        // Add to container
        container.appendChild(indicator);
        
        // Store indicator
        this.statusIndicators[id] = {
            element: indicator,
            bar,
            barFill,
            text,
            type: 'cpu',
            options
        };
        
        return indicator;
    }
    
    /**
     * Create a GPU usage indicator
     * @param {string} id - Indicator ID
     * @param {HTMLElement} container - Container element
     * @param {Object} options - Indicator options
     * @returns {HTMLElement} GPU usage indicator element
     */
    createGPUUsageIndicator(id, container, options = {}) {
        // Create GPU usage indicator element
        const indicator = document.createElement('div');
        indicator.className = 'gpu-usage-indicator';
        indicator.id = id;
        
        // Create usage bar
        const bar = document.createElement('div');
        bar.className = 'gpu-usage-bar';
        
        const barFill = document.createElement('div');
        barFill.className = 'gpu-usage-bar-fill';
        bar.appendChild(barFill);
        indicator.appendChild(bar);
        
        // Add text
        const text = document.createElement('div');
        text.className = 'gpu-usage-text';
        text.textContent = '0%';
        indicator.appendChild(text);
        
        // Add to container
        container.appendChild(indicator);
        
        // Store indicator
        this.statusIndicators[id] = {
            element: indicator,
            bar,
            barFill,
            text,
            type: 'gpu',
            options
        };
        
        return indicator;
    }
    
    /**
     * Create a performance indicator
     * @param {string} id - Indicator ID
     * @param {HTMLElement} container - Container element
     * @param {Object} options - Indicator options
     * @returns {HTMLElement} Performance indicator element
     */
    createPerformanceIndicator(id, container, options = {}) {
        // Create performance indicator element
        const indicator = document.createElement('div');
        indicator.className = 'performance-indicator';
        indicator.id = id;
        
        // Create icon
        const icon = document.createElement('div');
        icon.className = 'performance-icon';
        icon.innerHTML = '⚡';
        indicator.appendChild(icon);
        
        // Create bars
        const bars = document.createElement('div');
        bars.className = 'performance-bars';
        
        // Create 5 bars
        for (let i = 0; i < 5; i++) {
            const bar = document.createElement('div');
            bar.className = 'performance-bar';
            bars.appendChild(bar);
        }
        
        indicator.appendChild(bars);
        
        // Add to container
        container.appendChild(indicator);
        
        // Store indicator
        this.statusIndicators[id] = {
            element: indicator,
            icon,
            bars,
            type: 'performance',
            options
        };
        
        return indicator;
    }
    
    /**
     * Update a status indicator
     * @param {string} id - Indicator ID
     * @param {string} status - Status value
     * @param {string} text - Status text
     */
    updateStatusIndicator(id, status, text) {
        const indicator = this.statusIndicators[id];
        if (!indicator) return;
        
        // Update classes
        indicator.element.className = `status-indicator status-${status}`;
        
        // Update text if provided
        if (text !== undefined) {
            indicator.text.textContent = text;
        }
        
        // Announce to screen readers
        this.announceStatusChange(id, status, text);
    }
    
    /**
     * Update a memory usage indicator
     * @param {string} id - Indicator ID
     * @param {number} used - Used memory in MB
     * @param {number} total - Total memory in MB
     */
    updateMemoryUsageIndicator(id, used, total) {
        const indicator = this.statusIndicators[id];
        if (!indicator) return;
        
        // Calculate percentage
        const percentage = total > 0 ? Math.round((used / total) * 100) : 0;
        
        // Update bar
        indicator.barFill.style.width = `${percentage}%`;
        
        // Update text
        indicator.text.textContent = `${percentage}% (${Math.round(used)}MB/${Math.round(total)}MB)`;
        
        // Update status based on percentage
        let status;
        if (percentage < 50) {
            status = 'good';
            indicator.element.className = 'memory-usage-indicator memory-usage-low';
        } else if (percentage < 80) {
            status = 'warning';
            indicator.element.className = 'memory-usage-indicator memory-usage-medium';
        } else {
            status = 'error';
            indicator.element.className = 'memory-usage-indicator memory-usage-high';
        }
        
        // Announce to screen readers
        this.announceStatusChange(id, status, `Memory usage: ${percentage}%`);
    }
    
    /**
     * Update a CPU usage indicator
     * @param {string} id - Indicator ID
     * @param {number} usage - CPU usage percentage
     */
    updateCPUUsageIndicator(id, usage) {
        const indicator = this.statusIndicators[id];
        if (!indicator) return;
        
        // Update bar
        indicator.barFill.style.width = `${usage}%`;
        
        // Update text
        indicator.text.textContent = `${usage}%`;
        
        // Update status based on percentage
        let status;
        if (usage < 50) {
            status = 'good';
            indicator.element.className = 'cpu-usage-indicator cpu-usage-low';
        } else if (usage < 80) {
            status = 'warning';
            indicator.element.className = 'cpu-usage-indicator cpu-usage-medium';
        } else {
            status = 'error';
            indicator.element.className = 'cpu-usage-indicator cpu-usage-high';
        }
        
        // Announce to screen readers
        this.announceStatusChange(id, status, `CPU usage: ${usage}%`);
    }
    
    /**
     * Update a GPU usage indicator
     * @param {string} id - Indicator ID
     * @param {number} usage - GPU usage percentage
     */
    updateGPUUsageIndicator(id, usage) {
        const indicator = this.statusIndicators[id];
        if (!indicator) return;
        
        // Update bar
        indicator.barFill.style.width = `${usage}%`;
        
        // Update text
        indicator.text.textContent = `${usage}%`;
        
        // Update status based on percentage
        let status;
        if (usage < 50) {
            status = 'good';
            indicator.element.className = 'gpu-usage-indicator gpu-usage-low';
        } else if (usage < 80) {
            status = 'warning';
            indicator.element.className = 'gpu-usage-indicator gpu-usage-medium';
        } else {
            status = 'error';
            indicator.element.className = 'gpu-usage-indicator gpu-usage-high';
        }
        
        // Announce to screen readers
        this.announceStatusChange(id, status, `GPU usage: ${usage}%`);
    }
    
    /**
     * Update a performance indicator
     * @param {string} id - Indicator ID
     * @param {number} fps - Frames per second
     */
    updatePerformanceIndicator(id, fps) {
        const indicator = this.statusIndicators[id];
        if (!indicator) return;
        
        // Calculate number of bars to show based on FPS
        let barsToShow;
        let status;
        
        if (fps >= 60) {
            barsToShow = 5;
            status = 'good';
            indicator.element.className = 'performance-indicator performance-good';
        } else if (fps >= 30) {
            barsToShow = 3;
            status = 'fair';
            indicator.element.className = 'performance-indicator performance-fair';
        } else {
            barsToShow = 1;
            status = 'poor';
            indicator.element.className = 'performance-indicator performance-poor';
        }
        
        // Update bars
        const bars = indicator.bars.children;
        for (let i = 0; i < bars.length; i++) {
            if (i < barsToShow) {
                bars[i].classList.add(status);
            } else {
                bars[i].className = 'performance-bar';
            }
        }
        
        // Announce to screen readers
        this.announceStatusChange(id, status, `Performance: ${fps} FPS`);
    }
    
    /**
     * Start monitoring system status
     */
    startMonitoring() {
        if (this.isMonitoring) return;
        
        this.isMonitoring = true;
        this.monitoringInterval = setInterval(() => {
            this.updateSystemStatus();
        }, this.updateInterval);
        
        // Initial update
        this.updateSystemStatus();
    }
    
    /**
     * Stop monitoring system status
     */
    stopMonitoring() {
        if (!this.isMonitoring) return;
        
        this.isMonitoring = false;
        clearInterval(this.monitoringInterval);
    }
    
    /**
     * Update system status
     */
    updateSystemStatus() {
        // Get system metrics
        const memoryUsage = this.getMemoryUsage();
        const cpuUsage = this.getCPUUsage();
        const gpuUsage = this.getGPUUsage();
        const performance = this.getPerformanceMetrics();
        
        // Update indicators
        Object.keys(this.statusIndicators).forEach(id => {
            const indicator = this.statusIndicators[id];
            
            switch (indicator.type) {
                case 'memory':
                    this.updateMemoryUsageIndicator(id, memoryUsage.used, memoryUsage.total);
                    break;
                case 'cpu':
                    this.updateCPUUsageIndicator(id, cpuUsage);
                    break;
                case 'gpu':
                    this.updateGPUUsageIndicator(id, gpuUsage);
                    break;
                case 'performance':
                    this.updatePerformanceIndicator(id, performance.fps);
                    break;
            }
        });
        
        // Call callbacks
        Object.keys(this.callbacks).forEach(event => {
            if (this.callbacks[event]) {
                this.callbacks[event]({
                    memoryUsage,
                    cpuUsage,
                    gpuUsage,
                    performance
                });
            }
        });
    }
    
    /**
     * Get memory usage
     * @returns {Object} Memory usage information
     */
    getMemoryUsage() {
        // In a real implementation, this would get actual memory usage
        // For now, return simulated values
        const total = this.getDeviceMemory() * 1024; // Convert GB to MB
        const used = Math.random() * total * 0.8; // Use up to 80% of total
        
        return { used, total };
    }
    
    /**
     * Get CPU usage
     * @returns {number} CPU usage percentage
     */
    getCPUUsage() {
        // In a real implementation, this would get actual CPU usage
        // For now, return a simulated value
        return Math.random() * 100;
    }
    
    /**
     * Get GPU usage
     * @returns {number} GPU usage percentage
     */
    getGPUUsage() {
        // In a real implementation, this would get actual GPU usage
        // For now, return a simulated value
        return Math.random() * 100;
    }
    
    /**
     * Get performance metrics
     * @returns {Object} Performance metrics
     */
    getPerformanceMetrics() {
        // In a real implementation, this would get actual performance metrics
        // For now, return simulated values
        return {
            fps: 30 + Math.random() * 60, // 30-90 FPS
            renderTime: 5 + Math.random() * 15, // 5-20ms
            frameTime: 10 + Math.random() * 20 // 10-30ms
        };
    }
    
    /**
     * Get device memory
     * @returns {number} Device memory in GB
     */
    getDeviceMemory() {
        if (navigator.deviceMemory) {
            return navigator.deviceMemory;
        }
        return 4; // Default assumption
    }
    
    /**
     * Get CPU cores
     * @returns {number} Number of CPU cores
     */
    getCPUCores() {
        if (navigator.hardwareConcurrency) {
            return navigator.hardwareConcurrency;
        }
        return 4; // Default assumption
    }
    
    /**
     * Add a callback for system status updates
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
     * Remove a callback for system status updates
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
     * Announce status change to screen readers
     * @param {string} id - Indicator ID
     * @param {string} status - Status value
     * @param {string} text - Status text
     */
    announceStatusChange(id, status, text) {
        // Create live region if it doesn't exist
        let liveRegion = document.getElementById('status-live-region');
        if (!liveRegion) {
            liveRegion = document.createElement('div');
            liveRegion.id = 'status-live-region';
            liveRegion.setAttribute('aria-live', 'polite');
            liveRegion.setAttribute('aria-atomic', 'true');
            liveRegion.className = 'sr-only';
            document.body.appendChild(liveRegion);
        }
        
        // Announce to screen reader
        liveRegion.textContent = `${id}: ${status} - ${text}`;
        
        // Clear after announcement
        setTimeout(() => {
            liveRegion.textContent = '';
        }, 100);
    }
}

// Create global system status monitor
const systemStatusMonitor = new SystemStatusMonitor();

// ================================
// STATUS PANEL
// ================================

/**
 * Status panel for displaying detailed system status
 */
class StatusPanel {
    constructor(container) {
        this.container = container;
        this.isVisible = false;
        this.refreshInterval = 2000; // ms
        this.createPanel();
    }
    
    /**
     * Create status panel
     */
    createPanel() {
        // Create panel element
        this.panel = document.createElement('div');
        this.panel.className = 'status-panel';
        this.panel.style.display = 'none';
        
        // Create header
        const header = document.createElement('div');
        header.className = 'status-panel-header';
        
        // Create title
        const title = document.createElement('div');
        title.className = 'status-panel-title';
        title.textContent = 'System Status';
        header.appendChild(title);
        
        // Create refresh button
        const refreshButton = document.createElement('button');
        refreshButton.className = 'status-panel-refresh';
        refreshButton.innerHTML = '↻';
        refreshButton.setAttribute('aria-label', 'Refresh status');
        refreshButton.addEventListener('click', () => {
            this.refresh();
        });
        header.appendChild(refreshButton);
        
        this.panel.appendChild(header);
        
        // Create content
        this.content = document.createElement('div');
        this.content.className = 'status-panel-content';
        this.panel.appendChild(this.content);
        
        // Create sections
        this.createMemorySection();
        this.createCPUSection();
        this.createGPUSection();
        this.createPerformanceSection();
        
        // Add to container
        this.container.appendChild(this.panel);
        
        // Set up refresh interval
        this.refreshIntervalId = setInterval(() => {
            if (this.isVisible) {
                this.refresh();
            }
        }, this.refreshInterval);
    }
    
    /**
     * Create memory section
     */
    createMemorySection() {
        // Create section
        const section = document.createElement('div');
        section.className = 'status-panel-section';
        
        // Create header
        const header = document.createElement('div');
        header.className = 'status-panel-section-header';
        header.textContent = 'Memory';
        section.appendChild(header);
        
        // Create content
        const content = document.createElement('div');
        content.className = 'status-panel-section-content';
        
        // Create total item
        const totalItem = document.createElement('div');
        totalItem.className = 'status-panel-item';
        
        const totalLabel = document.createElement('div');
        totalLabel.className = 'status-panel-item-label';
        totalLabel.textContent = 'Total:';
        totalItem.appendChild(totalLabel);
        
        this.memoryTotal = document.createElement('div');
        this.memoryTotal.className = 'status-panel-item-value';
        this.memoryTotal.textContent = '0 MB';
        totalItem.appendChild(this.memoryTotal);
        
        content.appendChild(totalItem);
        
        // Create used item
        const usedItem = document.createElement('div');
        usedItem.className = 'status-panel-item';
        
        const usedLabel = document.createElement('div');
        usedLabel.className = 'status-panel-item-label';
        usedLabel.textContent = 'Used:';
        usedItem.appendChild(usedLabel);
        
        this.memoryUsed = document.createElement('div');
        this.memoryUsed.className = 'status-panel-item-value';
        this.memoryUsed.textContent = '0 MB';
        usedItem.appendChild(this.memoryUsed);
        
        content.appendChild(usedItem);
        
        // Create percentage item
        const percentageItem = document.createElement('div');
        percentageItem.className = 'status-panel-item';
        
        const percentageLabel = document.createElement('div');
        percentageLabel.className = 'status-panel-item-label';
        percentageLabel.textContent = 'Usage:';
        percentageItem.appendChild(percentageLabel);
        
        this.memoryPercentage = document.createElement('div');
        this.memoryPercentage.className = 'status-panel-item-value';
        this.memoryPercentage.textContent = '0%';
        percentageItem.appendChild(this.memoryPercentage);
        
        content.appendChild(percentageItem);
        
        section.appendChild(content);
        this.content.appendChild(section);
    }
    
    /**
     * Create CPU section
     */
    createCPUSection() {
        // Create section
        const section = document.createElement('div');
        section.className = 'status-panel-section';
        
        // Create header
        const header = document.createElement('div');
        header.className = 'status-panel-section-header';
        header.textContent = 'CPU';
        section.appendChild(header);
        
        // Create content
        const content = document.createElement('div');
        content.className = 'status-panel-section-content';
        
        // Create usage item
        const usageItem = document.createElement('div');
        usageItem.className = 'status-panel-item';
        
        const usageLabel = document.createElement('div');
        usageLabel.className = 'status-panel-item-label';
        usageLabel.textContent = 'Usage:';
        usageItem.appendChild(usageLabel);
        
        this.cpuUsage = document.createElement('div');
        this.cpuUsage.className = 'status-panel-item-value';
        this.cpuUsage.textContent = '0%';
        usageItem.appendChild(this.cpuUsage);
        
        content.appendChild(usageItem);
        
        // Create cores item
        const coresItem = document.createElement('div');
        coresItem.className = 'status-panel-item';
        
        const coresLabel = document.createElement('div');
        coresLabel.className = 'status-panel-item-label';
        coresLabel.textContent = 'Cores:';
        coresItem.appendChild(coresLabel);
        
        const coresValue = document.createElement('div');
        coresValue.className = 'status-panel-item-value';
        coresValue.textContent = systemStatusMonitor.getCPUCores();
        coresItem.appendChild(coresValue);
        
        content.appendChild(coresItem);
        
        section.appendChild(content);
        this.content.appendChild(section);
    }
    
    /**
     * Create GPU section
     */
    createGPUSection() {
        // Create section
        const section = document.createElement('div');
        section.className = 'status-panel-section';
        
        // Create header
        const header = document.createElement('div');
        header.className = 'status-panel-section-header';
        header.textContent = 'GPU';
        section.appendChild(header);
        
        // Create content
        const content = document.createElement('div');
        content.className = 'status-panel-section-content';
        
        // Create usage item
        const usageItem = document.createElement('div');
        usageItem.className = 'status-panel-item';
        
        const usageLabel = document.createElement('div');
        usageLabel.className = 'status-panel-item-label';
        usageLabel.textContent = 'Usage:';
        usageItem.appendChild(usageLabel);
        
        this.gpuUsage = document.createElement('div');
        this.gpuUsage.className = 'status-panel-item-value';
        this.gpuUsage.textContent = '0%';
        usageItem.appendChild(this.gpuUsage);
        
        content.appendChild(usageItem);
        
        // Create available item
        const availableItem = document.createElement('div');
        availableItem.className = 'status-panel-item';
        
        const availableLabel = document.createElement('div');
        availableLabel.className = 'status-panel-item-label';
        availableLabel.textContent = 'Available:';
        availableItem.appendChild(availableLabel);
        
        const availableValue = document.createElement('div');
        availableValue.className = 'status-panel-item-value';
        availableValue.textContent = 'Unknown';
        availableItem.appendChild(availableValue);
        
        content.appendChild(availableItem);
        
        section.appendChild(content);
        this.content.appendChild(section);
    }
    
    /**
     * Create performance section
     */
    createPerformanceSection() {
        // Create section
        const section = document.createElement('div');
        section.className = 'status-panel-section';
        
        // Create header
        const header = document.createElement('div');
        header.className = 'status-panel-section-header';
        header.textContent = 'Performance';
        section.appendChild(header);
        
        // Create content
        const content = document.createElement('div');
        content.className = 'status-panel-section-content';
        
        // Create FPS item
        const fpsItem = document.createElement('div');
        fpsItem.className = 'status-panel-item';
        
        const fpsLabel = document.createElement('div');
        fpsLabel.className = 'status-panel-item-label';
        fpsLabel.textContent = 'FPS:';
        fpsItem.appendChild(fpsLabel);
        
        this.fpsValue = document.createElement('div');
        this.fpsValue.className = 'status-panel-item-value';
        this.fpsValue.textContent = '0';
        fpsItem.appendChild(this.fpsValue);
        
        content.appendChild(fpsItem);
        
        // Create render time item
        const renderItem = document.createElement('div');
        renderItem.className = 'status-panel-item';
        
        const renderLabel = document.createElement('div');
        renderLabel.className = 'status-panel-item-label';
        renderLabel.textContent = 'Render:';
        renderItem.appendChild(renderLabel);
        
        this.renderValue = document.createElement('div');
        this.renderValue.className = 'status-panel-item-value';
        this.renderValue.textContent = '0ms';
        renderItem.appendChild(this.renderValue);
        
        content.appendChild(renderItem);
        
        // Create frame time item
        const frameItem = document.createElement('div');
        frameItem.className = 'status-panel-item';
        
        const frameLabel = document.createElement('div');
        frameLabel.className = 'status-panel-item-label';
        frameLabel.textContent = 'Frame:';
        frameItem.appendChild(frameLabel);
        
        this.frameValue = document.createElement('div');
        this.frameValue.className = 'status-panel-item-value';
        this.frameValue.textContent = '0ms';
        frameItem.appendChild(this.frameValue);
        
        content.appendChild(frameItem);
        
        section.appendChild(content);
        this.content.appendChild(section);
    }
    
    /**
     * Show status panel
     */
    show() {
        this.panel.style.display = 'block';
        this.isVisible = true;
        this.refresh();
    }
    
    /**
     * Hide status panel
     */
    hide() {
        this.panel.style.display = 'none';
        this.isVisible = false;
    }
    
    /**
     * Toggle status panel visibility
     */
    toggle() {
        if (this.isVisible) {
            this.hide();
        } else {
            this.show();
        }
    }
    
    /**
     * Refresh status panel
     */
    refresh() {
        // Get system metrics
        const memoryUsage = systemStatusMonitor.getMemoryUsage();
        const cpuUsage = systemStatusMonitor.getCPUUsage();
        const gpuUsage = systemStatusMonitor.getGPUUsage();
        const performance = systemStatusMonitor.getPerformanceMetrics();
        
        // Update memory section
        this.memoryTotal.textContent = `${Math.round(memoryUsage.total)} MB`;
        this.memoryUsed.textContent = `${Math.round(memoryUsage.used)} MB`;
        this.memoryPercentage.textContent = `${Math.round((memoryUsage.used / memoryUsage.total) * 100)}%`;
        
        // Update CPU section
        this.cpuUsage.textContent = `${Math.round(cpuUsage)}%`;
        
        // Update GPU section
        this.gpuUsage.textContent = `${Math.round(gpuUsage)}%`;
        
        // Update performance section
        this.fpsValue.textContent = Math.round(performance.fps);
        this.renderValue.textContent = `${Math.round(performance.renderTime)}ms`;
        this.frameValue.textContent = `${Math.round(performance.frameTime)}ms`;
    }
}

// ================================
// STATUS BAR INDICATORS
// ================================

/**
 * Status bar indicators manager
 */
class StatusBarIndicators {
    constructor(statusBar) {
        this.statusBar = statusBar;
        this.indicators = {};
        this.container = this.createContainer();
    }
    
    /**
     * Create container for indicators
     * @returns {HTMLElement} Container element
     */
    createContainer() {
        // Create container
        const container = document.createElement('div');
        container.className = 'status-bar-indicators';
        
        // Add to status bar
        this.statusBar.appendChild(container);
        
        return container;
    }
    
    /**
     * Add an indicator to the status bar
     * @param {string} id - Indicator ID
     * @param {string} status - Initial status
     * @param {string} text - Initial text
     * @returns {HTMLElement} Indicator element
     */
    addIndicator(id, status, text) {
        // Create indicator
        const indicator = document.createElement('div');
        indicator.className = `status-bar-indicator status-${status}`;
        indicator.id = id;
        
        // Create icon
        const icon = document.createElement('div');
        icon.className = 'status-bar-indicator-icon';
        indicator.appendChild(icon);
        
        // Create text
        const textElement = document.createElement('div');
        textElement.className = 'status-bar-indicator-text';
        textElement.textContent = text;
        indicator.appendChild(textElement);
        
        // Add to container
        this.container.appendChild(indicator);
        
        // Store indicator
        this.indicators[id] = {
            element: indicator,
            icon,
            text: textElement
        };
        
        return indicator;
    }
    
    /**
     * Update an indicator
     * @param {string} id - Indicator ID
     * @param {string} status - New status
     * @param {string} text - New text
     */
    updateIndicator(id, status, text) {
        const indicator = this.indicators[id];
        if (!indicator) return;
        
        // Update classes
        indicator.element.className = `status-bar-indicator status-${status}`;
        
        // Update text if provided
        if (text !== undefined) {
            indicator.text.textContent = text;
        }
    }
    
    /**
     * Remove an indicator
     * @param {string} id - Indicator ID
     */
    removeIndicator(id) {
        const indicator = this.indicators[id];
        if (!indicator) return;
        
        // Remove from container
        this.container.removeChild(indicator.element);
        
        // Remove from storage
        delete this.indicators[id];
    }
}

// ================================
// PYTHON IMPLEMENTATION NOTES
// ================================

/*
Below are notes on how to implement these status indicator features in Python/PySide6:

1. System Status Monitor:
```python
import psutil
import time
from PySide6.QtCore import QObject, QTimer, Signal

class SystemStatusMonitor(QObject):
    status_updated = Signal(dict)  # System status data
    
    def __init__(self):
        super().__init__()
        self.status_indicators = {}
        self.update_interval = 1000  # ms
        self.is_monitoring = False
        self.callbacks = {}
        self.performance_mode = self.detect_performance_mode()
        self.setup_performance_monitoring()
    
    def detect_performance_mode(self):
        # Check device capabilities
        memory = self.get_device_memory()
        cores = self.get_cpu_cores()
        
        if memory > 4 and cores > 4:
            return 'high'
        elif memory > 2 and cores > 2:
            return 'medium'
        else:
            return 'low'
    
    def setup_performance_monitoring(self):
        if self.performance_mode == 'high':
            self.update_interval = 500  # Update more frequently
        elif self.performance_mode == 'medium':
            self.update_interval = 1000  # Standard update frequency
        else:  # low
            self.update_interval = 2000  # Update less frequently
    
    def create_status_indicator(self, indicator_id, indicator_type, parent, options=None):
        # Create status indicator widget
        indicator = QWidget(parent)
        indicator.setObjectName(indicator_id)
        indicator.setStyleSheet("""
            QWidget {
                display: flex;
                align-items: center;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 8pt;
            }
        """)
        
        # Create layout
        layout = QHBoxLayout(indicator)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Create icon
        icon = QLabel()
        icon.setFixedSize(10, 10)
        icon.setStyleSheet("""
            QLabel {
                border-radius: 50%;
                background-color: #28a745;
            }
        """)
        layout.addWidget(icon)
        
        # Create text
        text = QLabel(options.get('text', '') if options else '')
        layout.addWidget(text)
        
        # Store indicator
        self.status_indicators[indicator_id] = {
            'widget': indicator,
            'icon': icon,
            'text': text,
            'type': indicator_type,
            'options': options or {}
        }
        
        return indicator
    
    def create_memory_usage_indicator(self, indicator_id, parent, options=None):
        # Create memory usage indicator widget
        indicator = QWidget(parent)
        indicator.setObjectName(indicator_id)
        indicator.setStyleSheet("""
            QWidget {
                display: flex;
                align-items: center;
                padding: 2px 6px;
                border-radius: 4px;
                font-size: 8pt;
                background-color: #f5f5f5;
                border: 1px solid #d0d0d0;
            }
        """)
        
        # Create layout
        layout = QHBoxLayout(indicator)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        
        # Create progress bar
        progress_bar = QProgressBar()
        progress_bar.setFixedWidth(40)
        progress_bar.setFixedHeight(8)
        progress_bar.setTextVisible(False)
        progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background-color: #e0e0e0;
            }
            QProgressBar::chunk {
                border-radius: 4px;
                background-color: #28a745;
            }
        """)
        layout.addWidget(progress_bar)
        
        # Create text
        text = QLabel("0%")
        layout.addWidget(text)
        
        # Store indicator
        self.status_indicators[indicator_id] = {
            'widget': indicator,
            'progress_bar': progress_bar,
            'text': text,
            'type': 'memory',
            'options': options or {}
        }
        
        return indicator
    
    def update_memory_usage_indicator(self, indicator_id, used, total):
        indicator = self.status_indicators.get(indicator_id)
        if not indicator:
            return
        
        # Calculate percentage
        percentage = int((used / total) * 100) if total > 0 else 0
        
        # Update progress bar
        indicator['progress_bar'].setValue(percentage)
        
        # Update text
        indicator['text'].setText(f"{percentage}% ({int(used)}MB/{int(total)}MB)")
        
        # Update status based on percentage
        if percentage < 50:
            status = 'good'
            color = '#28a745'
        elif percentage < 80:
            status = 'warning'
            color = '#ffc107'
        else:
            status = 'error'
            color = '#dc3545'
        
        # Update progress bar color
        indicator['progress_bar'].setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background-color: #e0e0e0;
            }}
            QProgressBar::chunk {{
                border-radius: 4px;
                background-color: {color};
            }}
        """)
        
        # Announce to screen readers
        self.announce_status_change(indicator_id, status, f"Memory usage: {percentage}%")
    
    def start_monitoring(self):
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitoring_timer = QTimer()
        self.monitoring_timer.timeout.connect(self.update_system_status)
        self.monitoring_timer.start(self.update_interval)
        
        # Initial update
        self.update_system_status()
    
    def stop_monitoring(self):
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        self.monitoring_timer.stop()
    
    def update_system_status(self):
        try:
            # Get system metrics
            memory_info = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent()
            
            # Get GPU usage if available
            gpu_percent = 0
            try:
                import GPUtil
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu_percent = gpus[0].load * 100
            except:
                pass
            
            # Update indicators
            for indicator_id, indicator in self.status_indicators.items():
                if indicator['type'] == 'memory':
                    self.update_memory_usage_indicator(
                        indicator_id, 
                        memory_info.used, 
                        memory_info.total
                    )
                elif indicator['type'] == 'cpu':
                    self.update_cpu_usage_indicator(indicator_id, cpu_percent)
                elif indicator['type'] == 'gpu':
                    self.update_gpu_usage_indicator(indicator_id, gpu_percent)
            
            # Emit signal
            self.status_updated.emit({
                'memory_usage': {
                    'used': memory_info.used,
                    'total': memory_info.total
                },
                'cpu_usage': cpu_percent,
                'gpu_usage': gpu_percent
            })
            
        except Exception as e:
            print(f"Error updating system status: {e}")
    
    def get_memory_usage(self):
        try:
            memory_info = psutil.virtual_memory()
            return {
                'used': memory_info.used,
                'total': memory_info.total
            }
        except:
            return {'used': 0, 'total': 0}
    
    def get_cpu_usage(self):
        try:
            return psutil.cpu_percent()
        except:
            return 0
    
    def get_gpu_usage(self):
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                return gpus[0].load * 100
        except:
            pass
        return 0
```

2. Status Panel:
```python
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PySide6.QtCore import QTimer, Qt

class StatusPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_visible = False
        self.refresh_interval = 2000  # ms
        self.setup_ui()
        self.setup_refresh_timer()
    
    def setup_ui(self):
        # Set main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        
        # Create header
        header_layout = QHBoxLayout()
        
        # Create title
        title = QLabel("System Status")
        title.setStyleSheet("font-size: 10pt; font-weight: bold; color: #333333;")
        header_layout.addWidget(title)
        
        # Add stretch
        header_layout.addStretch()
        
        # Create refresh button
        self.refresh_button = QPushButton("↻")
        self.refresh_button.setFixedSize(16, 16)
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background: none;
                border: none;
                color: #666666;
            }
            QPushButton:hover {
                color: #0078d4;
            }
        """)
        self.refresh_button.clicked.connect(self.refresh)
        header_layout.addWidget(self.refresh_button)
        
        layout.addLayout(header_layout)
        
        # Create separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)
        
        # Create content
        self.content_layout = QVBoxLayout()
        layout.addLayout(self.content_layout)
        
        # Create sections
        self.create_memory_section()
        self.create_cpu_section()
        self.create_gpu_section()
        self.create_performance_section()
    
    def create_memory_section(self):
        # Create section
        section = QWidget()
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(2)
        
        # Create header
        header = QLabel("Memory")
        header.setStyleSheet("font-size: 9pt; font-weight: bold; color: #333333;")
        section_layout.addWidget(header)
        
        # Create content
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(8, 0, 0, 0)
        content_layout.setSpacing(2)
        
        # Create total item
        total_layout = QHBoxLayout()
        total_label = QLabel("Total:")
        total_layout.addWidget(total_label)
        
        self.memory_total = QLabel("0 MB")
        self.memory_total.setStyleSheet("font-weight: bold; color: #333333;")
        total_layout.addWidget(self.memory_total)
        
        total_layout.addStretch()
        content_layout.addLayout(total_layout)
        
        # Create used item
        used_layout = QHBoxLayout()
        used_label = QLabel("Used:")
        used_layout.addWidget(used_label)
        
        self.memory_used = QLabel("0 MB")
        self.memory_used.setStyleSheet("font-weight: bold; color: #333333;")
        used_layout.addWidget(self.memory_used)
        
        used_layout.addStretch()
        content_layout.addLayout(used_layout)
        
        # Create percentage item
        percentage_layout = QHBoxLayout()
        percentage_label = QLabel("Usage:")
        percentage_layout.addWidget(percentage_label)
        
        self.memory_percentage = QLabel("0%")
        self.memory_percentage.setStyleSheet("font-weight: bold; color: #333333;")
        percentage_layout.addWidget(self.memory_percentage)
        
        percentage_layout.addStretch()
        content_layout.addLayout(percentage_layout)
        
        section_layout.addLayout(content_layout)
        self.content_layout.addWidget(section)
    
    def create_cpu_section(self):
        # Similar implementation for CPU section
        pass
    
    def create_gpu_section(self):
        # Similar implementation for GPU section
        pass
    
    def create_performance_section(self):
        # Similar implementation for performance section
        pass
    
    def setup_refresh_timer(self):
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_if_visible)
        self.refresh_timer.start(self.refresh_interval)
    
    def refresh_if_visible(self):
        if self.is_visible:
            self.refresh()
    
    def showEvent(self, event):
        super().showEvent(event)
        self.is_visible = True
        self.refresh()
    
    def hideEvent(self, event):
        super().hideEvent(event)
        self.is_visible = False
    
    def refresh(self):
        try:
            # Get system metrics
            memory_info = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent()
            
            # Update memory section
            self.memory_total.setText(f"{memory_info.total // (1024**2)} MB")
            self.memory_used.setText(f"{memory_info.used // (1024**2)} MB")
            self.memory_percentage.setText(f"{memory_info.percent}%")
            
            # Update other sections
            # ...
            
        except Exception as e:
            print(f"Error refreshing status panel: {e}")
```
*/