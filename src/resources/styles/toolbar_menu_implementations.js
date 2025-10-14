/**
 * Toolbar and Menu Implementations for 3D-MM Application
 * 
 * This JavaScript file demonstrates how to implement enhanced toolbar and menu organization,
 * which can be translated to the Python/PySide6 application.
 */

// ================================
// TOOLBAR MANAGER
// ================================

/**
 * Toolbar manager for organizing and managing toolbars
 */
class ToolbarManager {
    constructor() {
        this.toolbars = {};
        this.toolbarGroups = {};
        this.responsiveMode = this.detectResponsiveMode();
        this.setupResponsiveHandling();
    }
    
    /**
     * Detect responsive mode based on screen size
     * @returns {string} Responsive mode
     */
    detectResponsiveMode() {
        const width = window.innerWidth;
        
        if (width <= 600) {
            return 'small';
        } else if (width <= 800) {
            return 'medium';
        } else {
            return 'large';
        }
    }
    
    /**
     * Set up responsive handling
     */
    setupResponsiveHandling() {
        window.addEventListener('resize', () => {
            const newMode = this.detectResponsiveMode();
            if (newMode !== this.responsiveMode) {
                this.responsiveMode = newMode;
                this.updateToolbarLayout();
            }
        });
    }
    
    /**
     * Create a toolbar
     * @param {string} id - Toolbar ID
     * @param {string} title - Toolbar title
     * @param {HTMLElement} container - Container element
     * @returns {HTMLElement} Toolbar element
     */
    createToolbar(id, title, container) {
        // Create toolbar element
        const toolbar = document.createElement('div');
        toolbar.className = 'main-toolbar';
        toolbar.id = id;
        toolbar.setAttribute('role', 'toolbar');
        toolbar.setAttribute('aria-label', title);
        
        // Add to container
        container.appendChild(toolbar);
        
        // Store toolbar
        this.toolbars[id] = toolbar;
        
        return toolbar;
    }
    
    /**
     * Add a group to a toolbar
     * @param {string} toolbarId - Toolbar ID
     * @param {string} groupId - Group ID
     * @param {string} label - Group label
     * @returns {HTMLElement} Group element
     */
    addToolbarGroup(toolbarId, groupId, label) {
        const toolbar = this.toolbars[toolbarId];
        if (!toolbar) return null;
        
        // Create group element
        const group = document.createElement('div');
        group.className = 'toolbar-group';
        group.id = groupId;
        group.setAttribute('role', 'group');
        
        // Add label if provided
        if (label) {
            const labelElement = document.createElement('div');
            labelElement.className = 'toolbar-group-label';
            labelElement.textContent = label;
            group.appendChild(labelElement);
        }
        
        // Add to toolbar
        toolbar.appendChild(group);
        
        // Store group
        this.toolbarGroups[groupId] = group;
        
        return group;
    }
    
    /**
     * Add a button to a toolbar group
     * @param {string} groupId - Group ID
     * @param {string} buttonId - Button ID
     * @param {string} text - Button text
     * @param {string} icon - Button icon
     * @param {Function} callback - Button callback
     * @param {Object} options - Button options
     * @returns {HTMLElement} Button element
     */
    addToolbarButton(groupId, buttonId, text, icon, callback, options = {}) {
        const group = this.toolbarGroups[groupId];
        if (!group) return null;
        
        // Create button element
        const button = document.createElement('button');
        button.className = 'toolbar-button';
        button.id = buttonId;
        button.setAttribute('aria-label', text);
        
        // Add icon if provided
        if (icon) {
            const iconElement = document.createElement('span');
            iconElement.className = 'toolbar-button-icon';
            iconElement.innerHTML = icon;
            button.appendChild(iconElement);
            
            if (text) {
                button.className += ' toolbar-button-icon-text';
            } else {
                button.className += ' toolbar-button-icon';
            }
        } else if (text) {
            button.className += ' toolbar-button-text';
            button.textContent = text;
        }
        
        // Add tooltip if provided
        if (options.tooltip) {
            button.title = options.tooltip;
        }
        
        // Add keyboard shortcut if provided
        if (options.shortcut) {
            button.setAttribute('data-shortcut', options.shortcut);
            
            // Add keyboard hint in responsive mode
            if (this.responsiveMode === 'large') {
                const shortcutElement = document.createElement('span');
                shortcutElement.className = 'toolbar-button-keyboard-hint';
                shortcutElement.textContent = options.shortcut;
                button.appendChild(shortcutElement);
            }
        }
        
        // Add click handler
        button.addEventListener('click', () => {
            // Visual feedback
            this.animateButton(button);
            
            // Call callback
            if (callback) callback();
        });
        
        // Add to group
        group.appendChild(button);
        
        // Store button reference
        if (!group.buttons) group.buttons = {};
        group.buttons[buttonId] = button;
        
        return button;
    }
    
    /**
     * Add a separator to a toolbar group
     * @param {string} groupId - Group ID
     * @returns {HTMLElement} Separator element
     */
    addToolbarSeparator(groupId) {
        const group = this.toolbarGroups[groupId];
        if (!group) return null;
        
        // Create separator element
        const separator = document.createElement('div');
        separator.className = 'toolbar-separator';
        separator.setAttribute('role', 'separator');
        
        // Add to group
        group.appendChild(separator);
        
        return separator;
    }
    
    /**
     * Animate button press
     * @param {HTMLElement} button - Button element
     */
    animateButton(button) {
        // Add animation class
        button.classList.add('toolbar-button-animation');
        
        // Remove after animation completes
        setTimeout(() => {
            button.classList.remove('toolbar-button-animation');
        }, 300);
    }
    
    /**
     * Update toolbar layout based on responsive mode
     */
    updateToolbarLayout() {
        // Update all toolbars
        Object.keys(this.toolbars).forEach(toolbarId => {
            this.updateToolbar(toolbarId);
        });
    }
    
    /**
     * Update a specific toolbar
     * @param {string} toolbarId - Toolbar ID
     */
    updateToolbar(toolbarId) {
        const toolbar = this.toolbars[toolbarId];
        if (!toolbar) return;
        
        // Update based on responsive mode
        switch (this.responsiveMode) {
            case 'small':
                this.updateToolbarForSmallScreen(toolbar);
                break;
            case 'medium':
                this.updateToolbarForMediumScreen(toolbar);
                break;
            case 'large':
                this.updateToolbarForLargeScreen(toolbar);
                break;
        }
    }
    
