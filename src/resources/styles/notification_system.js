/**
 * Notification System for 3D-MM Application
 * 
 * This JavaScript file demonstrates how to implement error handling and user notifications,
 * which can be translated to the Python/PySide6 application.
 */

// ================================
// NOTIFICATION MANAGER
// ================================

/**
 * Notification manager for handling all user notifications
 */
class NotificationManager {
    constructor() {
        this.notifications = [];
        this.maxNotifications = 5;
        this.defaultDuration = 5000; // ms
        this.container = this.createNotificationContainer();
        this.setupGlobalErrorHandler();
    }
    
    /**
     * Create notification container
     * @returns {HTMLElement} Notification container element
     */
    createNotificationContainer() {
        // Create container if it doesn't exist
        let container = document.querySelector('.notification-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'notification-container';
            document.body.appendChild(container);
        }
        return container;
    }
    
    /**
     * Set up global error handler
     */
    setupGlobalErrorHandler() {
        // Handle uncaught errors
        window.addEventListener('error', (event) => {
            this.showError('An unexpected error occurred', event.error?.message || event.message);
            console.error('Global error:', event.error);
        });
        
        // Handle unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            this.showError('An unexpected error occurred', event.reason?.message || 'Promise rejection');
            console.error('Unhandled promise rejection:', event.reason);
        });
    }
    
    /**
     * Show an info notification
     * @param {string} title - Notification title
     * @param {string} message - Notification message
     * @param {Object} options - Notification options
     * @returns {HTMLElement} Notification element
     */
    showInfo(title, message, options = {}) {
        return this.showNotification('info', title, message, options);
    }
    
    /**
     * Show a success notification
     * @param {string} title - Notification title
     * @param {string} message - Notification message
     * @param {Object} options - Notification options
     * @returns {HTMLElement} Notification element
     */
    showSuccess(title, message, options = {}) {
        return this.showNotification('success', title, message, options);
    }
    
    /**
     * Show a warning notification
     * @param {string} title - Notification title
     * @param {string} message - Notification message
     * @param {Object} options - Notification options
     * @returns {HTMLElement} Notification element
     */
    showWarning(title, message, options = {}) {
        return this.showNotification('warning', title, message, options);
    }
    
    /**
     * Show an error notification
     * @param {string} title - Notification title
     * @param {string} message - Notification message
     * @param {Object} options - Notification options
     * @returns {HTMLElement} Notification element
     */
    showError(title, message, options = {}) {
        return this.showNotification('error', title, message, options);
    }
    
    /**
     * Show a notification
     * @param {string} type - Notification type
     * @param {string} title - Notification title
     * @param {string} message - Notification message
     * @param {Object} options - Notification options
     * @returns {HTMLElement} Notification element
     */
    showNotification(type, title, message, options = {}) {
        // Create notification element
        const notification = this.createNotificationElement(type, title, message, options);
        
        // Add to container
        this.container.appendChild(notification);
        
        // Add to notifications list
        this.notifications.push(notification);
        
        // Limit number of notifications
        this.limitNotifications();
        
        // Show notification with animation
        this.showNotificationWithAnimation(notification);
        
        // Set auto-hide if specified
        const duration = options.duration || this.defaultDuration;
        if (duration > 0) {
            setTimeout(() => {
                this.hideNotification(notification);
            }, duration);
        }
        
        return notification;
    }
    
    /**
     * Create notification element
     * @param {string} type - Notification type
     * @param {string} title - Notification title
     * @param {string} message - Notification message
     * @param {Object} options - Notification options
     * @returns {HTMLElement} Notification element
     */
    createNotificationElement(type, title, message, options) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `toast-notification ${type}`;
        
        // Create header
        const header = document.createElement('div');
        header.className = 'toast-notification-header';
        
        // Add icon
        const icon = document.createElement('div');
        icon.className = 'toast-notification-icon';
        icon.innerHTML = this.getIconForType(type);
        header.appendChild(icon);
        
        // Add title
        const titleElement = document.createElement('div');
        titleElement.textContent = title;
        header.appendChild(titleElement);
        
        // Add close button if not persistent
        if (!options.persistent) {
            const closeButton = document.createElement('button');
            closeButton.className = 'toast-notification-close';
            closeButton.innerHTML = '&times;';
            closeButton.setAttribute('aria-label', 'Close notification');
            closeButton.addEventListener('click', () => {
                this.hideNotification(notification);
            });
            header.appendChild(closeButton);
        }
        
        notification.appendChild(header);
        
        // Add message
        const messageElement = document.createElement('div');
        messageElement.className = 'toast-notification-message';
        messageElement.textContent = message;
        notification.appendChild(messageElement);
        
        // Add actions if specified
        if (options.actions && options.actions.length > 0) {
            const actionsElement = document.createElement('div');
            actionsElement.className = 'toast-notification-actions';
            
            options.actions.forEach(action => {
                const actionButton = document.createElement('button');
                actionButton.className = `toast-notification-action ${action.primary ? 'primary' : ''}`;
                actionButton.textContent = action.text;
                actionButton.addEventListener('click', () => {
                    if (action.callback) {
                        action.callback();
                    }
                    if (!action.persistent) {
                        this.hideNotification(notification);
                    }
                });
                actionsElement.appendChild(actionButton);
            });
            
            notification.appendChild(actionsElement);
        }
        
        return notification;
    }
    
    /**
     * Get icon for notification type
     * @param {string} type - Notification type
     * @returns {string} Icon HTML
     */
    getIconForType(type) {
        switch (type) {
            case 'info':
                return 'ℹ';
            case 'success':
                return '✓';
            case 'warning':
                return '⚠';
            case 'error':
                return '✕';
            default:
                return '';
        }
    }
    
    /**
     * Show notification with animation
     * @param {HTMLElement} notification - Notification element
     */
    showNotificationWithAnimation(notification) {
        // Add show class
        notification.classList.add('show');
        
        // Announce to screen readers
        this.announceToScreenReader(notification);
    }
    
    /**
     * Hide notification
     * @param {HTMLElement} notification - Notification element
     */
    hideNotification(notification) {
        // Add hide class
        notification.classList.add('hide');
        
        // Remove after animation completes
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
            
            // Remove from notifications list
            const index = this.notifications.indexOf(notification);
            if (index > -1) {
                this.notifications.splice(index, 1);
            }
        }, 300);
    }
    
    /**
     * Hide all notifications
     */
    hideAllNotifications() {
        // Create a copy to avoid modifying the array while iterating
        const notifications = [...this.notifications];
        
        // Hide each notification
        notifications.forEach(notification => {
            this.hideNotification(notification);
        });
    }
    
    /**
     * Limit number of notifications
     */
    limitNotifications() {
        // Remove oldest notifications if too many
        while (this.notifications.length > this.maxNotifications) {
            const oldestNotification = this.notifications.shift();
            this.hideNotification(oldestNotification);
        }
    }
    
    /**
     * Announce notification to screen readers
     * @param {HTMLElement} notification - Notification element
     */
    announceToScreenReader(notification) {
        // Create live region if it doesn't exist
        let liveRegion = document.getElementById('notification-live-region');
        if (!liveRegion) {
            liveRegion = document.createElement('div');
            liveRegion.id = 'notification-live-region';
            liveRegion.setAttribute('aria-live', 'polite');
            liveRegion.setAttribute('aria-atomic', 'true');
            liveRegion.className = 'sr-only';
            document.body.appendChild(liveRegion);
        }
        
        // Get notification text
        const title = notification.querySelector('.toast-notification-header div:last-child').textContent;
        const message = notification.querySelector('.toast-notification-message').textContent;
        
        // Announce to screen reader
        liveRegion.textContent = `${title}: ${message}`;
        
        // Clear after announcement
        setTimeout(() => {
            liveRegion.textContent = '';
        }, 100);
    }
}

