/**
 * Visual Feedback Implementations for 3D-MM Application
 * 
 * This JavaScript file demonstrates how to implement visual feedback for user actions,
 * which can be translated to the Python/PySide6 application.
 */

// ================================
// VISUAL FEEDBACK MANAGER
// ================================

/**
 * Visual feedback manager for handling user interaction feedback
 */
class VisualFeedbackManager {
    constructor() {
        this.feedbackEnabled = true;
        this.feedbackDuration = 300; // ms
        this.animationDuration = 200; // ms
        this.performanceMode = this.detectPerformanceMode();
        this.configureFeedbackSettings();
    }
    
    /**
     * Detect performance mode to adjust feedback intensity
     * @returns {string} Performance mode
     */
    detectPerformanceMode() {
        // Check for reduced motion preference
        if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            return 'low';
        }
        
        // Check device capabilities
        const hasHardwareAcceleration = this.checkHardwareAcceleration();
        const memory = this.getDeviceMemory();
        const cores = this.getCPUCores();
        
        if (hasHardwareAcceleration && memory > 4 && cores > 4) {
            return 'high';
        } else if (memory > 2 && cores > 2) {
            return 'medium';
        } else {
            return 'low';
        }
    }
    
    /**
     * Configure feedback settings based on performance mode
     */
    configureFeedbackSettings() {
        switch (this.performanceMode) {
            case 'high':
                this.feedbackDuration = 300;
                this.animationDuration = 300;
                this.enableTransforms = true;
                this.enableShadows = true;
                this.enableTransitions = true;
                break;
            case 'medium':
                this.feedbackDuration = 200;
                this.animationDuration = 200;
                this.enableTransforms = true;
                this.enableShadows = false;
                this.enableTransitions = true;
                break;
            case 'low':
                this.feedbackDuration = 100;
                this.animationDuration = 100;
                this.enableTransforms = false;
                this.enableShadows = false;
                this.enableTransitions = false;
                break;
        }
    }
    
    /**
     * Show hover feedback for an element
     * @param {HTMLElement} element - Element to show feedback for
     */
    showHoverFeedback(element) {
        if (!this.feedbackEnabled) return;
        
        // Add hover class
        element.classList.add('hover-feedback');
        
        // Apply transform if enabled
        if (this.enableTransforms) {
            element.style.transform = 'translateY(-1px)';
        }
        
        // Apply shadow if enabled
        if (this.enableShadows) {
            element.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.1)';
        }
    }
    
    /**
     * Remove hover feedback from an element
     * @param {HTMLElement} element - Element to remove feedback from
     */
    removeHoverFeedback(element) {
        // Remove hover class
        element.classList.remove('hover-feedback');
        
        // Reset styles
        element.style.transform = '';
        element.style.boxShadow = '';
    }
    
    /**
     * Show active feedback for an element
     * @param {HTMLElement} element - Element to show feedback for
     */
    showActiveFeedback(element) {
        if (!this.feedbackEnabled) return;
        
        // Add active class
        element.classList.add('active-feedback');
        
        // Apply transform if enabled
        if (this.enableTransforms) {
            element.style.transform = 'translateY(0px)';
        }
        
        // Apply shadow if enabled
        if (this.enableShadows) {
            element.style.boxShadow = '0 1px 2px rgba(0, 0, 0, 0.1)';
        }
    }
    
    /**
     * Remove active feedback from an element
     * @param {HTMLElement} element - Element to remove feedback from
     */
    removeActiveFeedback(element) {
        // Remove active class
        element.classList.remove('active-feedback');
        
        // Reset styles
        element.style.transform = '';
        element.style.boxShadow = '';
    }
    
    /**
     * Show success feedback for an element
     * @param {HTMLElement} element - Element to show feedback for
     * @param {string} message - Success message
     */
    showSuccessFeedback(element, message) {
        if (!this.feedbackEnabled) return;
        
        // Add success class
        element.classList.add('success-feedback');
        
        // Show success message
        this.showTemporaryMessage(element, message, 'success');
        
        // Remove feedback after duration
        setTimeout(() => {
            element.classList.remove('success-feedback');
        }, this.feedbackDuration);
    }
    
    /**
     * Show error feedback for an element
     * @param {HTMLElement} element - Element to show feedback for
     * @param {string} message - Error message
     */
    showErrorFeedback(element, message) {
        if (!this.feedbackEnabled) return;
        
        // Add error class
        element.classList.add('error-feedback');
        
        // Show error message
        this.showTemporaryMessage(element, message, 'error');
        
        // Add shake animation if enabled
        if (this.enableTransforms) {
            this.shakeElement(element);
        }
        
        // Remove feedback after duration
        setTimeout(() => {
            element.classList.remove('error-feedback');
        }, this.feedbackDuration);
    }
    
    /**
     * Show loading feedback for an element
     * @param {HTMLElement} element - Element to show feedback for
     */
    showLoadingFeedback(element) {
        if (!this.feedbackEnabled) return;
        
        // Add loading class
        element.classList.add('loading-feedback');
        
        // Disable element
        element.disabled = true;
        
        // Add loading spinner
        this.addLoadingSpinner(element);
    }
    
    /**
     * Remove loading feedback from an element
     * @param {HTMLElement} element - Element to remove feedback from
     */
    removeLoadingFeedback(element) {
        // Remove loading class
        element.classList.remove('loading-feedback');
        
        // Enable element
        element.disabled = false;
        
        // Remove loading spinner
        this.removeLoadingSpinner(element);
    }
    
    /**
     * Show focus feedback for an element
     * @param {HTMLElement} element - Element to show feedback for
     */
    showFocusFeedback(element) {
        if (!this.feedbackEnabled) return;
        
        // Add focus class
        element.classList.add('focus-feedback');
        
        // Apply focus styles
        element.style.outline = '2px solid #0078d4';
        element.style.outlineOffset = '1px';
    }
    
    /**
     * Remove focus feedback from an element
     * @param {HTMLElement} element - Element to remove feedback from
     */
    removeFocusFeedback(element) {
        // Remove focus class
        element.classList.remove('focus-feedback');
        
        // Reset styles
        element.style.outline = '';
        element.style.outlineOffset = '';
    }
    
    /**
     * Show drag over feedback for an element
     * @param {HTMLElement} element - Element to show feedback for
     */
    showDragOverFeedback(element) {
        if (!this.feedbackEnabled) return;
        
        // Add drag over class
        element.classList.add('drag-over-feedback');
        
        // Apply drag over styles
        element.style.border = '2px dashed #0078d4';
        element.style.backgroundColor = 'rgba(0, 120, 212, 0.05)';
    }
    
    /**
     * Remove drag over feedback from an element
     * @param {HTMLElement} element - Element to remove feedback from
     */
    removeDragOverFeedback(element) {
        // Remove drag over class
        element.classList.remove('drag-over-feedback');
        
        // Reset styles
        element.style.border = '';
        element.style.backgroundColor = '';
    }
    
    /**
     * Show drop valid feedback for an element
     * @param {HTMLElement} element - Element to show feedback for
     */
    showDropValidFeedback(element) {
        if (!this.feedbackEnabled) return;
        
        // Add drop valid class
        element.classList.add('drop-valid-feedback');
        
        // Apply drop valid styles
        element.style.border = '2px solid #28a745';
        element.style.backgroundColor = 'rgba(40, 167, 69, 0.05)';
        
        // Remove feedback after duration
        setTimeout(() => {
            element.classList.remove('drop-valid-feedback');
            element.style.border = '';
            element.style.backgroundColor = '';
        }, this.feedbackDuration);
    }
    
    /**
     * Show drop invalid feedback for an element
     * @param {HTMLElement} element - Element to show feedback for
     */
    showDropInvalidFeedback(element) {
        if (!this.feedbackEnabled) return;
        
        // Add drop invalid class
        element.classList.add('drop-invalid-feedback');
        
        // Apply drop invalid styles
        element.style.border = '2px solid #dc3545';
        element.style.backgroundColor = 'rgba(220, 53, 69, 0.05)';
        
        // Add shake animation if enabled
        if (this.enableTransforms) {
            this.shakeElement(element);
        }
        
        // Remove feedback after duration
        setTimeout(() => {
            element.classList.remove('drop-invalid-feedback');
            element.style.border = '';
            element.style.backgroundColor = '';
        }, this.feedbackDuration);
    }
    
    /**
     * Shake an element to indicate error
     * @param {HTMLElement} element - Element to shake
     */
    shakeElement(element) {
        element.style.animation = 'shake 0.5s';
        
        // Remove animation after completion
        setTimeout(() => {
            element.style.animation = '';
        }, 500);
    }
    
    /**
     * Add loading spinner to an element
     * @param {HTMLElement} element - Element to add spinner to
     */
    addLoadingSpinner(element) {
        // Create spinner
        const spinner = document.createElement('div');
        spinner.className = 'loading-spinner';
        
        // Position spinner
        spinner.style.position = 'absolute';
        spinner.style.top = '50%';
        spinner.style.left = '50%';
        spinner.style.transform = 'translate(-50%, -50%)';
        
        // Add to element
        element.style.position = 'relative';
        element.appendChild(spinner);
    }
    
    /**
     * Remove loading spinner from an element
     * @param {HTMLElement} element - Element to remove spinner from
     */
    removeLoadingSpinner(element) {
        // Find and remove spinner
        const spinner = element.querySelector('.loading-spinner');
        if (spinner) {
            element.removeChild(spinner);
        }
    }
    
    /**
     * Show a temporary message
     * @param {HTMLElement} element - Element to show message for
     * @param {string} message - Message to show
     * @param {string} type - Message type (success, error, info)
     */
    showTemporaryMessage(element, message, type) {
        // Create message element
        const messageElement = document.createElement('div');
        messageElement.className = `temporary-message ${type}`;
        messageElement.textContent = message;
        
        // Style message element
        messageElement.style.position = 'absolute';
        messageElement.style.top = '-30px';
        messageElement.style.left = '50%';
        messageElement.style.transform = 'translateX(-50%)';
        messageElement.style.padding = '4px 8px';
        messageElement.style.borderRadius = '4px';
        messageElement.style.fontSize = '12px';
        messageElement.style.whiteSpace = 'nowrap';
        messageElement.style.zIndex = '1000';
        
        // Set color based on type
        switch (type) {
            case 'success':
                messageElement.style.backgroundColor = '#d4edda';
                messageElement.style.color = '#155724';
                messageElement.style.border = '1px solid #c3e6cb';
                break;
            case 'error':
                messageElement.style.backgroundColor = '#f8d7da';
                messageElement.style.color = '#721c24';
                messageElement.style.border = '1px solid #f5c6cb';
                break;
            default:
                messageElement.style.backgroundColor = '#d1ecf1';
                messageElement.style.color = '#0c5460';
                messageElement.style.border = '1px solid #bee5eb';
        }
        
        // Add to element
        element.style.position = 'relative';
        element.appendChild(messageElement);
        
        // Remove after duration
        setTimeout(() => {
            if (element.contains(messageElement)) {
                element.removeChild(messageElement);
            }
        }, this.feedbackDuration);
    }
    
    /**
     * Enable or disable feedback
     * @param {boolean} enabled - Whether to enable feedback
     */
    setFeedbackEnabled(enabled) {
        this.feedbackEnabled = enabled;
    }
    
    /**
     * Check for hardware acceleration
     * @returns {boolean} Whether hardware acceleration is available
     */
    checkHardwareAcceleration() {
        // Create a test canvas
        const canvas = document.createElement('canvas');
        const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
        
        return gl !== null;
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
}

