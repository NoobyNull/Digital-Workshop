from pathlib import Path

path = Path("src/gui/CLO/cut_list_optimizer_widget.py")
text = path.read_text()
old = """
# Add + button (column 6)
        add_btn = QPushButton("+")
        add_btn.setMaximumWidth(30)

        def add_piece_wrapper(_=None, current_row=row) -> None:
            self.add_piece_from_table(current_row)

        add_btn.clicked.connect(add_piece_wrapper)
        add_container = QWidget()
        add_layout = QHBoxLayout(add_container)
        add_layout.setContentsMargins(0, 0, 0, 0)
        add_layout.addStretch()
        add_layout.addWidget(add_btn)
        add_layout.addStretch()
        self.ui_refs["pieces_table"].setCellWidget(row, 6, add_container)
"""
new = """
# Add + button (column 8)
        add_btn = QPushButton("+")
        add_btn.setMaximumWidth(30)

        def add_piece_wrapper(_=None, current_row=row) -> None:
            self.add_piece_from_table(current_row)

        add_btn.clicked.connect(add_piece_wrapper)
        add_container = QWidget()
        add_layout = QHBoxLayout(add_container)
        add_layout.setContentsMargins(0, 0, 0, 0)
        add_layout.addStretch()
        add_layout.addWidget(add_btn)
        add_layout.addStretch()
        self.ui_refs["pieces_table"].setCellWidget(row, 8, add_container)
"""
if old not in text:
    raise SystemExit("old add button block not found")
text = text.replace(old, new, 1)
path.write_text(text)