// Create global notification manager
const notificationManager = new NotificationManager();

// ================================
// DIALOG MANAGER
// ================================

/**
 * Dialog manager for showing modal dialogs
 */
class DialogManager {
    constructor() {
        this.activeDialog = null;
        this.dialogContainer = this.createDialogContainer();
    }
    
    /**
     * Create dialog container
     * @returns {HTMLElement} Dialog container element
     */
    createDialogContainer() {
        // Create container if it doesn't exist
        let container = document.querySelector('.dialog-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'dialog-container';
            document.body.appendChild(container);
        }
        return container;
    }
    
    /**
     * Show an error dialog
     * @param {string} title - Dialog title
     * @param {string} message - Dialog message
     * @param {string} details - Error details
     * @param {Object} options - Dialog options
     * @returns {Promise} Promise that resolves when dialog is closed
     */
    showErrorDialog(title, message, details = null, options = {}) {
        return this.showDialog('error', title, message, details, options);
    }
    
    /**
     * Show a warning dialog
     * @param {string} title - Dialog title
     * @param {string} message - Dialog message
     * @param {Object} options - Dialog options
     * @returns {Promise} Promise that resolves when dialog is closed
     */
    showWarningDialog(title, message, options = {}) {
        return this.showDialog('warning', title, message, null, options);
    }
    