    /**
     * Update toolbar for small screen
     * @param {HTMLElement} toolbar - Toolbar element
     */
    updateToolbarForSmallScreen(toolbar) {
        // Hide group labels
        const labels = toolbar.querySelectorAll('.toolbar-group-label');
        labels.forEach(label => {
            label.style.display = 'none';
        });
        
        // Hide text-only buttons
        const textButtons = toolbar.querySelectorAll('.toolbar-button-text');
        textButtons.forEach(button => {
            button.style.display = 'none';
        });
        
        // Hide keyboard hints
        const hints = toolbar.querySelectorAll('.toolbar-button-keyboard-hint');
        hints.forEach(hint => {
            hint.style.display = 'none';
        });
        
        // Collapse groups into overflow menu if needed
        this.collapseToolbar(toolbar);
    }
    
    /**
     * Update toolbar for medium screen
     * @param {HTMLElement} toolbar - Toolbar element
     */
    updateToolbarForMediumScreen(toolbar) {
        // Show group labels
        const labels = toolbar.querySelectorAll('.toolbar-group-label');
        labels.forEach(label => {
            label.style.display = 'block';
        });
        
        // Show text-only buttons
        const textButtons = toolbar.querySelectorAll('.toolbar-button-text');
        textButtons.forEach(button => {
            button.style.display = 'block';
        });
        
        // Hide keyboard hints
        const hints = toolbar.querySelectorAll('.toolbar-button-keyboard-hint');
        hints.forEach(hint => {
            hint.style.display = 'none';
        });
        
        // Collapse groups into overflow menu if needed
        this.collapseToolbar(toolbar);
    }
    
    /**
     * Update toolbar for large screen
     * @param {HTMLElement} toolbar - Toolbar element
     */
    updateToolbarForLargeScreen(toolbar) {
        // Show group labels
        const labels = toolbar.querySelectorAll('.toolbar-group-label');
        labels.forEach(label => {
            label.style.display = 'block';
        });
        
        // Show text-only buttons
        const textButtons = toolbar.querySelectorAll('.toolbar-button-text');
        textButtons.forEach(button => {
            button.style.display = 'block';
        });
        
        // Show keyboard hints
        const hints = toolbar.querySelectorAll('.toolbar-button-keyboard-hint');
        hints.forEach(hint => {
            hint.style.display = 'inline';
        });
        
        // Expand all groups
        this.expandToolbar(toolbar);
    }
    
    /**
     * Collapse toolbar into overflow menu
     * @param {HTMLElement} toolbar - Toolbar element
     */
    collapseToolbar(toolbar) {
        // Check if toolbar needs collapsing
        if (toolbar.offsetWidth < toolbar.scrollWidth) {
            // Create overflow menu if it doesn't exist
            let overflowButton = toolbar.querySelector('.toolbar-overflow-button');
            if (!overflowButton) {
                overflowButton = this.createOverflowButton(toolbar);
            }
            
            // Move buttons to overflow menu as needed
            this.moveButtonsToOverflow(toolbar);
        }
    }
    
    /**
     * Expand toolbar from overflow menu
     * @param {HTMLElement} toolbar - Toolbar element
     */
    expandToolbar(toolbar) {
        // Remove overflow menu if it exists
        const overflowButton = toolbar.querySelector('.toolbar-overflow-button');
        if (overflowButton) {
            toolbar.removeChild(overflowButton);
        }
        
        // Move all buttons back to toolbar
        this.moveButtonsFromOverflow(toolbar);
    }
    
    /**
     * Create overflow button
     * @param {HTMLElement} toolbar - Toolbar element
     * @returns {HTMLElement} Overflow button element
     */
    createOverflowButton(toolbar) {
        // Create overflow button
        const overflowButton = document.createElement('button');
        overflowButton.className = 'toolbar-button toolbar-overflow-button';
        overflowButton.innerHTML = '⋯';
        overflowButton.setAttribute('aria-label', 'More options');
        
        // Create overflow menu
        const overflowMenu = document.createElement('div');
        overflowMenu.className = 'overflow-menu';
        overflowMenu.style.display = 'none';
        
        // Add to toolbar
        toolbar.appendChild(overflowButton);
        toolbar.appendChild(overflowMenu);
        
        // Add click handler
        overflowButton.addEventListener('click', () => {
            const isVisible = overflowMenu.style.display !== 'none';
            overflowMenu.style.display = isVisible ? 'none' : 'block';
            
            // Position menu
            if (!isVisible) {
                const rect = overflowButton.getBoundingClientRect();
                overflowMenu.style.position = 'absolute';
                overflowMenu.style.right = '0px';
                overflowMenu.style.top = `${rect.height}px`;
                overflowMenu.style.zIndex = '1000';
            }
        });
        
        // Hide menu when clicking outside
        document.addEventListener('click', (event) => {
            if (!overflowButton.contains(event.target) && !overflowMenu.contains(event.target)) {
                overflowMenu.style.display = 'none';
            }
        });
        
        return overflowButton;
    }
    
    /**
     * Move buttons to overflow menu
     * @param {HTMLElement} toolbar - Toolbar element
     */
    moveButtonsToOverflow(toolbar) {
        const overflowButton = toolbar.querySelector('.toolbar-overflow-button');
        const overflowMenu = toolbar.querySelector('.overflow-menu');
        
        if (!overflowButton || !overflowMenu) return;
        
        // Get all buttons except overflow button
        const buttons = Array.from(toolbar.querySelectorAll('.toolbar-button:not(.toolbar-overflow-button)'));
        
        // Start from the end and move buttons to overflow menu until toolbar fits
        for (let i = buttons.length - 1; i >= 0; i--) {
            const button = buttons[i];
            
            // Check if button is already in overflow menu
            if (button.parentElement === overflowMenu) continue;
            
            // Check if toolbar fits without this button
            toolbar.removeChild(button);
            
            if (toolbar.offsetWidth >= toolbar.scrollWidth) {
                // Toolbar fits, add button to overflow menu
                overflowMenu.appendChild(button);
            } else {
                // Toolbar doesn't fit, add button back
                toolbar.insertBefore(button, overflowButton);
                break;
            }
        }
    }
    
    /**
     * Move buttons from overflow menu
     * @param {HTMLElement} toolbar - Toolbar element
     */
    moveButtonsFromOverflow(toolbar) {
        const overflowButton = toolbar.querySelector('.toolbar-overflow-button');
        const overflowMenu = toolbar.querySelector('.overflow-menu');
        
        if (!overflowMenu) return;
        
        // Move all buttons back to toolbar
        const buttons = Array.from(overflowMenu.querySelectorAll('.toolbar-button'));
        
        buttons.forEach(button => {
            overflowMenu.removeChild(button);
            toolbar.insertBefore(button, overflowButton);
        });
    }
}

