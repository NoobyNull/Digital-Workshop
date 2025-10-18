"""
CSS template for preview window.

Contains comprehensive stylesheet for previewing all widget types.
"""

CSS_PREVIEW_TEMPLATE = """
/* Base window */
QMainWindow {{
    background-color: {{window_bg}};
    color: {{text}};
}}

/* Menubar */
QMenuBar {{
    background-color: {{menubar_bg}};
    color: {{menubar_text}};
    border-bottom: 1px solid {{menubar_border}};
}}
QMenuBar::item {{
    background: transparent;
    padding: 4px 8px;
}}
QMenuBar::item:selected {{
    background: {{menubar_item_hover_bg}};
    color: {{menubar_item_hover_text}};
}}
QMenuBar::item:pressed {{
    background: {{menubar_item_pressed_bg}};
}}

/* Toolbar */
QToolBar {{
    background-color: {{toolbar_bg}};
    border-bottom: 1px solid {{toolbar_border}};
}}
QToolButton {{
    background: {{toolbutton_bg}};
    border: 1px solid {{toolbutton_border}};
    padding: 4px 8px;
}}
QToolButton:hover {{
    background: {{toolbutton_hover_bg}};
    border: 1px solid {{toolbutton_hover_border}};
}}
QToolButton:checked {{
    background: {{toolbutton_checked_bg}};
    color: {{toolbutton_checked_text}};
    border: 1px solid {{toolbutton_checked_border}};
}}

/* Status bar */
QStatusBar {{
    background-color: {{statusbar_bg}};
    color: {{statusbar_text}};
    border-top: 1px solid {{statusbar_border}};
}}

/* Dock */
QDockWidget {{
    background-color: {{dock_bg}};
    color: {{dock_text}};
    border: 1px solid {{dock_border}};
}}
QDockWidget::title {{
    background-color: {{dock_title_bg}};
    border-bottom: 1px solid {{dock_title_border}};
    padding: 4px 6px;
}}

/* Buttons */
QPushButton {{
    background-color: {{button_bg}};
    color: {{button_text}};
    border: 1px solid {{button_border}};
    padding: 6px 12px;
    border-radius: 2px;
}}
QPushButton:hover {{
    background-color: {{button_hover_bg}};
    border: 1px solid {{button_hover_border}};
}}
QPushButton:pressed {{
    background-color: {{button_pressed_bg}};
}}
QPushButton:checked {{
    background-color: {{button_checked_bg}};
    color: {{button_checked_text}};
    border: 1px solid {{button_checked_border}};
}}
QPushButton:default {{
    border: 1px solid {{button_default_border}};
    background-color: {{button_default_bg}};
    color: {{button_default_text}};
    font-weight: bold;
}}
QPushButton:disabled {{
    background-color: {{button_disabled_bg}};
    color: {{button_disabled_text}};
    border: 1px solid {{button_disabled_border}};
}}

/* Inputs */
QLineEdit, QTextEdit, QComboBox, QSpinBox {{
    border: 1px solid {{input_border}};
    border-radius: 2px;
    padding: 6px;
    background-color: {{input_bg}};
    color: {{input_text}};
    selection-background-color: {{selection_bg}};
    selection-color: {{selection_text}};
}}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {{
    border: 2px solid {{input_focus_border}};
}}
QLineEdit:disabled, QTextEdit:disabled, QComboBox:disabled, QSpinBox:disabled {{
    background-color: {{input_disabled_bg}};
    color: {{input_disabled_text}};
}}

/* Progress bar */
QProgressBar {{
    border: 1px solid {{progress_border}};
    border-radius: 2px;
    text-align: center;
    background-color: {{progress_bg}};
    color: {{progress_text}};
}}
QProgressBar::chunk {{
    background-color: {{progress_chunk}};
}}

/* Tabs */
QTabWidget::pane {{
    border: 1px solid {{tab_pane_border}};
    background-color: {{tab_pane_bg}};
}}
QTabBar::tab {{
    background: {{tab_bg}};
    padding: 6px 10px;
    margin-right: 2px;
    border: 1px solid {{tab_border}};
    border-bottom: none;
    color: {{tab_text}};
}}
QTabBar::tab:selected {{
    background: {{tab_selected_bg}};
    border-bottom: 2px solid {{tab_selected_border}};
}}
QTabBar::tab:hover {{
    background: {{tab_hover_bg}};
}}

/* Tables & Lists */
QTableWidget {{
    background-color: {{table_bg}};
    color: {{table_text}};
    gridline-color: {{table_gridline}};
    border: 1px solid {{table_border}};
}}
QHeaderView::section {{
    background-color: {{header_bg}};
    color: {{header_text}};
    border: 1px solid {{header_border}};
}}
QListWidget {{
    background-color: {{table_bg}};
    color: {{table_text}};
    border: 1px solid {{table_border}};
    selection-background-color: {{selection_bg}};
    selection-color: {{selection_text}};
}}

/* GroupBox */
QGroupBox {{
    font-weight: bold;
    border: 2px solid {{groupbox_border}};
    border-radius: 4px;
    margin-top: 1ex;
    padding-top: 8px;
    background-color: {{groupbox_bg}};
    color: {{groupbox_text}};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px 0 4px;
    color: {{groupbox_title_text}};
}}

/* Checkboxes and radios (basic) */
QCheckBox, QRadioButton {{
    color: {{text}};
}}

/* Slider */
QSlider::groove:horizontal {{
    height: 6px;
    background: {{slider_groove_bg}};
    border: 1px solid {{slider_groove_border}};
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    width: 12px;
    background: {{slider_handle}};
    border: 1px solid {{slider_handle_border}};
    margin: -5px 0;
    border-radius: 6px;
}}

/* Spinbox */
QSpinBox {{
    background: {{spinbox_bg}};
    color: {{spinbox_text}};
    border: 1px solid {{spinbox_border}};
}}
QSpinBox:focus {{
    border: 2px solid {{spinbox_focus_border}};
}}

/* Status indicators (by objectName) */
QLabel#status-good {{
    background-color: {{status_good_bg}};
    color: {{status_good_text}};
    border: 1px solid {{status_good_border}};
    padding: 4px 8px;
    border-radius: 2px;
}}
QLabel#status-warning {{
    background-color: {{status_warning_bg}};
    color: {{status_warning_text}};
    border: 1px solid {{status_warning_border}};
    padding: 4px 8px;
    border-radius: 2px;
}}
QLabel#status-error {{
    background-color: {{status_error_bg}};
    color: {{status_error_text}};
    border: 1px solid {{status_error_border}};
    padding: 4px 8px;
    border-radius: 2px;
}}

/* Generic labels */
QLabel {{
    color: {{label_text}};
}}
"""