    /**
     * Show a success dialog
     * @param {string} title - Dialog title
     * @param {string} message - Dialog message
     * @param {Object} options - Dialog options
     * @returns {Promise} Promise that resolves when dialog is closed
     */
    showSuccessDialog(title, message, options = {}) {
        return this.showDialog('success', title, message, null, options);
    }
    
    /**
     * Show an info dialog
     * @param {string} title - Dialog title
     * @param {string} message - Dialog message
     * @param {Object} options - Dialog options
     * @returns {Promise} Promise that resolves when dialog is closed
     */
    showInfoDialog(title, message, options = {}) {
        return this.showDialog('info', title, message, null, options);
    }
    
    /**
     * Show a dialog
     * @param {string} type - Dialog type
     * @param {string} title - Dialog title
     * @param {string} message - Dialog message
     * @param {string} details - Dialog details
     * @param {Object} options - Dialog options
     * @returns {Promise} Promise that resolves when dialog is closed
     */
    showDialog(type, title, message, details = null, options = {}) {
        return new Promise((resolve) => {
            // Create dialog element
            const dialog = this.createDialogElement(type, title, message, details, options);
            
            // Add to container
            this.dialogContainer.appendChild(dialog);
            
            // Set as active dialog
            this.activeDialog = dialog;
            
            // Show dialog with animation
            this.showDialogWithAnimation(dialog);
            
            // Set up close handler
            const closeDialog = (result) => {
                this.hideDialog(dialog);
                resolve(result);
            };
            
            // Set up button handlers
            const buttons = dialog.querySelectorAll('.dialog-action');
            buttons.forEach(button => {
                button.addEventListener('click', () => {
                    const result = button.getAttribute('data-result') || 'close';
                    closeDialog(result);
                });
            });
            
            // Set up close button handler
            const closeButton = dialog.querySelector('.dialog-close');
            if (closeButton) {
                closeButton.addEventListener('click', () => {
                    closeDialog('close');
                });
            }
            
            // Set up escape key handler
            const escapeKeyHandler = (event) => {
                if (event.key === 'Escape') {
                    closeDialog('cancel');
                    document.removeEventListener('keydown', escapeKeyHandler);
                }
            };
            document.addEventListener('keydown', escapeKeyHandler);
            
            // Set up overlay click handler
            const overlay = dialog.querySelector('.dialog-overlay');
            if (overlay && !options.modal) {
                overlay.addEventListener('click', () => {
                    closeDialog('cancel');
                });
            }
            
            // Focus management
            this.trapFocus(dialog);
            
            // Announce to screen readers
            this.announceToScreenReader(dialog);
        });
    }
    
    /**
     * Create dialog element
     * @param {string} type - Dialog type
     * @param {string} title - Dialog title
     * @param {string} message - Dialog message
     * @param {string} details - Dialog details
     * @param {Object} options - Dialog options
     * @returns {HTMLElement} Dialog element
     */
    createDialogElement(type, title, message, details, options) {
        // Create dialog overlay
        const overlay = document.createElement('div');
        overlay.className = 'dialog-overlay';
        
        // Create dialog
        const dialog = document.createElement('div');
        dialog.className = `${type}-dialog`;
        dialog.setAttribute('role', 'dialog');
        dialog.setAttribute('aria-modal', 'true');
        dialog.setAttribute('aria-labelledby', 'dialog-title');
        dialog.setAttribute('aria-describedby', 'dialog-message');
        
        // Create header
        const header = document.createElement('div');
        header.className = `${type}-dialog-header`;
        
        // Add icon
        const icon = document.createElement('div');
        icon.className = `${type}-dialog-icon`;
        icon.innerHTML = this.getIconForType(type);
        header.appendChild(icon);
        
        // Add title
        const titleElement = document.createElement('div');
        titleElement.id = 'dialog-title';
        titleElement.textContent = title;
        header.appendChild(titleElement);
        
        // Add close button
        const closeButton = document.createElement('button');
        closeButton.className = 'dialog-close';
        closeButton.innerHTML = '&times;';
        closeButton.setAttribute('aria-label', 'Close dialog');
        header.appendChild(closeButton);
        
        dialog.appendChild(header);
        
        // Create message
        const messageElement = document.createElement('div');
        messageElement.id = 'dialog-message';
        messageElement.className = `${type}-dialog-message`;
        messageElement.textContent = message;
        dialog.appendChild(messageElement);
        
        // Add details if provided
        if (details) {
            const detailsElement = document.createElement('div');
            detailsElement.className = `${type}-dialog-details`;
            detailsElement.textContent = details;
            dialog.appendChild(detailsElement);
            
            // Add toggle button for details
            const toggleButton = document.createElement('button');
            toggleButton.textContent = 'Show Details';
            toggleButton.className = 'dialog-toggle-details';
            toggleButton.addEventListener('click', () => {
                if (detailsElement.style.display === 'none') {
                    detailsElement.style.display = 'block';
                    toggleButton.textContent = 'Hide Details';
                } else {
                    detailsElement.style.display = 'none';
                    toggleButton.textContent = 'Show Details';
                }
            });
            dialog.insertBefore(toggleButton, detailsElement);
        }
        
        // Create actions
        const actionsElement = document.createElement('div');
        actionsElement.className = `${type}-dialog-actions`;
        
        // Add buttons based on options
        const buttons = options.buttons || ['OK'];
        buttons.forEach((buttonText, index) => {
            const button = document.createElement('button');
            button.className = 'dialog-action';
            button.textContent = buttonText;
            
            // Set result based on button text
            if (buttonText.toUpperCase() === 'OK') {
                button.setAttribute('data-result', 'ok');
            } else if (buttonText.toUpperCase() === 'CANCEL') {
                button.setAttribute('data-result', 'cancel');
            } else if (buttonText.toUpperCase() === 'YES') {
                button.setAttribute('data-result', 'yes');
                button.className += ' primary';
            } else if (buttonText.toUpperCase() === 'NO') {
                button.setAttribute('data-result', 'no');
            } else {
                button.setAttribute('data-result', buttonText.toLowerCase());
            }
            
            // Set first button as default
            if (index === 0) {
                button.className += ' primary';
            }
            
            actionsElement.appendChild(button);
        });
        
        dialog.appendChild(actionsElement);
        
        // Add overlay to dialog
        overlay.appendChild(dialog);
        
        return overlay;
    }
    