// Create global toolbar manager
const toolbarManager = new ToolbarManager();

// ================================
// MENU MANAGER
// ================================

/**
 * Menu manager for organizing and managing menus
 */
class MenuManager {
    constructor() {
        this.menus = {};
        this.contextMenus = {};
        this.menuShortcuts = {};
        this.setupKeyboardShortcuts();
    }
    
    /**
     * Create a menu bar
     * @param {string} id - Menu bar ID
     * @param {HTMLElement} container - Container element
     * @returns {HTMLElement} Menu bar element
     */
    createMenuBar(id, container) {
        // Create menu bar element
        const menuBar = document.createElement('div');
        menuBar.className = 'menu-bar';
        menuBar.id = id;
        menuBar.setAttribute('role', 'menubar');
        
        // Add to container
        container.appendChild(menuBar);
        
        // Store menu bar
        this.menus[id] = menuBar;
        
        return menuBar;
    }
    
    /**
     * Add a menu to a menu bar
     * @param {string} menuBarId - Menu bar ID
     * @param {string} menuId - Menu ID
     * @param {string} text - Menu text
     * @returns {HTMLElement} Menu element
     */
    addMenu(menuBarId, menuId, text) {
        const menuBar = this.menus[menuBarId];
        if (!menuBar) return null;
        
        // Create menu item element
        const menuItem = document.createElement('div');
        menuItem.className = 'menu-bar-item';
        menuItem.id = menuId;
        menuItem.setAttribute('role', 'menuitem');
        menuItem.setAttribute('aria-haspopup', 'true');
        menuItem.setAttribute('aria-expanded', 'false');
        menuItem.textContent = text;
        
        // Create dropdown menu
        const dropdownMenu = document.createElement('div');
        dropdownMenu.className = 'dropdown-menu';
        dropdownMenu.id = `${menuId}-dropdown`;
        dropdownMenu.setAttribute('role', 'menu');
        dropdownMenu.style.display = 'none';
        
        // Add to menu bar
        menuBar.appendChild(menuItem);
        menuBar.appendChild(dropdownMenu);
        
        // Set up menu interaction
        this.setupMenuInteraction(menuItem, dropdownMenu);
        
        // Store menu
        this.menus[menuId] = dropdownMenu;
        
        return dropdownMenu;
    }
    
    /**
     * Add a menu item to a menu
     * @param {string} menuId - Menu ID
     * @param {string} itemId - Item ID
     * @param {string} text - Item text
     * @param {Function} callback - Item callback
     * @param {Object} options - Item options
     * @returns {HTMLElement} Menu item element
     */
    addMenuItem(menuId, itemId, text, callback, options = {}) {
        const menu = this.menus[menuId];
        if (!menu) return null;
        
        // Create menu item element
        const menuItem = document.createElement('div');
        menuItem.className = 'dropdown-menu-item';
        menuItem.id = itemId;
        menuItem.setAttribute('role', 'menuitem');
        menuItem.textContent = text;
        
        // Add icon if provided
        if (options.icon) {
            menuItem.className += ' dropdown-menu-item-icon';
            menuItem.style.backgroundImage = `url(${options.icon})`;
        }
        
        // Add checkbox if provided
        if (options.checkbox) {
            menuItem.className += ' dropdown-menu-item-checkbox';
            if (options.checked) {
                menuItem.classList.add('checked');
            }
        }
        
        // Add shortcut if provided
        if (options.shortcut) {
            this.menuShortcuts[options.shortcut] = {
                menuId,
                itemId,
                callback
            };
            
            // Add shortcut text
            const shortcutElement = document.createElement('span');
            shortcutElement.className = 'dropdown-menu-item-shortcut';
            shortcutElement.textContent = options.shortcut;
            menuItem.appendChild(shortcutElement);
        }
        
        // Add click handler
        menuItem.addEventListener('click', () => {
            // Handle checkbox if needed
            if (options.checkbox) {
                menuItem.classList.toggle('checked');
                const isChecked = menuItem.classList.contains('checked');
                
                // Call callback with checked state
                if (callback) callback(isChecked);
            } else {
                // Call callback
                if (callback) callback();
            }
            
            // Close menu
            this.closeMenu(menuId);
        });
        
        // Add to menu
        menu.appendChild(menuItem);
        
        return menuItem;
    }
    
    /**
     * Add a separator to a menu
     * @param {string} menuId - Menu ID
     * @returns {HTMLElement} Separator element
     */
    addMenuSeparator(menuId) {
        const menu = this.menus[menuId];
        if (!menu) return null;
        
        // Create separator element
        const separator = document.createElement('div');
        separator.className = 'dropdown-menu-separator';
        separator.setAttribute('role', 'separator');
        
        // Add to menu
        menu.appendChild(separator);
        
        return separator;
    }
    
    /**
     * Set up menu interaction
     * @param {HTMLElement} menuItem - Menu item element
     * @param {HTMLElement} dropdownMenu - Dropdown menu element
     */
    setupMenuInteraction(menuItem, dropdownMenu) {
        // Show menu on hover
        menuItem.addEventListener('mouseenter', () => {
            this.showMenu(menuItem.id);
        });
        
        menuItem.addEventListener('mouseleave', (event) => {
            // Check if mouse is moving to dropdown menu
            if (!event.relatedTarget || !dropdownMenu.contains(event.relatedTarget)) {
                // Hide menu after a delay to allow moving to dropdown
                setTimeout(() => {
                    if (!dropdownMenu.matches(':hover')) {
                        this.closeMenu(menuItem.id);
                    }
                }, 100);
            }
        });
        
        dropdownMenu.addEventListener('mouseleave', (event) => {
            // Check if mouse is moving back to menu item
            if (!event.relatedTarget || !menuItem.contains(event.relatedTarget)) {
                // Hide menu after a delay to allow moving to menu item
                setTimeout(() => {
                    if (!menuItem.matches(':hover')) {
                        this.closeMenu(menuItem.id);
                    }
                }, 100);
            }
        });
        
        // Show menu on click for touch devices
        menuItem.addEventListener('click', () => {
            const isExpanded = menuItem.getAttribute('aria-expanded') === 'true';
            if (isExpanded) {
                this.closeMenu(menuItem.id);
            } else {
                this.showMenu(menuItem.id);
            }
        });
        
        // Hide menu when clicking outside
        document.addEventListener('click', (event) => {
            if (!menuItem.contains(event.target) && !dropdownMenu.contains(event.target)) {
                this.closeMenu(menuItem.id);
            }
        });
    }
    
