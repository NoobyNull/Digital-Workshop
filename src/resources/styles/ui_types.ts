/**
 * UI Types and Interfaces for 3D-MM Application
 * 
 * This TypeScript file defines interfaces and types that can be used as a reference
 * for implementing type-safe UI improvements in the Python/PySide6 application.
 */

// ================================
// BASE UI TYPES
// ================================

/**
 * Base interface for all UI components
 */
interface UIComponent {
    id: string;
    visible: boolean;
    enabled: boolean;
    tooltip?: string;
    styleClass?: string[];
    accessibility?: AccessibilityOptions;
}

/**
 * Accessibility options for UI components
 */
interface AccessibilityOptions {
    accessibleName?: string;
    accessibleDescription?: string;
    accessibleRole?: AccessibleRole;
    focusable?: boolean;
    keyboardShortcut?: string;
}

/**
 * Accessible roles for screen readers
 */
enum AccessibleRole {
    PUSH_BUTTON = "push button",
    CHECK_BOX = "check box",
    RADIO_BUTTON = "radio button",
    COMBO_BOX = "combo box",
    SPIN_BOX = "spin box",
    SLIDER = "slider",
    PROGRESS_BAR = "progress bar",
    STATUS_BAR = "status bar",
    MENU_BAR = "menu bar",
    MENU = "menu",
    MENU_ITEM = "menu item",
    TAB_WIDGET = "tab widget",
    TAB_PAGE = "tab page",
    TABLE = "table",
    LIST = "list",
    TREE = "tree",
    TEXT_EDIT = "text edit",
    LABEL = "label",
    GROUP_BOX = "group box",
    DIALOG = "dialog",
    WINDOW = "window",
    DOCK_WIDGET = "dock widget",
    TOOL_BAR = "tool bar",
    SCROLL_BAR = "scroll bar"
}

// ================================
// MAIN WINDOW TYPES
// ================================

/**
 * Main window configuration
 */
interface MainWindowConfig extends UIComponent {
    title: string;
    width: number;
    height: number;
    minWidth?: number;
    minHeight?: number;
    maximized?: boolean;
    theme?: Theme;
    layout?: LayoutConfig;
    menuBar?: MenuBarConfig;
    toolBars?: ToolBarConfig[];
    statusBar?: StatusBarConfig;
    dockWidgets?: DockWidgetConfig[];
    centralWidget?: CentralWidgetConfig;
}

/**
 * Theme configuration
 */
interface Theme {
    name: string;
    mode: ThemeMode;
    colors: ThemeColors;
    fonts: ThemeFonts;
    spacing: ThemeSpacing;
    borderRadius: ThemeBorderRadius;
}

/**
 * Theme modes
 */
enum ThemeMode {
    LIGHT = "light",
    DARK = "dark",
    HIGH_CONTRAST = "highContrast",
    CUSTOM = "custom"
}

/**
 * Theme color palette
 */
interface ThemeColors {
    primary: string;
    primaryHover: string;
    primaryLight: string;
    secondary: string;
    background: string;
    surface: string;
    text: string;
    textSecondary: string;
    border: string;
    success: string;
    warning: string;
    error: string;
    info: string;
}

/**
 * Theme font configuration
 */
interface ThemeFonts {
    family: string;
    size: {
        xs: string;
        sm: string;
        md: string;
        lg: string;
        xl: string;
    };
    weight: {
        normal: string;
        bold: string;
    };
}

/**
 * Theme spacing configuration
 */
interface ThemeSpacing {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
    xxl: string;
}

/**
 * Theme border radius configuration
 */
interface ThemeBorderRadius {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    full: string;
}

// ================================
// LAYOUT TYPES
// ================================

/**
 * Layout configuration
 */
interface LayoutConfig {
    type: LayoutType;
    margins?: Margins;
    spacing?: string;
    responsive?: ResponsiveConfig;
}

/**
 * Layout types
 */
enum LayoutType {
    VERTICAL = "vertical",
    HORIZONTAL = "horizontal",
    GRID = "grid",
    FORM = "form",
    STACKED = "stacked"
}

/**
 * Margin configuration
 */
interface Margins {
    left: string;
    top: string;
    right: string;
    bottom: string;
}

/**
 * Responsive configuration
 */
interface ResponsiveConfig {
    breakpoints: BreakpointConfig[];
    rules: ResponsiveRule[];
}

/**
 * Breakpoint configuration
 */
interface BreakpointConfig {
    name: string;
    minWidth: number;
    maxWidth?: number;
}

/**
 * Responsive rule
 */
interface ResponsiveRule {
    breakpoint: string;
    properties: Record<string, string>;
}

// ================================
// MENU BAR TYPES
// ================================

/**
 * Menu bar configuration
 */
interface MenuBarConfig extends UIComponent {
    menus: MenuConfig[];
}

/**
 * Menu configuration
 */
interface MenuConfig extends UIComponent {
    title: string;
    items: MenuItemConfig[];
}