    /**
     * Get icon for dialog type
     * @param {string} type - Dialog type
     * @returns {string} Icon HTML
     */
    getIconForType(type) {
        switch (type) {
            case 'info':
                return 'ℹ';
            case 'success':
                return '✓';
            case 'warning':
                return '⚠';
            case 'error':
                return '✕';
            default:
                return '';
        }
    }
    
    /**
     * Show dialog with animation
     * @param {HTMLElement} dialog - Dialog element
     */
    showDialogWithAnimation(dialog) {
        // Add show class
        dialog.classList.add('show');
        
        // Prevent body scroll
        document.body.style.overflow = 'hidden';
    }
    
    /**
     * Hide dialog
     * @param {HTMLElement} dialog - Dialog element
     */
    hideDialog(dialog) {
        // Add hide class
        dialog.classList.add('hide');
        
        // Remove after animation completes
        setTimeout(() => {
            if (dialog.parentNode) {
                dialog.parentNode.removeChild(dialog);
            }
            
            // Reset active dialog
            if (this.activeDialog === dialog) {
                this.activeDialog = null;
            }
            
            // Restore body scroll
            document.body.style.overflow = '';
        }, 300);
    }
    
    /**
     * Trap focus within dialog
     * @param {HTMLElement} dialog - Dialog element
     */
    trapFocus(dialog) {
        // Get focusable elements
        const focusableElements = dialog.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        
        if (focusableElements.length > 0) {
            // Focus first element
            focusableElements[0].focus();
            
            // Handle tab key
            dialog.addEventListener('keydown', (event) => {
                if (event.key === 'Tab') {
                    const firstElement = focusableElements[0];
                    const lastElement = focusableElements[focusableElements.length - 1];
                    
                    if (event.shiftKey) {
                        if (document.activeElement === firstElement) {
                            event.preventDefault();
                            lastElement.focus();
                        }
                    } else {
                        if (document.activeElement === lastElement) {
                            event.preventDefault();
                            firstElement.focus();
                        }
                    }
                }
            });
        }
    }
    
    /**
     * Announce dialog to screen readers
     * @param {HTMLElement} dialog - Dialog element
     */
    announceToScreenReader(dialog) {
        // Create live region if it doesn't exist
        let liveRegion = document.getElementById('dialog-live-region');
        if (!liveRegion) {
            liveRegion = document.createElement('div');
            liveRegion.id = 'dialog-live-region';
            liveRegion.setAttribute('aria-live', 'assertive');
            liveRegion.setAttribute('aria-atomic', 'true');
            liveRegion.className = 'sr-only';
            document.body.appendChild(liveRegion);
        }
        
        // Get dialog text
        const title = document.getElementById('dialog-title').textContent;
        const message = document.getElementById('dialog-message').textContent;
        
        // Announce to screen reader
        liveRegion.textContent = `Dialog opened: ${title}: ${message}`;
        
        // Clear after announcement
        setTimeout(() => {
            liveRegion.textContent = '';
        }, 100);
    }
}

// Create global dialog manager
const dialogManager = new DialogManager();