    /**
     * Show a menu
     * @param {string} menuId - Menu ID
     */
    showMenu(menuId) {
        // Close all other menus
        Object.keys(this.menus).forEach(id => {
            if (id !== menuId && id !== `${menuId}-dropdown`) {
                this.closeMenu(id);
            }
        });
        
        const menuItem = document.getElementById(menuId);
        const dropdownMenu = document.getElementById(`${menuId}-dropdown`);
        
        if (menuItem && dropdownMenu) {
            // Show menu
            dropdownMenu.style.display = 'block';
            
            // Update aria attributes
            menuItem.setAttribute('aria-expanded', 'true');
            
            // Add animation class
            dropdownMenu.classList.add('menu-animation');
            
            // Position menu
            const rect = menuItem.getBoundingClientRect();
            dropdownMenu.style.position = 'absolute';
            dropdownMenu.style.left = `${rect.left}px`;
            dropdownMenu.style.top = `${rect.bottom}px`;
            dropdownMenu.style.zIndex = '1000';
        }
    }
    
    /**
     * Close a menu
     * @param {string} menuId - Menu ID
     */
    closeMenu(menuId) {
        const menuItem = document.getElementById(menuId);
        const dropdownMenu = document.getElementById(`${menuId}-dropdown`);
        
        if (menuItem && dropdownMenu) {
            // Hide menu
            dropdownMenu.style.display = 'none';
            
            // Update aria attributes
            menuItem.setAttribute('aria-expanded', 'false');
        }
    }
    
    /**
     * Create a context menu
     * @param {string} id - Context menu ID
     * @returns {HTMLElement} Context menu element
     */
    createContextMenu(id) {
        // Create context menu element
        const contextMenu = document.createElement('div');
        contextMenu.className = 'context-menu';
        contextMenu.id = id;
        contextMenu.setAttribute('role', 'menu');
        contextMenu.style.display = 'none';
        
        // Add to document
        document.body.appendChild(contextMenu);
        
        // Store context menu
        this.contextMenus[id] = contextMenu;
        
        return contextMenu;
    }
    
    /**
     * Show a context menu
     * @param {string} id - Context menu ID
     * @param {number} x - X position
     * @param {number} y - Y position
     */
    showContextMenu(id, x, y) {
        const contextMenu = this.contextMenus[id];
        if (!contextMenu) return;
        
        // Close all other context menus
        Object.keys(this.contextMenus).forEach(menuId => {
            if (menuId !== id) {
                this.closeContextMenu(menuId);
            }
        });
        
        // Position menu
        contextMenu.style.position = 'fixed';
        contextMenu.style.left = `${x}px`;
        contextMenu.style.top = `${y}px`;
        contextMenu.style.zIndex = '1000';
        
        // Show menu
        contextMenu.style.display = 'block';
        
        // Add animation class
        contextMenu.classList.add('menu-animation');
        
        // Adjust position if menu goes off screen
        const rect = contextMenu.getBoundingClientRect();
        
        if (rect.right > window.innerWidth) {
            contextMenu.style.left = `${x - rect.width}px`;
        }
        
        if (rect.bottom > window.innerHeight) {
            contextMenu.style.top = `${y - rect.height}px`;
        }
    }
    
    /**
     * Close a context menu
     * @param {string} id - Context menu ID
     */
    closeContextMenu(id) {
        const contextMenu = this.contextMenus[id];
        if (contextMenu) {
            contextMenu.style.display = 'none';
        }
    }
    
    /**
     * Add an item to a context menu
     * @param {string} menuId - Context menu ID
     * @param {string} itemId - Item ID
     * @param {string} text - Item text
     * @param {Function} callback - Item callback
     * @param {Object} options - Item options
     * @returns {HTMLElement} Menu item element
     */
    addContextMenuItem(menuId, itemId, text, callback, options = {}) {
        const contextMenu = this.contextMenus[menuId];
        if (!contextMenu) return null;
        
        // Create menu item element
        const menuItem = document.createElement('div');
        menuItem.className = 'context-menu-item';
        menuItem.id = itemId;
        menuItem.setAttribute('role', 'menuitem');
        menuItem.textContent = text;
        
        // Add icon if provided
        if (options.icon) {
            menuItem.className += ' context-menu-item-icon';
            menuItem.style.backgroundImage = `url(${options.icon})`;
        }
        
        // Add checkbox if provided
        if (options.checkbox) {
            menuItem.className += ' context-menu-item-checkbox';
            if (options.checked) {
                menuItem.classList.add('checked');
            }
        }
        
        // Add click handler
        menuItem.addEventListener('click', () => {
            // Handle checkbox if needed
            if (options.checkbox) {
                menuItem.classList.toggle('checked');
                const isChecked = menuItem.classList.contains('checked');
                
                // Call callback with checked state
                if (callback) callback(isChecked);
            } else {
                // Call callback
                if (callback) callback();
            }
            
            // Close context menu
            this.closeContextMenu(menuId);
        });
        
        // Add to context menu
        contextMenu.appendChild(menuItem);
        
        return menuItem;
    }
    
    /**
     * Add a separator to a context menu
     * @param {string} menuId - Context menu ID
     * @returns {HTMLElement} Separator element
     */
    addContextMenuSeparator(menuId) {
        const contextMenu = this.contextMenus[menuId];
        if (!contextMenu) return null;
        
        // Create separator element
        const separator = document.createElement('div');
        separator.className = 'context-menu-separator';
        separator.setAttribute('role', 'separator');
        
        // Add to context menu
        contextMenu.appendChild(separator);
        
        return separator;
    }
    
    /**
     * Set up keyboard shortcuts
     */
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (event) => {
            // Check if Alt key is pressed
            if (event.altKey) {
                const key = event.key;
                const shortcut = `Alt+${key}`;
                
                // Check if shortcut is registered
                if (this.menuShortcuts[shortcut]) {
                    const { menuId, itemId, callback } = this.menuShortcuts[shortcut];
                    
                    // Show menu
                    this.showMenu(menuId);
                    
                    // Focus menu item
                    const menuItem = document.getElementById(itemId);
                    if (menuItem) {
                        menuItem.focus();
                    }
                    
                    // Call callback
                    if (callback) callback();
                    
                    // Prevent default
                    event.preventDefault();
                }
            }
        });
    }
}