/**
 * Menu item configuration
 */
interface MenuItemConfig extends UIComponent {
    text: string;
    shortcut?: string;
    checkable?: boolean;
    checked?: boolean;
    separator?: boolean;
    submenu?: MenuConfig;
    action?: string;
}

// ================================
// TOOL BAR TYPES
// ================================

/**
 * Tool bar configuration
 */
interface ToolBarConfig extends UIComponent {
    title: string;
    area: ToolBarArea;
    movable: boolean;
    floatable: boolean;
    actions: ToolActionConfig[];
}

/**
 * Tool bar areas
 */
enum ToolBarArea {
    LEFT = "left",
    RIGHT = "right",
    TOP = "top",
    BOTTOM = "bottom"
}

/**
 * Tool action configuration
 */
interface ToolActionConfig extends UIComponent {
    text: string;
    icon?: string;
    shortcut?: string;
    checkable?: boolean;
    checked?: boolean;
    separator?: boolean;
    action: string;
    priority?: ActionPriority;
}

/**
 * Action priority
 */
enum ActionPriority {
    LOW = "low",
    NORMAL = "normal",
    HIGH = "high",
    CRITICAL = "critical"
}

// ================================
// STATUS BAR TYPES
// ================================

/**
 * Status bar configuration
 */
interface StatusBarConfig extends UIComponent {
    permanentWidgets: StatusWidgetConfig[];
    temporaryWidgets?: StatusWidgetConfig[];
}

/**
 * Status widget configuration
 */
interface StatusWidgetConfig extends UIComponent {
    type: StatusWidgetType;
    content?: string;
    progress?: ProgressConfig;
    updateInterval?: number;
}

/**
 * Status widget types
 */
enum StatusWidgetType {
    LABEL = "label",
    PROGRESS_BAR = "progressBar",
    MEMORY_USAGE = "memoryUsage",
    PERFORMANCE_INDICATOR = "performanceIndicator",
    SYSTEM_STATUS = "systemStatus"
}

/**
 * Progress configuration
 */
interface ProgressConfig {
    minimum: number;
    maximum: number;
    value: number;
    textVisible: boolean;
}

// ================================
// DOCK WIDGET TYPES
// ================================

/**
 * Dock widget configuration
 */
interface DockWidgetConfig extends UIComponent {
    title: string;
    area: DockWidgetArea;
    allowedAreas: DockWidgetArea[];
    floating: boolean;
    closable: boolean;
    movable: boolean;
    content: DockContentConfig;
}

/**
 * Dock widget areas
 */
enum DockWidgetArea {
    LEFT = "left",
    RIGHT = "right",
    TOP = "top",
    BOTTOM = "bottom",
    ALL = "all"
}

/**
 * Dock content configuration
 */
interface DockContentConfig {
    type: DockContentType;
    properties: Record<string, any>;
}

/**
 * Dock content types
 */
enum DockContentType {
    MODEL_LIBRARY = "modelLibrary",
    METADATA_EDITOR = "metadataEditor",
    PROPERTIES_PANEL = "propertiesPanel",
    SEARCH_PANEL = "searchPanel",
    CUSTOM = "custom"
}

// ================================
// CENTRAL WIDGET TYPES
// ================================

/**
 * Central widget configuration
 */
interface CentralWidgetConfig extends UIComponent {
    type: CentralWidgetType;
    properties: Record<string, any>;
}

/**
 * Central widget types
 */
enum CentralWidgetType {
    VIEWER_3D = "viewer3d",
    SPLITTER = "splitter",
    TAB_WIDGET = "tabWidget",
    WIDGET_STACK = "widgetStack"
}

// ================================
// NOTIFICATION TYPES
// ================================

/**
 * Notification configuration
 */
interface NotificationConfig {
    type: NotificationType;
    title: string;
    message: string;
    duration?: number;
    actions?: NotificationAction[];
    dismissible?: boolean;
}

/**
 * Notification types
 */
enum NotificationType {
    INFO = "info",
    SUCCESS = "success",
    WARNING = "warning",
    ERROR = "error"
}

/**
 * Notification action
 */
interface NotificationAction {
    text: string;
    action: string;
    primary?: boolean;
}

// ================================
// PERFORMANCE MONITORING TYPES
// ================================

/**
 * Performance metrics
 */
interface PerformanceMetrics {
    memoryUsage: MemoryUsage;
    cpuUsage: number;
    gpuUsage?: number;
    fps?: number;
    renderTime?: number;
    loadTime?: number;
}

/**
 * Memory usage information
 */
interface MemoryUsage {
    total: number;
    used: number;
    available: number;
    percentage: number;
}

/**
 * System status
 */
interface SystemStatus {
    overall: StatusLevel;
    memory: StatusLevel;
    cpu: StatusLevel;
    gpu?: StatusLevel;
    storage?: StatusLevel;
}

/**
 * Status levels
 */