// ================================
// PROGRESS MANAGER
// ================================

/**
 * Progress manager for showing progress notifications
 */
class ProgressManager {
    constructor() {
        this.activeProgress = null;
        this.progressContainer = this.createProgressContainer();
    }
    
    /**
     * Create progress container
     * @returns {HTMLElement} Progress container element
     */
    createProgressContainer() {
        // Create container if it doesn't exist
        let container = document.querySelector('.progress-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'progress-container';
            document.body.appendChild(container);
        }
        return container;
    }
    
    /**
     * Show progress notification
     * @param {string} title - Progress title
     * @param {string} status - Progress status
     * @param {Function} onCancel - Cancel callback
     * @returns {Object} Progress controller object
     */
    showProgress(title, status, onCancel = null) {
        // Hide any existing progress
        if (this.activeProgress) {
            this.hideProgress();
        }
        
        // Create progress element
        const progress = this.createProgressElement(title, status, onCancel);
        
        // Add to container
        this.progressContainer.appendChild(progress);
        
        // Set as active progress
        this.activeProgress = progress;
        
        // Return progress controller
        return {
            updateProgress: (value, max, newStatus) => {
                this.updateProgress(progress, value, max, newStatus);
            },
            complete: (message) => {
                this.completeProgress(progress, message);
            },
            error: (message) => {
                this.errorProgress(progress, message);
            },
            hide: () => {
                this.hideProgress();
            }
        };
    }
    
    /**
     * Create progress element
     * @param {string} title - Progress title
     * @param {string} status - Progress status
     * @param {Function} onCancel - Cancel callback
     * @returns {HTMLElement} Progress element
     */
    createProgressElement(title, status, onCancel) {
        // Create progress element
        const progress = document.createElement('div');
        progress.className = 'progress-notification';
        
        // Create header
        const header = document.createElement('div');
        header.className = 'progress-notification-header';
        
        // Add title
        const titleElement = document.createElement('div');
        titleElement.className = 'progress-notification-title';
        titleElement.textContent = title;
        header.appendChild(titleElement);
        
        // Add percentage
        const percentageElement = document.createElement('div');
        percentageElement.className = 'progress-notification-percentage';
        percentageElement.textContent = '0%';
        header.appendChild(percentageElement);
        
        progress.appendChild(header);
        
        // Create progress bar
        const progressBar = document.createElement('div');
        progressBar.className = 'progress-notification-progress';
        
        const progressBarFill = document.createElement('div');
        progressBarFill.className = 'progress-notification-progress-bar';
        progressBar.appendChild(progressBarFill);
        
        progress.appendChild(progressBar);
        
        // Create status
        const statusElement = document.createElement('div');
        statusElement.className = 'progress-notification-status';
        
        const statusText = document.createElement('div');
        statusText.textContent = status;
        statusElement.appendChild(statusText);
        
        // Add cancel button if provided
        if (onCancel) {
            const cancelButton = document.createElement('button');
            cancelButton.className = 'progress-notification-cancel';
            cancelButton.textContent = 'Cancel';
            cancelButton.addEventListener('click', () => {
                onCancel();
            });
            statusElement.appendChild(cancelButton);
        }
        
        progress.appendChild(statusElement);
        
        return progress;
    }
    
    /**
     * Update progress
     * @param {HTMLElement} progress - Progress element
     * @param {number} value - Current value
     * @param {number} max - Maximum value
     * @param {string} status - New status
     */
    updateProgress(progress, value, max, status) {
        // Calculate percentage
        const percentage = max > 0 ? Math.round((value / max) * 100) : 0;
        
        // Update percentage
        const percentageElement = progress.querySelector('.progress-notification-percentage');
        percentageElement.textContent = `${percentage}%`;
        
        // Update progress bar
        const progressBarFill = progress.querySelector('.progress-notification-progress-bar');
        progressBarFill.style.width = `${percentage}%`;
        
        // Update status if provided
        if (status) {
            const statusText = progress.querySelector('.progress-notification-status div');
            statusText.textContent = status;
        }
    }
    
    /**
     * Complete progress
     * @param {HTMLElement} progress - Progress element
     * @param {string} message - Completion message
     */
    completeProgress(progress, message) {
        // Update to 100%
        this.updateProgress(progress, 100, 100, message || 'Complete');
        
        // Add success class
        progress.classList.add('success');
        
        // Hide after delay
        setTimeout(() => {
            this.hideProgress();
        }, 2000);
    }
    