// Create global menu manager
const menuManager = new MenuManager();

// ================================
// ================================
// TOOLBAR CUSTOMIZATION
// ================================

/**
 * Toolbar customization manager for customizing toolbars
 */
class ToolbarCustomizationManager {
    constructor(toolbarManager) {
        this.toolbarManager = toolbarManager;
        this.customizationDialog = null;
        this.availableActions = [];
        this.setupAvailableActions();
    }
    
    /**
     * Set up available actions
     */
    setupAvailableActions() {
        // Define available actions
        this.availableActions = [
            { id: 'new', text: 'New', icon: '📄', category: 'File' },
            { id: 'open', text: 'Open', icon: '📁', category: 'File' },
            { id: 'save', text: 'Save', icon: '💾', category: 'File' },
            { id: 'save-as', text: 'Save As', icon: '💾', category: 'File' },
            { id: 'undo', text: 'Undo', icon: '↶', category: 'Edit' },
            { id: 'redo', text: 'Redo', icon: '↷', category: 'Edit' },
            { id: 'cut', text: 'Cut', icon: '✂', category: 'Edit' },
            { id: 'copy', text: 'Copy', icon: '📋', category: 'Edit' },
            { id: 'paste', text: 'Paste', icon: '📋', category: 'Edit' },
            { id: 'delete', text: 'Delete', icon: '🗑', category: 'Edit' },
            { id: 'zoom-in', text: 'Zoom In', icon: '🔍', category: 'View' },
            { id: 'zoom-out', text: 'Zoom Out', icon: '🔍', category: 'View' },
            { id: 'zoom-fit', text: 'Zoom to Fit', icon: '🔍', category: 'View' },
            { id: 'zoom-actual', text: 'Actual Size', icon: '🔍', category: 'View' },
            { id: 'rotate-left', text: 'Rotate Left', icon: '↺', category: 'View' },
            { id: 'rotate-right', text: 'Rotate Right', icon: '↻', category: 'View' },
            { id: 'wireframe', text: 'Wireframe', icon: '⊞', category: 'View' },
            { id: 'solid', text: 'Solid', icon: '◼', category: 'View' },
            { id: 'textured', text: 'Textured', icon: '🎨', category: 'View' }
        ];
    }
    
    /**
     * Show customization dialog
     * @param {string} toolbarId - Toolbar ID to customize
     */
    showCustomizationDialog(toolbarId) {
        // Create dialog if it doesn't exist
        if (!this.customizationDialog) {
            this.customizationDialog = this.createCustomizationDialog();
        }
        
        // Set up dialog for toolbar
        this.setupDialogForToolbar(toolbarId);
        
        // Show dialog
        this.customizationDialog.style.display = 'block';
    }
    
    /**
     * Create customization dialog
     * @returns {HTMLElement} Dialog element
     */
    createCustomizationDialog() {
        // Create dialog overlay
        const overlay = document.createElement('div');
        overlay.className = 'customization-dialog-overlay';
        
        // Create dialog
        const dialog = document.createElement('div');
        dialog.className = 'toolbar-customization';
        
        // Create header
        const header = document.createElement('div');
        header.className = 'customization-dialog-header';
        header.textContent = 'Customize Toolbar';
        
        // Create content
        const content = document.createElement('div');
        content.className = 'customization-dialog-content';
        
        // Create available actions list
        const availableLabel = document.createElement('div');
        availableLabel.textContent = 'Available Actions:';
        content.appendChild(availableLabel);
        
        const availableList = document.createElement('div');
        availableList.className = 'toolbar-customization-list';
        availableList.id = 'available-actions-list';
        content.appendChild(availableList);
        
        // Create current actions list
        const currentLabel = document.createElement('div');
        currentLabel.textContent = 'Current Actions:';
        content.appendChild(currentLabel);
        
        const currentList = document.createElement('div');
        currentList.className = 'toolbar-customization-list';
        currentList.id = 'current-actions-list';
        content.appendChild(currentList);
        
        // Create buttons
        const buttons = document.createElement('div');
        buttons.className = 'toolbar-customization-buttons';
        
        const addButton = document.createElement('button');
        addButton.className = 'toolbar-customization-button';
        addButton.textContent = 'Add →';
        addButton.disabled = true;
        
        const removeButton = document.createElement('button');
        removeButton.className = 'toolbar-customization-button';
        removeButton.textContent = '← Remove';
        removeButton.disabled = true;
        
        const resetButton = document.createElement('button');
        resetButton.className = 'toolbar-customization-button';
        resetButton.textContent = 'Reset';
        
        const okButton = document.createElement('button');
        okButton.className = 'toolbar-customization-button primary';
        okButton.textContent = 'OK';
        
        const cancelButton = document.createElement('button');
        cancelButton.className = 'toolbar-customization-button';
        cancelButton.textContent = 'Cancel';
        
        buttons.appendChild(addButton);
        buttons.appendChild(removeButton);
        buttons.appendChild(resetButton);
        buttons.appendChild(okButton);
        buttons.appendChild(cancelButton);
        
        // Add to dialog
        dialog.appendChild(header);
        dialog.appendChild(content);
        dialog.appendChild(buttons);
        overlay.appendChild(dialog);
        
        // Add to document
        document.body.appendChild(overlay);
        
        // Set up event handlers
        this.setupDialogEventHandlers(overlay, dialog, addButton, removeButton, resetButton, okButton, cancelButton);
        
        return overlay;
    }
    
    /**
     * Set up dialog event handlers
     * @param {HTMLElement} overlay - Dialog overlay
     * @param {HTMLElement} dialog - Dialog element
     * @param {HTMLElement} addButton - Add button
     * @param {HTMLElement} removeButton - Remove button
     * @param {HTMLElement} resetButton - Reset button
     * @param {HTMLElement} okButton - OK button
     * @param {HTMLElement} cancelButton - Cancel button
     */
    setupDialogEventHandlers(overlay, dialog, addButton, removeButton, resetButton, okButton, cancelButton) {
        // Close dialog on cancel
        cancelButton.addEventListener('click', () => {
            overlay.style.display = 'none';
        });
        
        // Close dialog on overlay click
        overlay.addEventListener('click', (event) => {
            if (event.target === overlay) {
                overlay.style.display = 'none';
            }
        });
        
        // Add button handler
        addButton.addEventListener('click', () => {
            this.moveSelectedAction('available', 'current');
        });
        
        // Remove button handler
        removeButton.addEventListener('click', () => {
            this.moveSelectedAction('current', 'available');
        });
        
        // Reset button handler
        resetButton.addEventListener('click', () => {
            this.resetToolbarToDefault();
        });
        
        // OK button handler
        okButton.addEventListener('click', () => {
            this.applyToolbarChanges();
            overlay.style.display = 'none';
        });
    }
    