// Create global visual feedback manager
const visualFeedbackManager = new VisualFeedbackManager();

// ================================
// VISUAL FEEDBACK EVENT HANDLERS
// ================================

/**
 * Set up visual feedback event handlers for interactive elements
 */
function setupVisualFeedbackEventHandlers() {
    // Find all interactive elements
    const interactiveElements = document.querySelectorAll(
        'button, input, select, textarea, [role="button"], [role="checkbox"], [role="radio"]'
    );
    
    // Add event listeners to each element
    interactiveElements.forEach(element => {
        // Mouse events
        element.addEventListener('mouseenter', () => {
            visualFeedbackManager.showHoverFeedback(element);
        });
        
        element.addEventListener('mouseleave', () => {
            visualFeedbackManager.removeHoverFeedback(element);
        });
        
        element.addEventListener('mousedown', () => {
            visualFeedbackManager.showActiveFeedback(element);
        });
        
        element.addEventListener('mouseup', () => {
            visualFeedbackManager.removeActiveFeedback(element);
        });
        
        // Focus events
        element.addEventListener('focus', () => {
            visualFeedbackManager.showFocusFeedback(element);
        });
        
        element.addEventListener('blur', () => {
            visualFeedbackManager.removeFocusFeedback(element);
        });
        
        // Drag and drop events
        element.addEventListener('dragover', (event) => {
            event.preventDefault();
            visualFeedbackManager.showDragOverFeedback(element);
        });
        
        element.addEventListener('dragleave', () => {
            visualFeedbackManager.removeDragOverFeedback(element);
        });
        
        element.addEventListener('drop', (event) => {
            event.preventDefault();
            
            // Check if drop is valid
            if (isValidDrop(event, element)) {
                visualFeedbackManager.showDropValidFeedback(element);
            } else {
                visualFeedbackManager.showDropInvalidFeedback(element);
            }
        });
    });
}