    /**
     * Show error in progress
     * @param {HTMLElement} progress - Progress element
     * @param {string} message - Error message
     */
    errorProgress(progress, message) {
        // Update status
        const statusText = progress.querySelector('.progress-notification-status div');
        statusText.textContent = message || 'Error';
        
        // Add error class
        progress.classList.add('error');
        
        // Hide after delay
        setTimeout(() => {
            this.hideProgress();
        }, 3000);
    }
    
    /**
     * Hide progress
     */
    hideProgress() {
        if (this.activeProgress) {
            // Add hide class
            this.activeProgress.classList.add('hide');
            
            // Remove after animation completes
            setTimeout(() => {
                if (this.activeProgress.parentNode) {
                    this.activeProgress.parentNode.removeChild(this.activeProgress);
                }
                this.activeProgress = null;
            }, 300);
        }
    }
}

// Create global progress manager
const progressManager = new ProgressManager();

// ================================
// LOADING MANAGER
// ================================

/**
 * Loading manager for showing loading overlays
 */
class LoadingManager {
    constructor() {
        this.activeLoading = null;
        this.loadingContainer = this.createLoadingContainer();
    }
    
    /**
     * Create loading container
     * @returns {HTMLElement} Loading container element
     */
    createLoadingContainer() {
        // Create container if it doesn't exist
        let container = document.querySelector('.loading-overlay');
        if (!container) {
            container = document.createElement('div');
            container.className = 'loading-overlay';
            container.style.display = 'none';
            document.body.appendChild(container);
        }
        return container;
    }
    
    /**
     * Show loading overlay
     * @param {string} message - Loading message
     * @param {Function} onCancel - Cancel callback
     * @returns {Object} Loading controller object
     */
    showLoading(message = 'Loading...', onCancel = null) {
        // Hide any existing loading
        if (this.activeLoading) {
            this.hideLoading();
        }
        
        // Clear container
        this.loadingContainer.innerHTML = '';
        
        // Create spinner
        const spinner = document.createElement('div');
        spinner.className = 'loading-spinner';
        this.loadingContainer.appendChild(spinner);
        
        // Create message
        const messageElement = document.createElement('div');
        messageElement.className = 'loading-message';
        messageElement.textContent = message;
        this.loadingContainer.appendChild(messageElement);
        
        // Create progress
        const progress = document.createElement('div');
        progress.className = 'loading-progress';
        
        const progressBar = document.createElement('div');
        progressBar.className = 'loading-progress-bar';
        progress.appendChild(progressBar);
        this.loadingContainer.appendChild(progress);
        
        // Create cancel button if provided
        if (onCancel) {
            const cancelButton = document.createElement('button');
            cancelButton.className = 'loading-cancel';
            cancelButton.textContent = 'Cancel';
            cancelButton.addEventListener('click', () => {
                onCancel();
            });
            this.loadingContainer.appendChild(cancelButton);
        }
        
        // Show loading
        this.loadingContainer.style.display = 'flex';
        this.activeLoading = {
            container: this.loadingContainer,
            progressBar
        };
        
        // Prevent body scroll
        document.body.style.overflow = 'hidden';
        
        // Return loading controller
        return {
            updateProgress: (value, max) => {
                this.updateLoadingProgress(value, max);
            },
            setMessage: (newMessage) => {
                this.updateLoadingMessage(newMessage);
            },
            hide: () => {
                this.hideLoading();
            }
        };
    }
    
    /**
     * Update loading progress
     * @param {number} value - Current value
     * @param {number} max - Maximum value
     */
    updateLoadingProgress(value, max) {
        if (this.activeLoading) {
            // Calculate percentage
            const percentage = max > 0 ? Math.round((value / max) * 100) : 0;
            
            // Update progress bar
            this.activeLoading.progressBar.style.width = `${percentage}%`;
        }
    }
    
    /**
     * Update loading message
     * @param {string} message - New message
     */
    updateLoadingMessage(message) {
        if (this.activeLoading) {
            const messageElement = this.loadingContainer.querySelector('.loading-message');
            messageElement.textContent = message;
        }
    }
    
    /**
     * Hide loading overlay
     */
    hideLoading() {
        if (this.activeLoading) {
            // Hide loading
            this.loadingContainer.style.display = 'none';
            
            // Restore body scroll
            document.body.style.overflow = '';
            
            this.activeLoading = null;
        }
    }
}

// Create global loading manager
const loadingManager = new LoadingManager();

// ================================
// PYTHON IMPLEMENTATION NOTES
// ================================