    /**
     * Set up dialog for toolbar
     * @param {string} toolbarId - Toolbar ID
     */
    setupDialogForToolbar(toolbarId) {
        // Store current toolbar ID
        this.currentToolbarId = toolbarId;
        
        // Clear lists
        const availableList = document.getElementById('available-actions-list');
        const currentList = document.getElementById('current-actions-list');
        
        availableList.innerHTML = '';
        currentList.innerHTML = '';
        
        // Get current toolbar actions
        const currentActions = this.getCurrentToolbarActions(toolbarId);
        
        // Populate available actions list
        this.availableActions.forEach(action => {
            // Check if action is already in current actions
            if (!currentActions.find(a => a.id === action.id)) {
                const item = this.createActionItem(action);
                availableList.appendChild(item);
            }
        });
        
        // Populate current actions list
        currentActions.forEach(action => {
            const item = this.createActionItem(action);
            currentList.appendChild(item);
        });
        
        // Set up selection handlers
        this.setupSelectionHandlers(availableList, currentList);
    }
    
    /**
     * Get current toolbar actions
     * @param {string} toolbarId - Toolbar ID
     * @returns {Array} Current actions
     */
    getCurrentToolbarActions(toolbarId) {
        // In a real implementation, this would get the current actions from the toolbar
        // For now, return a default set
        return [
            { id: 'new', text: 'New', icon: '📄' },
            { id: 'open', text: 'Open', icon: '📁' },
            { id: 'save', text: 'Save', icon: '💾' },
            { id: 'undo', text: 'Undo', icon: '↶' },
            { id: 'redo', text: 'Redo', icon: '↷' }
        ];
    }
    
    /**
     * Create action item
     * @param {Object} action - Action object
     * @returns {HTMLElement} Action item element
     */
    createActionItem(action) {
        const item = document.createElement('div');
        item.className = 'toolbar-customization-item';
        item.dataset.actionId = action.id;
        
        // Add icon
        const icon = document.createElement('span');
        icon.textContent = action.icon;
        icon.style.marginRight = '8px';
        item.appendChild(icon);
        
        // Add text
        const text = document.createElement('span');
        text.textContent = action.text;
        item.appendChild(text);
        
        return item;
    }
    
    /**
     * Set up selection handlers
     * @param {HTMLElement} availableList - Available actions list
     * @param {HTMLElement} currentList - Current actions list
     */
    setupSelectionHandlers(availableList, currentList) {
        // Available list selection handler
        availableList.addEventListener('click', (event) => {
            const item = event.target.closest('.toolbar-customization-item');
            if (item) {
                // Toggle selection
                item.classList.toggle('selected');
                
                // Update button states
                this.updateButtonStates();
            }
        });
        
        // Current list selection handler
        currentList.addEventListener('click', (event) => {
            const item = event.target.closest('.toolbar-customization-item');
            if (item) {
                // Toggle selection
                item.classList.toggle('selected');
                
                // Update button states
                this.updateButtonStates();
            }
        });
        
        // Double-click to move
        availableList.addEventListener('dblclick', (event) => {
            const item = event.target.closest('.toolbar-customization-item');
            if (item) {
                item.classList.add('selected');
                this.moveSelectedAction('available', 'current');
            }
        });
        
        currentList.addEventListener('dblclick', (event) => {
            const item = event.target.closest('.toolbar-customization-item');
            if (item) {
                item.classList.add('selected');
                this.moveSelectedAction('current', 'available');
            }
        });
    }
    
    /**
     * Update button states
     */
    updateButtonStates() {
        const availableSelected = document.querySelectorAll('#available-actions-list .selected').length > 0;
        const currentSelected = document.querySelectorAll('#current-actions-list .selected').length > 0;
        
        const addButton = document.querySelector('.toolbar-customization-button');
        const removeButton = document.querySelectorAll('.toolbar-customization-button')[1];
        
        if (addButton) addButton.disabled = !availableSelected;
        if (removeButton) removeButton.disabled = !currentSelected;
    }
    
    /**
     * Move selected action
     * @param {string} fromList - Source list
     * @param {string} toList - Target list
     */
    moveSelectedAction(fromList, toList) {
        const fromElement = document.getElementById(`${fromList}-actions-list`);
        const toElement = document.getElementById(`${toList}-actions-list`);
        
        if (!fromElement || !toElement) return;
        
        // Get selected items
        const selectedItems = Array.from(fromElement.querySelectorAll('.selected'));
        
        // Move items
        selectedItems.forEach(item => {
            // Remove from source list
            fromElement.removeChild(item);
            
            // Remove selection
            item.classList.remove('selected');
            
            // Add to target list
            toElement.appendChild(item);
        });
        
        // Update button states
        this.updateButtonStates();
    }
    
    /**
     * Reset toolbar to default
     */
    resetToolbarToDefault() {
        // Clear current list
        const currentList = document.getElementById('current-actions-list');
        currentList.innerHTML = '';
        
        // Add default actions
        const defaultActions = [
            { id: 'new', text: 'New', icon: '📄' },
            { id: 'open', text: 'Open', icon: '📁' },
            { id: 'save', text: 'Save', icon: '💾' },
            { id: 'undo', text: 'Undo', icon: '↶' },
            { id: 'redo', text: 'Redo', icon: '↷' }
        ];
        
        defaultActions.forEach(action => {
            const item = this.createActionItem(action);
            currentList.appendChild(item);
        });
        
        // Update available list
        this.setupDialogForToolbar(this.currentToolbarId);
    }
    
    /**
     * Apply toolbar changes
     */
    applyToolbarChanges() {
        // Get current actions
        const currentList = document.getElementById('current-actions-list');
        const actionItems = currentList.querySelectorAll('.toolbar-customization-item');
        
        const actions = Array.from(actionItems).map(item => {
            const actionId = item.dataset.actionId;
            return this.availableActions.find(action => action.id === actionId);
        }).filter(Boolean);
        
        // Apply to toolbar
        this.applyActionsToToolbar(this.currentToolbarId, actions);
    }
    
