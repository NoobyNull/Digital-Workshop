"""
PreviewWindow - Live preview of theme with real Qt widgets.

Shows a mini QMainWindow with various widgets to preview the current theme.
"""

from typing import Optional

from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox, QSpinBox, QSlider,
    QProgressBar, QTabWidget, QTableWidget, QTableWidgetItem, QCheckBox, QRadioButton,
    QGroupBox, QDockWidget, QListWidget, QListWidgetItem, QToolBar, QStatusBar
)

from src.gui.theme import ThemeManager, SPACING_12
from .preview_css_template import CSS_PREVIEW_TEMPLATE


class PreviewWindow(QMainWindow):
    """
    Mini QMainWindow with real widgets. Styles are applied via ThemeManager CSS processing.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Preview")
        self.resize(700, 520)

        # Menubar
        bar = self.menuBar()
        menu_file = bar.addMenu("File")
        menu_file.addAction("New")
        menu_file.addAction("Open")
        menu_file.addSeparator()
        menu_file.addAction("Exit")

        menu_edit = bar.addMenu("Edit")
        menu_edit.addAction("Copy")
        menu_edit.addAction("Paste")

        menu_view = bar.addMenu("View")
        menu_view.addAction("Reset Layout")

        # Toolbar
        tb = QToolBar("Main Toolbar")
        tb.setIconSize(QSize(16, 16))
        self.addToolBar(tb)
        tb.addAction("New")
        tb.addAction("Open")
        tb.addAction("Save")

        # Status bar
        sb = QStatusBar()
        self.setStatusBar(sb)
        sb.showMessage("Ready", 2000)

        # Dock
        dock = QDockWidget("Sample Dock", self)
        dock_list = QListWidget()
        for i in range(5):
            dock_list.addItem(QListWidgetItem(f"Item {i+1}"))
        dock.setWidget(dock_list)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        cv = QVBoxLayout(central)
        cv.setContentsMargins(SPACING_12, SPACING_12, SPACING_12, SPACING_12)
        cv.setSpacing(SPACING_12)

        # Button row
        row_btns = QHBoxLayout()
        btn_normal = QPushButton("Normal")
        btn_hover_hint = QLabel("(Hover states preview on mouseover)")
        btn_pressed_hint = QLabel("(Press to see pressed state)")
        btn_checked = QPushButton("Checked")
        btn_checked.setCheckable(True)
        btn_checked.setChecked(True)
        btn_disabled = QPushButton("Disabled")
        btn_disabled.setEnabled(False)
        btn_default = QPushButton("Default")
        btn_default.setDefault(True)

        row_btns.addWidget(btn_normal)
        row_btns.addWidget(btn_checked)
        row_btns.addWidget(btn_disabled)
        row_btns.addWidget(btn_default)
        row_btns.addStretch(1)
        cv.addLayout(row_btns)
        cv.addWidget(btn_hover_hint)
        cv.addWidget(btn_pressed_hint)

        # Inputs
        row_inputs = QHBoxLayout()
        le = QLineEdit()
        le.setPlaceholderText("QLineEdit")
        te = QTextEdit()
        te.setPlainText("QTextEdit\nmultiline")
        cb = QComboBox()
        cb.addItems(["Option A", "Option B", "Option C"])
        sp = QSpinBox()
        sp.setRange(0, 100)
        sp.setValue(42)
        sl = QSlider(Qt.Horizontal)
        sl.setRange(0, 100)
        sl.setValue(50)
        row_inputs.addWidget(le, 1)
        row_inputs.addWidget(te, 1)
        row_inputs.addWidget(cb, 0)
        row_inputs.addWidget(sp, 0)
        row_inputs.addWidget(sl, 1)
        cv.addLayout(row_inputs)

        # Progress
        pb = QProgressBar()
        pb.setValue(45)
        cv.addWidget(pb)

        # Tabs with table and list
        tabs = QTabWidget()
        tab1 = QWidget()
        tab1v = QVBoxLayout(tab1)
        table = QTableWidget(3, 3)
        table.setHorizontalHeaderLabels(["A", "B", "C"])
        for r in range(3):
            for c in range(3):
                table.setItem(r, c, QTableWidgetItem(f"{r},{c}"))
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setVisible(False)
        tab1v.addWidget(table)

        tab2 = QWidget()
        tab2v = QVBoxLayout(tab2)
        l = QListWidget()
        l.addItems([f"List {i+1}" for i in range(8)])
        tab2v.addWidget(l)

        tabs.addTab(tab1, "Table")
        tabs.addTab(tab2, "List")
        cv.addWidget(tabs)

        # Group box with checks/radios
        grp = QGroupBox("Group && State Indicators")
        gb_v = QVBoxLayout(grp)
        cb1 = QCheckBox("Enable feature")
        cb2 = QCheckBox("Disabled option")
        cb2.setEnabled(False)
        rb1 = QRadioButton("Choice A")
        rb2 = QRadioButton("Choice B")
        rb1.setChecked(True)
        gb_v.addWidget(cb1)
        gb_v.addWidget(cb2)
        gb_v.addWidget(rb1)
        gb_v.addWidget(rb2)
        cv.addWidget(grp)

        # Status indicators
        status_row = QHBoxLayout()
        lbl_ok = QLabel("Success")
        lbl_ok.setObjectName("status-good")
        lbl_warn = QLabel("Warning")
        lbl_warn.setObjectName("status-warning")
        lbl_err = QLabel("Error")
        lbl_err.setObjectName("status-error")
        status_row.addWidget(lbl_ok)
        status_row.addWidget(lbl_warn)
        status_row.addWidget(lbl_err)
        status_row.addStretch(1)
        cv.addLayout(status_row)

        # Register and apply preview stylesheet
        tm = ThemeManager.instance()
        tm.register_widget(self, css_text=CSS_PREVIEW_TEMPLATE)
        tm.apply_stylesheet(self)