/**
 * Check if a drop is valid
 * @param {DragEvent} event - Drag event
 * @param {HTMLElement} element - Drop target element
 * @returns {boolean} Whether the drop is valid
 */
function isValidDrop(event, element) {
    // Check if the element accepts the dragged data
    // This would depend on the specific implementation
    return true;
}

// ================================
// VISUAL FEEDBACK FOR SPECIFIC ACTIONS
// ================================

/**
 * Show visual feedback for button click
 * @param {HTMLElement} button - Button element
 * @param {Function} callback - Callback function
 */
function showButtonClickFeedback(button, callback) {
    // Show active feedback
    visualFeedbackManager.showActiveFeedback(button);
    
    // Execute callback
    const result = callback();
    
    // Handle promise if callback returns one
    if (result && typeof result.then === 'function') {
        // Show loading feedback
        visualFeedbackManager.showLoadingFeedback(button);
        
        // Handle promise completion
        result
            .then(data => {
                // Remove loading feedback
                visualFeedbackManager.removeLoadingFeedback(button);
                
                // Show success feedback
                visualFeedbackManager.showSuccessFeedback(button, 'Success');
            })
            .catch(error => {
                // Remove loading feedback
                visualFeedbackManager.removeLoadingFeedback(button);
                
                // Show error feedback
                visualFeedbackManager.showErrorFeedback(button, error.message);
            });
    } else {
        // Remove active feedback after delay
        setTimeout(() => {
            visualFeedbackManager.removeActiveFeedback(button);
        }, visualFeedbackManager.animationDuration);
    }
}