enum StatusLevel {
    GOOD = "good",
    WARNING = "warning",
    ERROR = "error",
    UNKNOWN = "unknown"
}

// ================================
// EVENT TYPES
// ================================

/**
 * UI event types
 */
enum UIEventType {
    WINDOW_RESIZED = "windowResized",
    WINDOW_STATE_CHANGED = "windowStateChanged",
    THEME_CHANGED = "themeChanged",
    MENU_ACTION_TRIGGERED = "menuActionTriggered",
    TOOL_ACTION_TRIGGERED = "toolActionTriggered",
    DOCK_WIDGET_MOVED = "dockWidgetMoved",
    DOCK_WIDGET_CLOSED = "dockWidgetClosed",
    NOTIFICATION_SHOWN = "notificationShown",
    NOTIFICATION_DISMISSED = "notificationDismissed",
    PERFORMANCE_UPDATED = "performanceUpdated",
    MODEL_LOADED = "modelLoaded",
    MODEL_SELECTED = "modelSelected"
}

/**
 * UI event base interface
 */
interface UIEvent {
    type: UIEventType;
    timestamp: Date;
    source: string;
}

/**
 * Window resized event
 */
interface WindowResizedEvent extends UIEvent {
    type: UIEventType.WINDOW_RESIZED;
    oldSize: Size;
    newSize: Size;
}

/**
 * Window state changed event
 */
interface WindowStateChangedEvent extends UIEvent {
    type: UIEventType.WINDOW_STATE_CHANGED;
    oldState: WindowState;
    newState: WindowState;
}

/**
 * Theme changed event
 */
interface ThemeChangedEvent extends UIEvent {
    type: UIEventType.THEME_CHANGED;
    oldTheme: string;
    newTheme: string;
}

/**
 * Performance updated event
 */
interface PerformanceUpdatedEvent extends UIEvent {
    type: UIEventType.PERFORMANCE_UPDATED;
    metrics: PerformanceMetrics;
}

// ================================
// UTILITY TYPES
// ================================

/**
 * Size dimensions
 */
interface Size {
    width: number;
    height: number;
}

/**
 * Point coordinates
 */
interface Point {
    x: number;
    y: number;
}

/**
 * Rectangle
 */
interface Rectangle {
    x: number;
    y: number;
    width: number;
    height: number;
}

/**
 * Window states
 */
enum WindowState {
    NORMAL = "normal",
    MINIMIZED = "minimized",
    MAXIMIZED = "maximized",
    FULL_SCREEN = "fullScreen"
}

// ================================
// PYTHON IMPLEMENTATION NOTES
// ================================

/*
TypeScript interfaces can be translated to Python classes or dataclasses:

```python
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict, Any

class ThemeMode(Enum):
    LIGHT = "light"
    DARK = "dark"
    HIGH_CONTRAST = "highContrast"
    CUSTOM = "custom"

@dataclass
class ThemeColors:
    primary: str
    primaryHover: str
    primaryLight: str
    secondary: str
    background: str
    surface: str
    text: str
    textSecondary: str
    border: str
    success: str
    warning: str
    error: str
    info: str

@dataclass
class Theme:
    name: str
    mode: ThemeMode
    colors: ThemeColors
    # ... other properties

@dataclass
class MainWindowConfig:
    title: str
    width: int
    height: int
    minWidth: Optional[int] = None
    minHeight: Optional[int] = None
    maximized: Optional[bool] = False
    theme: Optional[Theme] = None
    # ... other properties
```

For event handling, you can use PySide6's signal and slot mechanism:

```python
from PySide6.QtCore import Signal, QObject

class UIEventManager(QObject):
    window_resized = Signal(object, object)  # old_size, new_size
    theme_changed = Signal(str, str)  # old_theme, new_theme
    performance_updated = Signal(object)  # metrics
    
    def emit_window_resized(self, old_size, new_size):
        self.window_resized.emit(old_size, new_size)
```

For responsive design, you can implement breakpoints in Python:

```python
class ResponsiveManager:
    def __init__(self, window):
        self.window = window
        self.breakpoints = [
            {"name": "small", "max_width": 600},
            {"name": "medium", "min_width": 601, "max_width": 1000},
            {"name": "large", "min_width": 1001}
        ]
    
    def get_current_breakpoint(self):
        width = self.window.width()
        for bp in self.breakpoints:
            if "min_width" in bp and width < bp["min_width"]:
                continue
            if "max_width" in bp and width > bp["max_width"]:
                continue
            return bp["name"]
        return "large"
    
    def apply_responsive_rules(self):
        breakpoint = self.get_current_breakpoint()
        # Apply rules based on breakpoint
        if breakpoint == "small":
            self.window.model_library_dock.setMinimumWidth(150)
        elif breakpoint == "medium":
            self.window.model_library_dock.setMinimumWidth(200)
        else:  # large
            self.window.model_library_dock.setMinimumWidth(250)
```
*/