    /**
     * Apply actions to toolbar
     * @param {string} toolbarId - Toolbar ID
     * @param {Array} actions - Actions to apply
     */
    applyActionsToToolbar(toolbarId, actions) {
        // In a real implementation, this would update the actual toolbar
        console.log(`Applying actions to toolbar ${toolbarId}:`, actions);
    }
}

// Create global toolbar customization manager
const toolbarCustomizationManager = new ToolbarCustomizationManager(toolbarManager);

// ================================
// PYTHON IMPLEMENTATION NOTES
// ================================

/*
Below are notes on how to implement these toolbar and menu features in Python/PySide6:

1. Toolbar Manager:
```python
from PySide6.QtWidgets import QToolBar, QToolButton, QAction, QButtonGroup, QWidget, QHBoxLayout
from PySide6.QtCore import Qt, QSize, Signal

class ToolbarManager(QObject):
    def __init__(self):
        super().__init__()
        self.toolbars = {}
        self.toolbar_groups = {}
        self.responsive_mode = self.detect_responsive_mode()
    
    def detect_responsive_mode(self):
        # Get screen width
        screen = QApplication.primaryScreen()
        width = screen.size().width()
        
        if width <= 600:
            return 'small'
        elif width <= 800:
            return 'medium'
        else:
            return 'large'
    
    def create_toolbar(self, toolbar_id, title, parent):
        # Create toolbar
        toolbar = QToolBar(title, parent)
        toolbar.setObjectName(toolbar_id)
        toolbar.setMovable(False)
        
        # Store toolbar
        self.toolbars[toolbar_id] = toolbar
        
        return toolbar
    
    def add_toolbar_group(self, toolbar_id, group_id, label):
        toolbar = self.toolbars.get(toolbar_id)
        if not toolbar:
            return None
        
        # Create group widget
        group = QWidget()
        group.setObjectName(group_id)
        
        # Create layout
        layout = QHBoxLayout(group)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        # Add label if provided
        if label:
            label_widget = QLabel(label)
            label_widget.setStyleSheet("font-size: 8pt; color: #666666; margin: 0 4px;")
            layout.addWidget(label_widget)
        
        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)
        
        # Add to toolbar
        toolbar.addWidget(group)
        
        # Store group
        self.toolbar_groups[group_id] = group
        
        return group
    
    def add_toolbar_button(self, group_id, button_id, text, icon, callback, options=None):
        group = self.toolbar_groups.get(group_id)
        if not group:
            return None
        
        # Create action
        action = QAction(icon, text, self)
        action.setObjectName(button_id)
        
        # Set tooltip if provided
        if options and 'tooltip' in options:
            action.setToolTip(options['tooltip'])
        
        # Set shortcut if provided
        if options and 'shortcut' in options:
            action.setShortcut(options['shortcut'])
        
        # Connect callback
        if callback:
            action.triggered.connect(callback)
        
        # Create tool button
        button = QToolButton(group)
        button.setDefaultAction(action)
        button.setObjectName(button_id)
        
        # Set button style
        button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon if text and icon else Qt.ToolButtonTextOnly)
        
        # Add to group layout
        layout = group.layout()
        layout.addWidget(button)
        
        return button
    
    def update_toolbar_layout(self):
        # Update based on responsive mode
        for toolbar_id in self.toolbars:
            self.update_toolbar(toolbar_id)
    
    def update_toolbar(self, toolbar_id):
        toolbar = self.toolbars.get(toolbar_id)
        if not toolbar:
            return
        
        # Update based on responsive mode
        if self.responsive_mode == 'small':
            self.update_toolbar_for_small_screen(toolbar)
        elif self.responsive_mode == 'medium':
            self.update_toolbar_for_medium_screen(toolbar)
        else:
            self.update_toolbar_for_large_screen(toolbar)
```

2. Menu Manager:
```python
from PySide6.QtWidgets import QMenuBar, QMenu, QAction, QWidgetAction
from PySide6.QtCore import Qt, Signal

class MenuManager(QObject):
    def __init__(self):
        super().__init__()
        self.menus = {}
        self.context_menus = {}
        self.menu_shortcuts = {}
    
    def create_menu_bar(self, menu_bar_id, parent):
        # Create menu bar
        menu_bar = QMenuBar(parent)
        menu_bar.setObjectName(menu_bar_id)
        
        # Store menu bar
        self.menus[menu_bar_id] = menu_bar
        
        return menu_bar
    
    def add_menu(self, menu_bar_id, menu_id, text):
        menu_bar = self.menus.get(menu_bar_id)
        if not menu_bar:
            return None
        
        # Create menu
        menu = QMenu(text, menu_bar)
        menu.setObjectName(menu_id)
        
        # Add to menu bar
        menu_bar.addMenu(menu)
        
        # Store menu
        self.menus[menu_id] = menu
        
        return menu
    
    def add_menu_item(self, menu_id, item_id, text, callback, options=None):
        menu = self.menus.get(menu_id)
        if not menu:
            return None
        
        # Create action
        action = QAction(text, self)
        action.setObjectName(item_id)
        
        # Set icon if provided
        if options and 'icon' in options:
            action.setIcon(options['icon'])
        
        # Set shortcut if provided
        if options and 'shortcut' in options:
            action.setShortcut(options['shortcut'])
            self.menu_shortcuts[options['shortcut']] = {
                'menu_id': menu_id,
                'item_id': item_id,
                'callback': callback
            }
        
        # Set checkable if provided
        if options and 'checkbox' in options and options['checkbox']:
            action.setCheckable(True)
            if options and 'checked' in options:
                action.setChecked(options['checked'])
        
        # Connect callback
        if callback:
            action.triggered.connect(
                lambda checked=False: callback(checked) if action.isCheckable() else callback()
            )
        
        # Add to menu
        menu.addAction(action)
        
        return action
    
    def add_menu_separator(self, menu_id):
        menu = self.menus.get(menu_id)
        if not menu:
            return None
        
        # Add separator
        menu.addSeparator()
        
        return True
    
    def create_context_menu(self, context_menu_id):
        # Create context menu
        context_menu = QMenu()
        context_menu.setObjectName(context_menu_id)
        
        # Store context menu
        self.context_menus[context_menu_id] = context_menu
        
        return context_menu
    
    def show_context_menu(self, context_menu_id, pos):
        context_menu = self.context_menus.get(context_menu_id)
        if not context_menu:
            return
        
        # Show context menu
        context_menu.exec_(pos)
```

3. Toolbar Customization:
```python
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QLabel, QPushButton

class ToolbarCustomizationDialog(QDialog):
    def __init__(self, toolbar_manager, parent=None):
        super().__init__(parent)
        self.toolbar_manager = toolbar_manager
        self.available_actions = []
        self.setup_available_actions()
        self.setup_ui()
    
    def setup_available_actions(self):
        # Define available actions
        self.available_actions = [
            {'id': 'new', 'text': 'New', 'icon': 'new.png', 'category': 'File'},
            {'id': 'open', 'text': 'Open', 'icon': 'open.png', 'category': 'File'},
            # ... more actions
        ]
    
    def setup_ui(self):
        self.setWindowTitle("Customize Toolbar")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Create content layout
        content_layout = QHBoxLayout()
        
        # Create available actions list
        available_layout = QVBoxLayout()
        available_label = QLabel("Available Actions:")
        available_layout.addWidget(available_label)
        
        self.available_list = QListWidget()
        available_layout.addWidget(self.available_list)
        
        content_layout.addLayout(available_layout)
        
        # Create button layout
        button_layout = QVBoxLayout()
        button_layout.addStretch()
        
        self.add_button = QPushButton("Add →")
        self.add_button.setEnabled(False)
        button_layout.addWidget(self.add_button)
        
        self.remove_button = QPushButton("← Remove")
        self.remove_button.setEnabled(False)
        button_layout.addWidget(self.remove_button)
        
        button_layout.addStretch()
        
        content_layout.addLayout(button_layout)
        
        # Create current actions list
        current_layout = QVBoxLayout()
        current_label = QLabel("Current Actions:")
        current_layout.addWidget(current_label)
        
        self.current_list = QListWidget()
        current_layout.addWidget(self.current_list)
        
        content_layout.addLayout(current_layout)
        
        layout.addLayout(content_layout)
        
        # Create dialog buttons
        dialog_buttons = QHBoxLayout()
        dialog_buttons.addStretch()
        
        self.reset_button = QPushButton("Reset")
        dialog_buttons.addWidget(self.reset_button)
        
        self.ok_button = QPushButton("OK")
        self.ok_button.setDefault(True)
        dialog_buttons.addWidget(self.ok_button)
        
        self.cancel_button = QPushButton("Cancel")
        dialog_buttons.addWidget(self.cancel_button)
        
        layout.addLayout(dialog_buttons)
        
        # Connect signals
        self.connect_signals()
    
    def connect_signals(self):
        self.available_list.itemSelectionChanged.connect(self.update_button_states)
        self.current_list.itemSelectionChanged.connect(self.update_button_states)
        
        self.add_button.clicked.connect(self.add_selected_action)
        self.remove_button.clicked.connect(self.remove_selected_action)
        self.reset_button.clicked.connect(self.reset_toolbar)
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
    
    def update_button_states(self):
        available_selected = len(self.available_list.selectedItems()) > 0
        current_selected = len(self.current_list.selectedItems()) > 0
        
        self.add_button.setEnabled(available_selected)
        self.remove_button.setEnabled(current_selected)
    
    def setup_for_toolbar(self, toolbar_id):
        # Store current toolbar ID
        self.current_toolbar_id = toolbar_id
        
        # Clear lists
        self.available_list.clear()
        self.current_list.clear()
        
        # Get current toolbar actions
        current_actions = self.get_current_toolbar_actions(toolbar_id)
        
        # Populate available actions list
        for action in self.available_actions:
            # Check if action is already in current actions
            if not any(a['id'] == action['id'] for a in current_actions):
                item = QListWidgetItem(action['text'])
                item.setData(Qt.UserRole, action)
                self.available_list.addItem(item)
        
        # Populate current actions list
        for action in current_actions:
            item = QListWidgetItem(action['text'])
            item.setData(Qt.UserRole, action)
            self.current_list.addItem(item)
    
    def get_current_toolbar_actions(self, toolbar_id):
        # In a real implementation, this would get the current actions from the toolbar
        # For now, return a default set
        return [
            {'id': 'new', 'text': 'New', 'icon': 'new.png'},
            {'id': 'open', 'text': 'Open', 'icon': 'open.png'},
            {'id': 'save', 'text': 'Save', 'icon': 'save.png'},
            {'id': 'undo', 'text': 'Undo', 'icon': 'undo.png'},
            {'id': 'redo', 'text': 'Redo', 'icon': 'redo.png'}
        ]
    
    def add_selected_action(self):
        # Get selected items
        selected_items = self.available_list.selectedItems()
        
        # Move items
        for item in selected_items:
            # Get action data
            action = item.data(Qt.UserRole)
            
            # Create new item
            new_item = QListWidgetItem(item.text())
            new_item.setData(Qt.UserRole, action)
            
            # Add to current list
            self.current_list.addItem(new_item)
            
            # Remove from available list
            row = self.available_list.row(item)
            self.available_list.takeItem(row)
        
        # Update button states
        self.update_button_states()
    
    def remove_selected_action(self):
        # Get selected items
        selected_items = self.current_list.selectedItems()
        
        # Move items
        for item in selected_items:
            # Get action data
            action = item.data(Qt.UserRole)
            
            # Create new item
            new_item = QListWidgetItem(item.text())
            new_item.setData(Qt.UserRole, action)
            
            # Add to available list
            self.available_list.addItem(new_item)
            
            # Remove from current list
            row = self.current_list.row(item)
            self.current_list.takeItem(row)
        
        # Update button states
        self.update_button_states()
    
    def reset_toolbar(self):
        # Clear current list
        self.current_list.clear()
        
        # Add default actions
        default_actions = [
            {'id': 'new', 'text': 'New', 'icon': 'new.png'},
            {'id': 'open', 'text': 'Open', 'icon': 'open.png'},
            {'id': 'save', 'text': 'Save', 'icon': 'save.png'},
            {'id': 'undo', 'text': 'Undo', 'icon': 'undo.png'},
            {'id': 'redo', 'text': 'Redo', 'icon': 'redo.png'}
        ]
        
        for action in default_actions:
            item = QListWidgetItem(action['text'])
            item.setData(Qt.UserRole, action)
            self.current_list.addItem(item)
    
    def get_current_actions(self):
        # Get current actions
        actions = []
        
        for i in range(self.current_list.count()):
            item = self.current_list.item(i)
            action = item.data(Qt.UserRole)
            actions.append(action)
        
        return actions
```
*/