/*
Below are notes on how to implement these notification features in Python/PySide6:

1. Notification Manager:
```python
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import QTimer, QPropertyAnimation, QEasingCurve, Signal, QObject

class NotificationManager(QObject):
    notification_shown = Signal(str, str, str)  # type, title, message
    
    def __init__(self):
        super().__init__()
        self.notifications = []
        self.max_notifications = 5
        self.default_duration = 5000  # ms
        self.container = self.create_notification_container()
    
    def create_notification_container(self):
        # Create container widget
        container = QWidget()
        container.setObjectName("notification_container")
        container.setFixedWidth(400)
        
        # Set layout
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addStretch()
        
        # Add to main window
        main_window = QApplication.instance().mainWindow
        main_window.add_notification_widget(container)
        
        return container
    
    def show_info(self, title, message, options=None):
        return self.show_notification("info", title, message, options)
    
    def show_success(self, title, message, options=None):
        return self.show_notification("success", title, message, options)
    
    def show_warning(self, title, message, options=None):
        return self.show_notification("warning", title, message, options)
    
    def show_error(self, title, message, options=None):
        return self.show_notification("error", title, message, options)
    
    def show_notification(self, notification_type, title, message, options=None):
        # Create notification widget
        notification = NotificationWidget(notification_type, title, message, options)
        
        # Add to container
        self.container.layout().insertWidget(0, notification)
        
        # Add to notifications list
        self.notifications.append(notification)
        
        # Limit number of notifications
        self.limit_notifications()
        
        # Show notification with animation
        self.show_notification_with_animation(notification)
        
        # Set auto-hide if specified
        duration = options.get("duration", self.default_duration) if options else self.default_duration
        if duration > 0:
            QTimer.singleShot(duration, lambda: self.hide_notification(notification))
        
        # Emit signal
        self.notification_shown.emit(notification_type, title, message)
        
        return notification
    
    def show_notification_with_animation(self, notification):
        # Create fade-in animation
        self.fade_in_animation = QPropertyAnimation(notification, b"windowOpacity")
        self.fade_in_animation.setDuration(300)
        self.fade_in_animation.setStartValue(0.0)
        self.fade_in_animation.setEndValue(1.0)
        self.fade_in_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_in_animation.start()
    
    def hide_notification(self, notification):
        # Create fade-out animation
        self.fade_out_animation = QPropertyAnimation(notification, b"windowOpacity")
        self.fade_out_animation.setDuration(300)
        self.fade_out_animation.setStartValue(1.0)
        self.fade_out_animation.setEndValue(0.0)
        self.fade_out_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_out_animation.finished.connect(
            lambda: self.remove_notification(notification)
        )
        self.fade_out_animation.start()
    
    def remove_notification(self, notification):
        # Remove from container
        self.container.layout().removeWidget(notification)
        
        # Remove from notifications list
        if notification in self.notifications:
            self.notifications.remove(notification)
        
        # Delete notification
        notification.deleteLater()
    
    def limit_notifications(self):
        # Remove oldest notifications if too many
        while len(self.notifications) > self.max_notifications:
            oldest_notification = self.notifications.pop(0)
            self.remove_notification(oldest_notification)
    
    def hide_all_notifications(self):
        # Create a copy to avoid modifying the list while iterating
        notifications = self.notifications.copy()
        
        # Hide each notification
        for notification in notifications:
            self.hide_notification(notification)
```

2. Dialog Manager:
```python
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit

class DialogManager:
    def __init__(self):
        self.active_dialog = None
    
    def show_error_dialog(self, title, message, details=None, options=None):
        return self.show_dialog("error", title, message, details, options)
    
    def show_warning_dialog(self, title, message, options=None):
        return self.show_dialog("warning", title, message, None, options)
    
    def show_success_dialog(self, title, message, options=None):
        return self.show_dialog("success", title, message, None, options)
    
    def show_info_dialog(self, title, message, options=None):
        return self.show_dialog("info", title, message, None, options)
    
    def show_dialog(self, dialog_type, title, message, details=None, options=None):
        # Create dialog
        dialog = QDialog()
        dialog.setWindowTitle(title)
        dialog.setMinimumWidth(400)
        dialog.setModal(True)
        
        # Create layout
        layout = QVBoxLayout(dialog)
        
        # Create header
        header_layout = QHBoxLayout()
        
        # Add icon
        icon_label = QLabel()
        icon_label.setText(self.get_icon_for_type(dialog_type))
        header_layout.addWidget(icon_label)
        
        # Add title
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; font-size: 14pt;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Add message
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        layout.addWidget(message_label)
        
        # Add details if provided
        if details:
            details_text = QTextEdit()
            details_text.setPlainText(details)
            details_text.setReadOnly(True)
            details_text.setMaximumHeight(100)
            layout.addWidget(details_text)
        
        # Add buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        # Default buttons
        buttons = options.get("buttons", ["OK"]) if options else ["OK"]
        
        for button_text in buttons:
            button = QPushButton(button_text)
            
            # Set result based on button text
            if button_text.upper() == "OK":
                button.clicked.connect(lambda: dialog.accept())
            elif button_text.upper() == "CANCEL":
                button.clicked.connect(lambda: dialog.reject())
            elif button_text.upper() == "YES":
                button.clicked.connect(lambda: dialog.accept())
                button.setStyleSheet("background-color: #0078d4; color: white;")
            elif button_text.upper() == "NO":
                button.clicked.connect(lambda: dialog.reject())
            
            buttons_layout.addWidget(button)
        
        layout.addLayout(buttons_layout)
        
        # Show dialog
        self.active_dialog = dialog
        result = dialog.exec_()
        
        # Reset active dialog
        self.active_dialog = None
        
        return result == QDialog.Accepted
    
    def get_icon_for_type(self, dialog_type):
        if dialog_type == "info":
            return "ℹ"
        elif dialog_type == "success":
            return "✓"
        elif dialog_type == "warning":
            return "⚠"
        elif dialog_type == "error":
            return "✕"
        else:
            return ""
```

3. Progress Manager:
```python
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QPushButton

class ProgressWidget(QWidget):
    def __init__(self, title, status, on_cancel=None):
        super().__init__()
        self.setup_ui(title, status, on_cancel)
    
    def setup_ui(self, title, status, on_cancel):
        # Set layout
        layout = QVBoxLayout(self)
        
        # Create header
        header_layout = QHBoxLayout()
        
        # Add title
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(title_label)
        
        # Add percentage
        self.percentage_label = QLabel("0%")
        header_layout.addWidget(self.percentage_label)
        
        layout.addLayout(header_layout)
        
        # Create progress bar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        # Create status
        status_layout = QHBoxLayout()
        
        # Add status text
        self.status_label = QLabel(status)
        status_layout.addWidget(self.status_label)
        
        # Add cancel button if provided
        if on_cancel:
            cancel_button = QPushButton("Cancel")
            cancel_button.clicked.connect(on_cancel)
            status_layout.addWidget(cancel_button)
        
        status_layout.addStretch()
        layout.addLayout(status_layout)
    
    def update_progress(self, value, max_value, status=None):
        # Calculate percentage
        percentage = int((value / max_value) * 100) if max_value > 0 else 0
        
        # Update percentage
        self.percentage_label.setText(f"{percentage}%")
        
        # Update progress bar
        self.progress_bar.setMaximum(max_value)
        self.progress_bar.setValue(value)
        
        # Update status if provided
        if status:
            self.status_label.setText(status)
    
    def complete(self, message="Complete"):
        # Update to 100%
        self.update_progress(100, 100, message)
        
        # Add success style
        self.setStyleSheet("background-color: #d4edda; border: 1px solid #c3e6cb;")
    
    def error(self, message="Error"):
        # Update status
        self.status_label.setText(message)
        
        # Add error style
        self.setStyleSheet("background-color: #f8d7da; border: 1px solid #f5c6cb;")

class ProgressManager:
    def __init__(self):
        self.active_progress = None
        self.progress_container = self.create_progress_container()
    
    def create_progress_container(self):
        # Create container widget
        container = QWidget()
        container.setObjectName("progress_container")
        container.setFixedWidth(400)
        
        # Set layout
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Add to main window
        main_window = QApplication.instance().mainWindow
        main_window.add_progress_widget(container)
        
        return container
    
    def show_progress(self, title, status, on_cancel=None):
        # Hide any existing progress
        if self.active_progress:
            self.hide_progress()
        
        # Create progress widget
        progress_widget = ProgressWidget(title, status, on_cancel)
        
        # Add to container
        self.progress_container.layout().addWidget(progress_widget)
        
        # Set as active progress
        self.active_progress = progress_widget
        
        # Return progress controller
        return ProgressController(progress_widget, self)
    
    def hide_progress(self):
        if self.active_progress:
            # Remove from container
            self.progress_container.layout().removeWidget(self.active_progress)
            
            # Delete progress widget
            self.active_progress.deleteLater()
            self.active_progress = None

class ProgressController:
    def __init__(self, progress_widget, manager):
        self.progress_widget = progress_widget
        self.manager = manager
    
    def update_progress(self, value, max_value, status=None):
        self.progress_widget.update_progress(value, max_value, status)
    
    def complete(self, message="Complete"):
        self.progress_widget.complete(message)
        
        # Hide after delay
        QTimer.singleShot(2000, self.manager.hide_progress)
    
    def error(self, message="Error"):
        self.progress_widget.error(message)
        
        # Hide after delay
        QTimer.singleShot(3000, self.manager.hide_progress)
    
    def hide(self):
        self.manager.hide_progress()
```
*/