/**
 * Show visual feedback for form submission
 * @param {HTMLFormElement} form - Form element
 * @param {Function} callback - Callback function
 */
function showFormSubmissionFeedback(form, callback) {
    // Find submit button
    const submitButton = form.querySelector('button[type="submit"], input[type="submit"]');
    
    if (submitButton) {
        // Show loading feedback
        visualFeedbackManager.showLoadingFeedback(submitButton);
    }
    
    // Execute callback
    const result = callback();
    
    // Handle promise if callback returns one
    if (result && typeof result.then === 'function') {
        result
            .then(data => {
                // Remove loading feedback
                if (submitButton) {
                    visualFeedbackManager.removeLoadingFeedback(submitButton);
                    
                    // Show success feedback
                    visualFeedbackManager.showSuccessFeedback(submitButton, 'Form submitted successfully');
                }
            })
            .catch(error => {
                // Remove loading feedback
                if (submitButton) {
                    visualFeedbackManager.removeLoadingFeedback(submitButton);
                    
                    // Show error feedback
                    visualFeedbackManager.showErrorFeedback(submitButton, error.message);
                }
            });
    }
}

/**
 * Show visual feedback for file upload
 * @param {HTMLInputElement} input - File input element
 * @param {Function} callback - Callback function
 */
function showFileUploadFeedback(input, callback) {
    // Show loading feedback
    visualFeedbackManager.showLoadingFeedback(input);
    
    // Execute callback
    const result = callback();
    
    // Handle promise if callback returns one
    if (result && typeof result.then === 'function') {
        result
            .then(data => {
                // Remove loading feedback
                visualFeedbackManager.removeLoadingFeedback(input);
                
                // Show success feedback
                visualFeedbackManager.showSuccessFeedback(input, 'File uploaded successfully');
            })
            .catch(error => {
                // Remove loading feedback
                visualFeedbackManager.removeLoadingFeedback(input);
                
                // Show error feedback
                visualFeedbackManager.showErrorFeedback(input, error.message);
            });
    }
}

// ================================
// PYTHON IMPLEMENTATION NOTES
// ================================

/*
Below are notes on how to implement these visual feedback features in Python/PySide6:

1. Visual Feedback Manager:
```python
from PySide6.QtCore import QObject, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtWidgets import QWidget, QGraphicsOpacityEffect

class VisualFeedbackManager(QObject):
    def __init__(self):
        super().__init__()
        self.feedback_enabled = True
        self.feedback_duration = 300  # ms
        self.animation_duration = 200  # ms
        self.performance_mode = self.detect_performance_mode()
        self.configure_feedback_settings()
    
    def detect_performance_mode(self):
        # Check for reduced motion preference
        # In PySide6, this would need to be checked through system settings
        
        # Check device capabilities
        has_hardware_acceleration = self.check_hardware_acceleration()
        memory = self.get_device_memory()
        cores = self.get_cpu_cores()
        
        if has_hardware_acceleration and memory > 4 and cores > 4:
            return 'high'
        elif memory > 2 and cores > 2:
            return 'medium'
        else:
            return 'low'
    
    def configure_feedback_settings(self):
        if self.performance_mode == 'high':
            self.feedback_duration = 300
            self.animation_duration = 300
            self.enable_transforms = True
            self.enable_shadows = True
            self.enable_transitions = True
        elif self.performance_mode == 'medium':
            self.feedback_duration = 200
            self.animation_duration = 200
            self.enable_transforms = True
            self.enable_shadows = False
            self.enable_transitions = True
        else:  # low
            self.feedback_duration = 100
            self.animation_duration = 100
            self.enable_transforms = False
            self.enable_shadows = False
            self.enable_transitions = False
    
    def show_hover_feedback(self, widget):
        if not self.feedback_enabled:
            return
        
        # Apply hover stylesheet
        widget.setStyleSheet(widget.styleSheet() + " QWidget:hover { background-color: #e1e1e1; }")
        
        # Apply transform if enabled
        if self.enable_transforms:
            # This would require custom widget implementation
            pass
    
    def show_success_feedback(self, widget, message):
        if not self.feedback_enabled:
            return
        
        # Apply success stylesheet
        original_style = widget.styleSheet()
        widget.setStyleSheet(original_style + " QWidget { background-color: #d4edda; }")
        
        # Show success message
        self.show_temporary_message(widget, message, 'success')
        
        # Reset after duration
        QTimer.singleShot(self.feedback_duration, lambda: widget.setStyleSheet(original_style))
    
    def show_error_feedback(self, widget, message):
        if not self.feedback_enabled:
            return
        
        # Apply error stylesheet
        original_style = widget.styleSheet()
        widget.setStyleSheet(original_style + " QWidget { background-color: #f8d7da; }")
        
        # Show error message
        self.show_temporary_message(widget, message, 'error')
        
        # Add shake animation if enabled
        if self.enable_transforms:
            self.shake_widget(widget)
        
        # Reset after duration
        QTimer.singleShot(self.feedback_duration, lambda: widget.setStyleSheet(original_style))
    
    def shake_widget(self, widget):
        # Create shake animation
        animation = QPropertyAnimation(widget, b"pos")
        animation.setDuration(500)
        animation.setLoopCount(1)
        
        # Set key values for shake effect
        original_pos = widget.pos()
        animation.setKeyValueAt(0, original_pos)
        animation.setKeyValueAt(0.1, original_pos + QPoint(-5, 0))
        animation.setKeyValueAt(0.2, original_pos + QPoint(5, 0))
        animation.setKeyValueAt(0.3, original_pos + QPoint(-5, 0))
        animation.setKeyValueAt(0.4, original_pos + QPoint(5, 0))
        animation.setKeyValueAt(0.5, original_pos + QPoint(-3, 0))
        animation.setKeyValueAt(0.6, original_pos + QPoint(3, 0))
        animation.setKeyValueAt(0.7, original_pos + QPoint(-2, 0))
        animation.setKeyValueAt(0.8, original_pos + QPoint(2, 0))
        animation.setKeyValueAt(0.9, original_pos + QPoint(-1, 0))
        animation.setKeyValueAt(1, original_pos)
        
        animation.setEasingCurve(QEasingCurve.InOutQuad)
        animation.start()
```

2. Event Handlers:
```python
from PySide6.QtCore import Signal, QObject

class VisualFeedbackEventHandlers(QObject):
    def __init__(self, feedback_manager):
        super().__init__()
        self.feedback_manager = feedback_manager
    
    def setup_button_feedback(self, button):
        # Connect signals
        button.pressed.connect(lambda: self.feedback_manager.show_active_feedback(button))
        button.released.connect(lambda: self.feedback_manager.remove_active_feedback(button))
        
        # For hover effects, you'd need to implement enterEvent and leaveEvent
        # in a custom button widget or use event filters
    
    def setup_input_feedback(self, input_widget):
        # Connect signals
        input_widget.focusInEvent = lambda e: self.feedback_manager.show_focus_feedback(input_widget)
        input_widget.focusOutEvent = lambda e: self.feedback_manager.remove_focus_feedback(input_widget)
```

3. Custom Button with Visual Feedback:
```python
from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import QEvent

class VisualFeedbackButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.feedback_manager = visualFeedbackManager
    
    def enterEvent(self, event):
        super().enterEvent(event)
        self.feedback_manager.show_hover_feedback(self)
    
    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.feedback_manager.remove_hover_feedback(self)
    
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.feedback_manager.show_active_feedback(self)
    
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.feedback_manager.remove_active_feedback(self)
```

4. Visual Feedback for Specific Actions:
```python
def show_button_click_feedback(button, callback):
    # Show active feedback
    visualFeedbackManager.show_active_feedback(button)
    
    # Execute callback
    result = callback()
    
    # Handle async operations
    if hasattr(result, 'then'):  # Promise-like object
        # Show loading feedback
        visualFeedbackManager.show_loading_feedback(button)
        
        # Handle completion
        result.then(
            lambda data: (
                visualFeedbackManager.remove_loading_feedback(button),
                visualFeedbackManager.show_success_feedback(button, "Success")
            ),
            lambda error: (
                visualFeedbackManager.remove_loading_feedback(button),
                visualFeedbackManager.show_error_feedback(button, str(error))
            )
        )
    else:
        # Remove active feedback after delay
        QTimer.singleShot(visualFeedbackManager.animation_duration, 
                         lambda: visualFeedbackManager.remove_active_feedback(button))
```
*/